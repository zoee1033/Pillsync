import atexit
import concurrent.futures
from datetime import datetime
from types import SimpleNamespace

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


def _async_send_push_worker(user_id: int, reminder_id: int, medicine_id: int, notification_id: int, medicine_name: str):
    """
    Background worker executing FCM push notifications asynchronously.
    Runs in an isolated database session so network latency never blocks the main scheduler thread.
    """
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
            print(f"[TRACE {datetime.utcnow().isoformat()}] [ASYNC_WORKER] No active device tokens for user {user_id}", flush=True)
            return

        for device in active_tokens:
            masked_tok = f"{device.fcm_token[:6]}...{device.fcm_token[-6:]}" if len(device.fcm_token) > 12 else "***"
            print(f"[TRACE {datetime.utcnow().isoformat()}] [ASYNC_WORKER] Attempting FCM push for user {user_id} using token ID {device.id} ({masked_tok})...", flush=True)

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
                    },
                )

                mark_as_sent(notification_id, db)
                print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 3: FIREBASE_SEND_SUCCESS] FCM Message ID: {response}, Notification ID: {notification_id}, Token ID: {device.id}", flush=True)
                break

            except messaging.UnregisteredError as e:
                device.is_active = False
                try:
                    db.commit()
                except SQLAlchemyError as commit_err:
                    db.rollback()
                    print(f"[DISPATCH_ERROR] Failed to deactivate token ID {device.id}: {commit_err}", flush=True)

                print(
                    f"[DISPATCH_LOG] reminder_id={reminder_id} notification_id={notification_id} token_id={device.id} "
                    f"token_status=DEACTIVATED exception_type=UnregisteredError retryable=False detail=\"{e}\"",
                    flush=True
                )
                print(f"[TRACE {datetime.utcnow().isoformat()}] Token ID {device.id} permanently invalidated (UnregisteredError). Moving to next token...", flush=True)

            except (firebase_exceptions.FirebaseError, Exception) as e:
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
                    except SQLAlchemyError as commit_err:
                        db.rollback()
                        print(f"[DISPATCH_ERROR] Failed to deactivate token ID {device.id}: {commit_err}", flush=True)

                    print(
                        f"[DISPATCH_LOG] reminder_id={reminder_id} notification_id={notification_id} token_id={device.id} "
                        f"token_status=DEACTIVATED exception_type={type(e).__name__} retryable=False detail=\"{e}\"",
                        flush=True
                    )
                else:
                    print(
                        f"[DISPATCH_LOG] reminder_id={reminder_id} notification_id={notification_id} token_id={device.id} "
                        f"token_status=ACTIVE exception_type={type(e).__name__} retryable=True detail=\"{e}\"",
                        flush=True
                    )
                    print(f"[TRACE {datetime.utcnow().isoformat()}] Transient Firebase error for token ID {device.id}: {e}", flush=True)
    finally:
        db.close()


def submit_async_fcm_dispatch(user_id: int, reminder_id: int, medicine_id: int, notification_id: int, medicine_name: str):
    """Submits FCM push notification delivery to background thread pool executor."""
    _fcm_executor.submit(
        _async_send_push_worker,
        user_id=user_id,
        reminder_id=reminder_id,
        medicine_id=medicine_id,
        notification_id=notification_id,
        medicine_name=medicine_name
    )
    print(f"[TRACE {datetime.utcnow().isoformat()}] [ASYNC_DISPATCH_SUBMITTED] FCM push submitted to background thread pool for Notification ID: {notification_id}", flush=True)


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