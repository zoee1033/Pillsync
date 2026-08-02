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


def check_refill_notifications(db):
    """
    Scans active medicines, computes remaining days, and generates refill notifications
    at thresholds 7, 5, 3, 1, and 0 days. Continues persistent daily alerts until stock is updated.
    """
    import re
    from app.models.medicine import Medicine
    from app.models.reminder import Reminder
    from app.models.notification import Notification

    today_str = date.today().isoformat()
    active_medicines = (
        db.query(Medicine)
        .join(Medicine.treatment)
        .filter(Treatment.status == "Active", Medicine.is_active == True)
        .all()
    )

    for med in active_medicines:
        user_id = med.treatment.user_id
        reminders = db.query(Reminder).filter(Reminder.medicine_id == med.id, Reminder.status == "Active").all()

        dose_match = re.search(r'(\d+)', med.dosage or "1")
        dose_per_intake = int(dose_match.group(1)) if dose_match else 1
        daily_cons = dose_per_intake * (len(reminders) if reminders else 1)
        rem_days = int(max(0, med.quantity) / daily_cons) if daily_cons > 0 else 30

        # Refill Notification Thresholds
        notif_data = None
        if rem_days == 7:
            notif_data = ("💊 Refill Reminder", f"You have only 7 days of {med.medicine_name} remaining. Please arrange a refill soon.")
        elif rem_days == 5:
            notif_data = ("⚠️ Medicine Running Low", f"Only 5 days of {med.medicine_name} remaining. Please purchase a refill.")
        elif rem_days == 3:
            notif_data = ("🚨 Critical Refill Alert", f"Only 3 days left of {med.medicine_name}. Restock immediately to avoid missing doses.")
        elif rem_days == 1:
            notif_data = ("🚨 Final Warning", f"Today's supply of {med.medicine_name} is almost over. Please refill now.")
        elif rem_days <= 0 or med.quantity <= 0:
            notif_data = ("❌ Medicine Out of Stock", f"No tablets remaining for {med.medicine_name}. Upcoming reminders may be affected.")

        if notif_data:
            title, message = notif_data
            # Prevent duplicate notifications for the same medicine on the same day
            existing_today = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.reminder_id == (reminders[0].id if reminders else None),
                    Notification.notification_type == "Refill",
                    Notification.created_at >= datetime.combine(date.today(), datetime.min.time())
                )
                .first()
            )

            if not existing_today:
                new_notif = Notification(
                    user_id=user_id,
                    reminder_id=reminders[0].id if reminders else None,
                    title=title,
                    message=message,
                    notification_type="Refill",
                    is_sent=True,
                    sent_at=datetime.utcnow()
                )
                db.add(new_notif)
                db.commit()


def reminder_job():
    db = SessionLocal()

    try:
        print(f"⏰ APScheduler executing reminder job at {datetime.now()}", flush=True)
        process_due_reminders(db)
        check_expired_treatments(db)
        check_refill_notifications(db)
    finally:
        db.close()