from datetime import datetime

from app.models.reminder import Reminder
from app.scheduler.dispatcher import dispatch_reminder


def process_due_reminders(db):
    """
    Find reminders that should be triggered now.
    """

    current_time = datetime.now().time().replace(second=0, microsecond=0)

    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.reminder_time == current_time,
            Reminder.notification_enabled == True,
            Reminder.status == "Active",
        )
        .all()
    )

    print(f"Found {len(reminders)} reminder(s)")

    for reminder in reminders:
        dispatch_reminder(db, reminder)