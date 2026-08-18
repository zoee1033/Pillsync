import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduler.jobs import (
    reminder_scheduler_job,
    refill_scheduler_job,
    expired_treatment_job,
    notification_cleanup_job,
    scheduler_health_check_job
)

logger = logging.getLogger("SCHEDULER")

_scheduler_instance = None


def get_scheduler() -> BackgroundScheduler:
    """Returns singleton BackgroundScheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BackgroundScheduler()
    return _scheduler_instance


def start_scheduler():
    """
    Initializes and starts the production-grade APScheduler instance with:
    - Protection against duplicate scheduler running instances.
    - Configurable reminder execution interval (REMINDER_INTERVAL_SECONDS).
    - Separate dedicated jobs for Reminders, Refill, Expired Treatments, Notification Cleanup, and Health Check.
    - Coalesce missed jobs & misfire grace time protection.
    """
    scheduler = get_scheduler()

    if not scheduler.running:
        reminder_interval = int(os.getenv("REMINDER_INTERVAL_SECONDS", "1"))

        # Job 1: Reminder Scheduler
        scheduler.add_job(
            reminder_scheduler_job,
            trigger="interval",
            seconds=reminder_interval,
            id="medicine_reminders",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
            replace_existing=True,
        )

        # Job 2: Refill Notifications (every 1 hour)
        scheduler.add_job(
            refill_scheduler_job,
            trigger="interval",
            minutes=60,
            id="refill_notifications",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
            replace_existing=True,
        )

        # Job 3: Expired Treatment Cleanup (every 1 hour)
        scheduler.add_job(
            expired_treatment_job,
            trigger="interval",
            minutes=60,
            id="expired_treatments",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
            replace_existing=True,
        )

        # Job 4: Notification Retention Cleanup (every 24 hours)
        scheduler.add_job(
            notification_cleanup_job,
            trigger="interval",
            hours=24,
            id="notification_cleanup",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
            replace_existing=True,
        )

        # Job 5: Scheduler Health Check Pulse (every 1 minute)
        scheduler.add_job(
            scheduler_health_check_job,
            trigger="interval",
            seconds=60,
            id="scheduler_health_check",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
            replace_existing=True,
        )

        scheduler.start()
        logger.info(f"APScheduler initialized with {reminder_interval}s interval and separate dedicated jobs.")


def stop_scheduler():
    """Gracefully shuts down scheduler instance on application teardown."""
    global _scheduler_instance
    if _scheduler_instance and _scheduler_instance.running:
        _scheduler_instance.shutdown(wait=False)
        logger.info("APScheduler stopped cleanly.")