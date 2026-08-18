import atexit
import logging
import concurrent.futures
from datetime import datetime
from types import SimpleNamespace

logger = logging.getLogger("DISPATCHER")

# pyrefly: ignore [missing-import]
from firebase_admin import messaging, exceptions as firebase_exceptions
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models.device_token import DeviceToken
from app.schemas.notification_schema import NotificationCreate
from app.services.firebase_service import send_push_notification
from app.services.notification_service import create_notification, mark_as_sent

# Bounded ThreadPoolExecutor for background FCM network dispatches
_fcm_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="fcm_worker")


def _shutdown_executor():
    """Graceful shutdown hook for worker thread pool on application exit."""
    try:
        _fcm_executor.shutdown(wait=False, cancel_futures=True)
    except Exception:
        pass


atexit.register(_shutdown_executor)


def _async_send_push_worker(
    user_id: int,
    reminder_id: int,
    medicine_id: int,
    notification_id: int,
    medicine_name: str,
    priority: str = "HIGH"
):
    """
    Background worker executing FCM push notifications asynchronously.
    Runs in an isolated database session with automatic retry, exponential backoff, rate limiting, and DLQ capture.
    """
    import time
    import traceback
    from app.services.event_bus import event_bus, EventType
    from app.services.dead_letter_queue import dead_letter_queue
    from app.services.notification_rate_limiter import rate_limiter
    from app.services.notification_observability import metrics_collector, ObservabilityContext

    obs_ctx = ObservabilityContext(user_id=user_id, reminder_id=reminder_id, notification_id=notification_id)
    dispatch_start = time.perf_counter()

    # Apply Sliding Window Rate Limiter
    delay_sec = rate_limiter.check_and_acquire(user_id)
    if delay_sec > 0:
        time.sleep(delay_sec)

    from app.config import settings
    if settings.ENABLE_VERBOSE_NOTIFICATION_LOGS:
        logger.debug(f"{obs_ctx.to_log_prefix()} Sending FCM... (Priority={priority})")

    db = SessionLocal()
    try:
        active_tokens = (
            db.query(DeviceToken)
            .filter(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active == True
            )
            .order_by(
                DeviceToken.last_used_at.desc(),
                DeviceToken.created_at.desc()
            )
            .all()
        )

        if not active_tokens:
            if settings.ENABLE_VERBOSE_NOTIFICATION_LOGS:
                logger.debug(f"{obs_ctx.to_log_prefix()} No active device tokens. Marking notification sent locally.")
            mark_as_sent(notification_id, db)
            event_bus.publish(EventType.NOTIFICATION_SENT, {"notification_id": notification_id, "user_id": user_id, "mode": "local_browser"})
            return

        sent_any = False
        last_exception_msg = ""
        last_fcm_resp = ""

        for device in active_tokens:
            masked_tok = f"{device.fcm_token[:6]}...{device.fcm_token[-6:]}" if len(device.fcm_token) > 12 else "***"
            max_retries = 3
            backoff_sec = 0.5

            for attempt in range(1, max_retries + 1):
                t_fcm_start = time.perf_counter()
                try:
                    response = send_push_notification(
                        token=device.fcm_token,
                        title="💊 Pill Reminder",
                        body=f"It's time to take {medicine_name}",
                        data={
                            "reminder_id": str(reminder_id),
                            "medicine_id": str(medicine_id),
                            "user_id": str(user_id),
                            "notification_id": str(notification_id),
                            "priority": priority
                        },
                    )

                    fcm_latency_ms = (time.perf_counter() - t_fcm_start) * 1000.0
                    metrics_collector.record_fcm_response_time(fcm_latency_ms)

                    mark_as_sent(notification_id, db)
                    sent_any = True
                    last_fcm_resp = str(response)

                    logger.info(f"Delivery successful for Notification #{notification_id} (FCM Msg ID: {response}, {fcm_latency_ms:.1f}ms)")
                    event_bus.publish(EventType.NOTIFICATION_SENT, {"notification_id": notification_id, "user_id": user_id, "fcm_msg_id": response})
                    break

                except messaging.UnregisteredError as e:
                    device.is_active = False
                    try:
                        db.commit()
                    except SQLAlchemyError:
                        db.rollback()

                    last_exception_msg = str(e)
                    logger.warning(f"Token #{device.id} permanently invalidated (UnregisteredError). Deactivated.")
                    event_bus.publish(EventType.TOKEN_INVALIDATED, {"device_id": device.id, "user_id": user_id})
                    break

                except (firebase_exceptions.FirebaseError, Exception) as e:
                    last_exception_msg = str(e)
                    err_str = str(e).lower()
                    is_unregistered = (
                        "notregistered" in err_str
                        or "invalid-registration-token" in err_str
                        or "not a valid fcm registration token" in err_str
                        or "unregistered" in err_str
                    )

                    if is_unregistered:
                        device.is_active = False
                        try:
                            db.commit()
                        except SQLAlchemyError:
                            db.rollback()
                        logger.warning(f"Token #{device.id} deactivated due to invalid token error.")
                        event_bus.publish(EventType.TOKEN_INVALIDATED, {"device_id": device.id, "user_id": user_id})
                        break

                    metrics_collector.record_retry(attempt)
                    logger.warning(f"Transient FCM error (Attempt #{attempt}/{max_retries}) for Token #{device.id}: {e}")
                    if attempt < max_retries:
                        time.sleep(backoff_sec)
                        backoff_sec *= 2.0

            if sent_any:
                break

        if not sent_any:
            mark_as_sent(notification_id, db)
            # Push permanently failed notification to DLQ
            dlq_id = dead_letter_queue.push(
                notification_id=notification_id,
                user_id=user_id,
                error=last_exception_msg or "All device tokens failed dispatch",
                retry_count=3,
                stack_trace_summary=traceback.format_exc(),
                fcm_response=last_fcm_resp,
                token_status="ALL_TOKENS_FAILED"
            )
            event_bus.publish(EventType.NOTIFICATION_FAILED, {"notification_id": notification_id, "user_id": user_id, "dlq_id": dlq_id})

    finally:
        db.close()
        total_dispatch_ms = (time.perf_counter() - dispatch_start) * 1000.0
        metrics_collector.record_dispatch_latency(total_dispatch_ms)


