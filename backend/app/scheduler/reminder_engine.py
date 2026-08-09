import logging
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.reminder import Reminder
from app.models.medicine import Medicine
from app.models.treatment import Treatment
from app.scheduler.dispatcher import submit_async_fcm_dispatch
from app.services.reminder_service import calculate_next_trigger
from app.services.notification_lifecycle import (
    create_atomic_reminder_notification,
    log_lifecycle_event
)
from app.services.websocket_manager import broadcast_notification_event

logger = logging.getLogger("REMINDER_ENGINE")


def process_due_reminders(db):
    """
    Find reminders that are due based on next_trigger_at.
    Executes atomic database updates (last_triggered_at, next_trigger_at, Notification, History)
    in a SINGLE db.commit() transaction per reminder, then offloads FCM push network delivery
    asynchronously to background workers.
    """
    now = datetime.now().astimezone()

    # Eagerly load Medicine and Treatment relationships in a SINGLE SQL query to eliminate N+1 latency
    reminders = (
        db.query(Reminder)
        .options(
            joinedload(Reminder.medicine).joinedload(Medicine.treatment)
        )
        .filter(
            Reminder.notification_enabled == True,
            Reminder.status == "Active",
            or_(
                Reminder.next_trigger_at <= now,
                and_(
                    Reminder.next_trigger_at.is_(None),
                    Reminder.reminder_time <= now.time()
                )
            )
        )
        .all()
    )

    due_reminders = []
    for r in reminders:
        if r.last_triggered_at:
            last_trig = r.last_triggered_at
            if last_trig.tzinfo is None:
                last_trig = last_trig.replace(tzinfo=now.tzinfo)
            delta = (now - last_trig).total_seconds()
            if delta < 60:
                continue
        due_reminders.append(r)

    if due_reminders:
        log_lifecycle_event("Scheduler", f"Found {len(due_reminders)} due reminder(s) to process.")

    for reminder in due_reminders:
        try:
            medicine_id = getattr(reminder, "medicine_id", reminder.medicine.id)
            user_id = reminder.medicine.treatment.user_id
            treatment_id = reminder.medicine.treatment_id
            medicine_name = reminder.medicine.medicine_name

            # Check Idempotency Engine for duplicate prevention
            from app.services.notification_idempotency import idempotency_engine
            if idempotency_engine.is_duplicate(user_id, reminder.id, now):
                continue

            idempotency_engine.mark_processed(user_id, reminder.id, now)

            # 1. Update reminder timestamps
            reminder.last_triggered_at = now
            reminder.next_trigger_at = calculate_next_trigger(
                reminder.reminder_time,
                reminder.repeat_type,
                base_datetime=now
            )

            # 2. Create Notification + History record atomically via NotificationLifecycle
            notification, history_entry = create_atomic_reminder_notification(
                db=db,
                reminder=reminder,
                user_id=user_id,
                medicine_id=medicine_id,
                medicine_name=medicine_name,
                treatment_id=treatment_id,
                now=now
            )

            # 3. SINGLE ATOMIC COMMIT FOR ALL REMINDER DATABASE UPDATES!
            db.commit()
            db.refresh(reminder)
            db.refresh(notification)

            log_lifecycle_event("NotificationLifecycle", f"Atomic commit success for Reminder #{reminder.id}. Next trigger at {reminder.next_trigger_at}")

            # 4. Broadcast real-time event to open browser tabs instantly
            try:
                broadcast_notification_event(
                    user_id=user_id,
                    event_type="REMINDER_TRIGGERED",
                    payload={
                        "notification_id": notification.id,
                        "reminder_id": reminder.id,
                        "medicine_id": medicine_id,
                        "medicine_name": medicine_name,
                        "title": notification.title,
                        "message": notification.message,
                        "created_at": notification.created_at.isoformat() if notification.created_at else now.isoformat()
                    }
                )
            except Exception as ws_err:
                pass

            # 5. Offload FCM push delivery to background thread pool AFTER successful commit
            submit_async_fcm_dispatch(
                user_id=user_id,
                reminder_id=reminder.id,
                medicine_id=medicine_id,
                notification_id=notification.id,
                medicine_name=medicine_name
            )

        except SQLAlchemyError as db_err:
            db.rollback()
            log_lifecycle_event("Reminder", f"Database error processing Reminder #{reminder.id}: {db_err}")
        except Exception as e:
            db.rollback()
            log_lifecycle_event("Reminder", f"Unexpected error processing Reminder #{reminder.id}: {e}")