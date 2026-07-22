from app.database import SessionLocal
from app.scheduler.reminder_engine import process_due_reminders


def reminder_job():
    db = SessionLocal()

    try:
        process_due_reminders(db)

    finally:
        db.close()