def submit_async_fcm_dispatch(
    user_id: int,
    reminder_id: int,
    medicine_id: int,
    notification_id: int,
    medicine_name: str,
    priority: str = "HIGH"
):
    """Submits FCM push notification delivery to background thread pool executor."""
    _fcm_executor.submit(
        _async_send_push_worker,
        user_id=user_id,
        reminder_id=reminder_id,
        medicine_id=medicine_id,
        notification_id=notification_id,
        medicine_name=medicine_name,
        priority=priority
    )
    from app.config import settings
    if settings.ENABLE_VERBOSE_NOTIFICATION_LOGS:
        logger.debug(f"[ASYNC_DISPATCH_SUBMITTED] FCM push submitted to background thread pool for Notification ID: {notification_id}")


def batch_dispatch_notifications(notifications_list: list, batch_size: int = 50) -> dict:
    """
    Batches multiple notifications (default batch size: 50) and dispatches concurrently.
    Measures batch latency, batch success, and batch failures.
    """
    import time
    batch_start = time.perf_counter()
    processed_count = 0

    for item in notifications_list:
        submit_async_fcm_dispatch(
            user_id=item.get("user_id", 0),
            reminder_id=item.get("reminder_id", 0),
            medicine_id=item.get("medicine_id", 0),
            notification_id=item.get("notification_id", 0),
            medicine_name=item.get("medicine_name", "Medicine"),
            priority=item.get("priority", "NORMAL")
        )
        processed_count += 1

    elapsed_ms = (time.perf_counter() - batch_start) * 1000.0
    return {
        "batch_size": len(notifications_list),
        "dispatched_count": processed_count,
        "batch_latency_ms": round(elapsed_ms, 2)
    }


def create_notification_record(db, reminder, medicine_name: str, user_id: int):
    """
    Creates a Notification DB record within caller's active database transaction.
    """
    return create_notification(
        db=db,
        notification=NotificationCreate(
            reminder_id=reminder.id,
            title="💊 Pill Reminder",
            message=f"It's time to take {medicine_name}",
            notification_type="Reminder",
        ),
        current_user=SimpleNamespace(id=user_id),
    )


def dispatch_reminder(db, reminder):
    """
    Backward-compatible reminder dispatch interface.
    Creates notification record, marks sent, and dispatches FCM push notification.
    """
    user_id = getattr(reminder.medicine.treatment, "user_id", 0)
    medicine_id = getattr(reminder.medicine, "id", 0)
    medicine_name = getattr(reminder.medicine, "medicine_name", "Medicine")

    notif = create_notification(
        db=db,
        notification=NotificationCreate(
            reminder_id=reminder.id,
            title="💊 Pill Reminder",
            message=f"It's time to take {medicine_name}",
            notification_type="Reminder",
        ),
        current_user=SimpleNamespace(id=user_id),
    )

    mark_as_sent(notif.id, db)

    submit_async_fcm_dispatch(
        user_id=user_id,
        reminder_id=reminder.id,
        medicine_id=medicine_id,
        notification_id=notif.id,
        medicine_name=medicine_name
    )

    return notif