from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler.jobs import reminder_job

scheduler = BackgroundScheduler()


def start_scheduler():

    scheduler.add_job(
        reminder_job,
        trigger="interval",
        minutes=1,
        id="medicine_reminders",
        replace_existing=True,
    )

    scheduler.start()

    print("Scheduler Started")