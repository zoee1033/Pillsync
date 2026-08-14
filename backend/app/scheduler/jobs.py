import time
import logging
from datetime import date, datetime
from app.database import SessionLocal
from app.models.enums import HistoryStatus
from app.models.history import History
from app.models.treatment import Treatment
from app.scheduler.reminder_engine import process_due_reminders
from app.services.history_service import is_duplicate_history
from app.services.notification_service import cleanup_old_notifications

logger = logging.getLogger("SCHEDULER_JOBS")


def check_expired_treatments(db):
    """Scans active treatments and marks expired ones."""
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
    return len(expired_treatments)


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

    created_count = 0
    for med in active_medicines:
        user_id = med.treatment.user_id
        reminders = db.query(Reminder).filter(Reminder.medicine_id == med.id, Reminder.status == "Active").all()

        dose_per_intake = 1
        if med.dosage:
            tab_match = re.search(r'(\d+)\s*(?:tablets?|tabs?|caps?|capsules?|pills?|units?|puffs?)\b', med.dosage, re.IGNORECASE)
            if tab_match:
                dose_per_intake = int(tab_match.group(1))
            else:
                num_match = re.search(r'^\s*(\d+)\s*$', med.dosage)
                if num_match:
                    dose_per_intake = int(num_match.group(1))
        if dose_per_intake <= 0:
            dose_per_intake = 1

        daily_cons = dose_per_intake * (len(reminders) if reminders else 1)

        # 1. Determine remaining treatment duration (days relative to today)
        parsed_duration = None
        if med.treatment and med.treatment.end_date:
            try:
                today = date.today()
                t_days = (med.treatment.end_date - today).days
                if t_days > 0:
                    parsed_duration = t_days
            except Exception:
                pass

        if parsed_duration is None and med.instructions:
            dur_match = re.search(r'(?:duration:?\s*|for\s*|^|\b)(\d+)\s*(?:days?|d)\b', med.instructions, re.IGNORECASE)
            if dur_match:
                parsed_duration = int(dur_match.group(1))

        remaining_treatment_days = parsed_duration if (parsed_duration is not None and parsed_duration > 0) else 1

        # 2. Compute required stock for remaining treatment
        required_stock = remaining_treatment_days * daily_cons
        current_stock = max(0, med.quantity)

        # 3. Decision: Refill needed ONLY IF current_stock < required_stock
        notif_data = None
        if current_stock < required_stock:
            if current_stock <= 0 or med.quantity <= 0:
                notif_data = ("❌ Medicine Out of Stock", f"No tablets remaining for {med.medicine_name}. Upcoming reminders may be affected.")
            else:
                notif_data = ("⚠️ Refill Reminder", f"Stock ({current_stock} tablets) is insufficient for remaining treatment ({remaining_treatment_days} days). Please arrange a refill.")

        if notif_data:
            title, message = notif_data
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
                created_count += 1

    return created_count


# ==========================================================
# Dedicated Modular APScheduler Jobs
# ==========================================================

def reminder_scheduler_job():
    """Independent Reminder Scheduler Job."""
    from app.config import settings
    if settings.ENABLE_VERBOSE_SCHEDULER_LOGS:
        logger.debug(f"Running reminder scheduler at {datetime.utcnow().isoformat()}...")
    db = SessionLocal()
    try:
        process_due_reminders(db)
    except Exception as e:
        logger.error(f"Error in reminder scheduler job: {e}", exc_info=True)
    finally:
        db.close()


def refill_scheduler_job():
    """Independent Refill Notification Scheduler Job."""
    from app.config import settings
    if settings.ENABLE_VERBOSE_SCHEDULER_LOGS:
        logger.debug(f"Running refill scheduler at {datetime.utcnow().isoformat()}...")
    db = SessionLocal()
    try:
        count = check_refill_notifications(db)
        if count > 0:
            logger.info(f"Refill scheduler processed. Generated {count} new refill alert(s).")
    except Exception as e:
        logger.error(f"Error in refill scheduler job: {e}", exc_info=True)
    finally:
        db.close()


def expired_treatment_job():
    """Independent Expired Treatment Cleanup Job."""
    from app.config import settings
    if settings.ENABLE_VERBOSE_SCHEDULER_LOGS:
        logger.debug(f"Running expired treatment cleanup at {datetime.utcnow().isoformat()}...")
    db = SessionLocal()
    try:
        count = check_expired_treatments(db)
        if count > 0:
            logger.info(f"Expired treatment cleanup processed {count} treatment(s).")
    except Exception as e:
        logger.error(f"Error in expired treatment job: {e}", exc_info=True)
    finally:
        db.close()


def notification_cleanup_job():
    """Independent Old Notification Cleanup Job."""
    from app.config import settings
    if settings.ENABLE_VERBOSE_SCHEDULER_LOGS:
        logger.debug(f"Running notification cleanup job at {datetime.utcnow().isoformat()}...")
    db = SessionLocal()
    try:
        deleted = cleanup_old_notifications(db, days=30)
        if deleted > 0:
            logger.info(f"Notification cleanup job deleted {deleted} old notification(s).")
    except Exception as e:
        logger.error(f"Error in notification cleanup job: {e}", exc_info=True)
    finally:
        db.close()


def scheduler_health_check_job():
    """Independent Scheduler Health Check Pulse."""
    from app.config import settings
    if settings.ENABLE_VERBOSE_SCHEDULER_LOGS:
        logger.debug(f"Health check pulse at {datetime.utcnow().isoformat()} - Scheduler active.")


def reminder_job():
    """Backward compatible composite job execution."""
    reminder_scheduler_job()
    expired_treatment_job()
    refill_scheduler_job()