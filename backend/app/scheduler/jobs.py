from datetime import date, datetime
from app.database import SessionLocal
from app.models.enums import HistoryStatus
from app.models.history import History
from app.models.treatment import Treatment
from app.scheduler.reminder_engine import process_due_reminders
from app.services.history_service import is_duplicate_history


def check_expired_treatments(db):
    today = date.today()
    expired_treatments = (
        db.query(Treatment)
        .filter(
            Treatment.status == "Active",
            Treatment.end_date < today
        )
        .all()
    )

    for treatment in expired_treatments:
        treatment.status = HistoryStatus.EXPIRED.value
        if not is_duplicate_history(db, treatment.user_id, treatment.id, HistoryStatus.EXPIRED.value):
            hist = History(
                user_id=treatment.user_id,
                treatment_id=treatment.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.EXPIRED.value,
                notes=f"Treatment '{treatment.disease_name}' expired on {treatment.end_date}."
            )
            db.add(hist)
    db.commit()


def reminder_job():
    db = SessionLocal()

    try:
        print(f"⏰ APScheduler executing reminder job at {datetime.now()}", flush=True)
        process_due_reminders(db)
        check_expired_treatments(db)
    finally:
        db.close()