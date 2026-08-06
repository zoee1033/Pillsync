from datetime import datetime
from types import SimpleNamespace

# pyrefly: ignore [missing-import]
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.reminder import Reminder
from app.models.history import History
from app.models.enums import HistoryStatus
from app.models.medicine import Medicine
from app.models.treatment import Treatment
from app.scheduler.dispatcher import create_notification_record, submit_async_fcm_dispatch
from app.services.reminder_service import calculate_next_trigger
from app.services.history_service import is_duplicate_history


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
            # Ensure timezone awareness for delta comparison
            last_trig = r.last_triggered_at
            if last_trig.tzinfo is None:
                last_trig = last_trig.replace(tzinfo=now.tzinfo)
            delta = (now - last_trig).total_seconds()
            if delta < 60:
                continue
        due_reminders.append(r)

    if due_reminders:
        print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 1: SCHEDULER_EXECUTION] Found {len(due_reminders)} due reminder(s). Job ID: medicine_reminders", flush=True)

    for reminder in due_reminders:
        try:
            medicine_id = getattr(reminder, "medicine_id", reminder.medicine.id)
            user_id = reminder.medicine.treatment.user_id
            treatment_id = reminder.medicine.treatment_id
            medicine_name = reminder.medicine.medicine_name

            print(f"[TRACE {datetime.utcnow().isoformat()}] Processing due Reminder ID: {reminder.id}, Medicine: {medicine_name}", flush=True)

            # 1. Update reminder timestamps atomically
            reminder.last_triggered_at = now
            reminder.next_trigger_at = calculate_next_trigger(
                reminder.reminder_time,
                reminder.repeat_type,
                base_datetime=now
            )

            # 2. Create Notification DB record
            notification = create_notification_record(
                db=db,
                reminder=reminder,
                medicine_name=medicine_name,
                user_id=user_id
            )

            # 3. Create History DB record if not duplicate
            if not is_duplicate_history(db, user_id, treatment_id, HistoryStatus.REMINDER_TRIGGERED.value, medicine_id):
                hist = History(
                    user_id=user_id,
                    treatment_id=treatment_id,
                    medicine_id=medicine_id,
                    reminder_id=reminder.id,
                    scheduled_time=now,
                    action_time=now,
                    status=HistoryStatus.REMINDER_TRIGGERED.value,
                    notes=f"Reminder triggered for '{medicine_name}'."
                )
                db.add(hist)

            # 4. SINGLE ATOMIC COMMIT FOR ALL REMINDER DATABASE UPDATES!
            db.commit()
            db.refresh(reminder)
            print(f"[TRACE {datetime.utcnow().isoformat()}] [ATOMIC_COMMIT_SUCCESS] Reminder ID {reminder.id} committed cleanly. next_trigger_at = {reminder.next_trigger_at}", flush=True)

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
            print(f"[ENGINE_ERROR] Database error processing Reminder ID {reminder.id}: {db_err}", flush=True)
        except Exception as e:
            db.rollback()
            print(f"[ENGINE_ERROR] Unexpected error processing Reminder ID {reminder.id}: {e}", flush=True)