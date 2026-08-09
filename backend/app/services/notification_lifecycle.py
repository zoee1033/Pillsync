import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.notification import Notification
from app.models.history import History
from app.models.enums import HistoryStatus
from app.models.reminder import Reminder
from app.models.medicine import Medicine
from app.services.history_service import is_duplicate_history

logger = logging.getLogger("NOTIFICATION_LIFECYCLE")


class NotificationState(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


def log_lifecycle_event(stage: str, message: str, meta: Optional[Dict[str, Any]] = None):
    """Formats structured lifecycle logging with timestamp."""
    from app.config import settings
    if settings.ENABLE_VERBOSE_NOTIFICATION_LOGS:
        now_iso = datetime.utcnow().isoformat()
        meta_str = f" | {meta}" if meta else ""
        logger.debug(f"[{stage}] [{now_iso}] {message}{meta_str}")


def transition_notification_state(
    db: Session,
    notification_id: int,
    new_state: NotificationState,
    reason: str = ""
) -> Optional[Notification]:
    """
    Centralized state transition manager for Notifications.
    Transitions through PENDING -> PROCESSING -> SENT -> DELIVERED -> READ / FAILED.
    """
    try:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            log_lifecycle_event("NotificationLifecycle", f"Notification #{notification_id} not found for state transition.")
            return None

        old_sent_status = notif.is_sent
        old_read_status = notif.is_read

        if new_state == NotificationState.SENT:
            notif.is_sent = True
            notif.sent_at = datetime.utcnow()
        elif new_state == NotificationState.DELIVERED:
            notif.is_sent = True
            if not notif.sent_at:
                notif.sent_at = datetime.utcnow()
        elif new_state == NotificationState.READ:
            notif.is_read = True
        elif new_state == NotificationState.FAILED:
            # Keep record for audit
            pass

        db.commit()
        db.refresh(notif)

        log_lifecycle_event(
            "NotificationLifecycle",
            f"Notification #{notification_id} state transition: {new_state.value} ({reason})",
            {"notification_id": notification_id, "is_sent": notif.is_sent, "is_read": notif.is_read}
        )

        # Broadcast via WebSocket if real-time manager is available
        try:
            from app.services.websocket_manager import broadcast_notification_event
            broadcast_notification_event(
                user_id=notif.user_id,
                event_type="NOTIFICATION_STATE_CHANGED",
                payload={
                    "notification_id": notif.id,
                    "state": new_state.value,
                    "is_read": notif.is_read,
                    "is_sent": notif.is_sent,
                    "reminder_id": notif.reminder_id
                }
            )
        except Exception as ws_err:
            pass

        return notif

    except SQLAlchemyError as err:
        db.rollback()
        log_lifecycle_event("NotificationLifecycle", f"Database error during state transition for #{notification_id}: {err}")
        return None


def create_atomic_reminder_notification(
    db: Session,
    reminder: Reminder,
    user_id: int,
    medicine_id: int,
    medicine_name: str,
    treatment_id: int,
    now: datetime
) -> Tuple[Notification, Optional[History]]:
    """
    Executes atomic database transaction creating Notification + History records
    and updating Reminder timestamps within a SINGLE commit.
    """
    log_lifecycle_event("Reminder", f"Reminder #{reminder.id} triggered for medicine '{medicine_name}'")

    # 1. Create Notification record (Initial State: PENDING -> SENT)
    title = "💊 Pill Reminder"
    msg = f"It's time to take {medicine_name}"

    # Check duplicate notification for same reminder in last 60s
    existing_dup = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.reminder_id == reminder.id,
            Notification.created_at >= datetime.combine(now.date(), datetime.min.time())
        )
        .order_by(Notification.created_at.desc())
        .first()
    )

    if existing_dup and existing_dup.created_at:
        dup_created = existing_dup.created_at
        if dup_created.tzinfo is None and now.tzinfo is not None:
            dup_created = dup_created.replace(tzinfo=now.tzinfo)
        delta_sec = (now - dup_created).total_seconds()
        if delta_sec < 45:
            log_lifecycle_event("NotificationLifecycle", f"Duplicate notification prevented for Reminder #{reminder.id} (last sent {delta_sec:.1f}s ago).")
            return existing_dup, None

    notification = Notification(
        user_id=user_id,
        reminder_id=reminder.id,
        title=title,
        message=msg,
        notification_type="Reminder",
        is_sent=True,
        is_read=False,
        sent_at=now
    )
    db.add(notification)
    db.flush()  # Populates notification.id

    log_lifecycle_event("Notification", f"Created notification #{notification.id} for user #{user_id}")

    # 2. Create History entry if not duplicate
    history_entry = None
    if not is_duplicate_history(db, user_id, treatment_id, HistoryStatus.REMINDER_TRIGGERED.value, medicine_id):
        history_entry = History(
            user_id=user_id,
            treatment_id=treatment_id,
            medicine_id=medicine_id,
            reminder_id=reminder.id,
            scheduled_time=now,
            action_time=now,
            status=HistoryStatus.REMINDER_TRIGGERED.value,
            notes=f"Reminder triggered for '{medicine_name}'."
        )
        db.add(history_entry)

    log_lifecycle_event("NotificationLifecycle", f"Atomic commit prepared for Notification #{notification.id} & History record")

    return notification, history_entry
