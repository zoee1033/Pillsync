from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler.jobs import reminder_job

scheduler = BackgroundScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            reminder_job,
            trigger="interval",
            seconds=1,
            id="medicine_reminders",
            max_instances=3,
            coalesce=True,
            misfire_grace_time=15,
            replace_existing=True,
        )
        scheduler.start()
        print("⏰ APScheduler initialized with 1-second interval and max_instances=3", flush=True)