from datetime import datetime
from sqlalchemy import or_, and_

from app.models.reminder import Reminder
from app.scheduler.dispatcher import dispatch_reminder
from app.services.reminder_service import calculate_next_trigger


def process_due_reminders(db):
    """
    Find reminders that are due based on next_trigger_at.
    Dispatches notifications, sets last_triggered_at, and advances next_trigger_at.
    """

    now = datetime.now().astimezone()

    reminders = (
        db.query(Reminder)
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

    print(f"⏰ Scheduler checking due reminders at {now}. Found {len(reminders)} due reminder(s).", flush=True)

    for reminder in reminders:
        try:
            dispatch_reminder(db, reminder)
        except Exception as e:
            print(f"Error dispatching reminder ID {reminder.id}: {e}", flush=True)

        try:
            reminder.last_triggered_at = now
            reminder.next_trigger_at = calculate_next_trigger(
                reminder.reminder_time,
                reminder.repeat_type,
                base_datetime=now
            )
            db.commit()
            db.refresh(reminder)
            print(f"Reminder ID {reminder.id} updated: next_trigger_at = {reminder.next_trigger_at}", flush=True)
        except Exception as e:
            db.rollback()
            print(f"Error updating reminder ID {reminder.id} trigger timestamp: {e}", flush=True)