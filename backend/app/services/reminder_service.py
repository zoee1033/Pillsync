from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.history import History
from app.models.medicine import Medicine
from app.models.reminder import Reminder
from app.models.treatment import Treatment
from app.models.user import User

from app.schemas.reminder_schema import (
    ReminderCreate,
    ReminderUpdate
)


# ==========================================================
# Helper Function
# ==========================================================

def calculate_next_trigger(reminder_time, repeat_type="Daily", base_datetime=None):
    from datetime import time as time_type
    if isinstance(reminder_time, str):
        reminder_time = time_type.fromisoformat(reminder_time)
    now = base_datetime or datetime.now().astimezone()

    if now.tzinfo is not None:
        today_trigger = datetime.combine(now.date(), reminder_time).replace(tzinfo=now.tzinfo)
    else:
        today_trigger = datetime.combine(now.date(), reminder_time)

    if today_trigger > now:
        return today_trigger

    if repeat_type == "Weekly":
        return today_trigger + timedelta(days=7)
    elif repeat_type == "Monthly":
        return today_trigger + timedelta(days=30)
    else:  # Daily, Custom, or default
        return today_trigger + timedelta(days=1)


# ==========================================================
# Create Reminder
# ==========================================================

def create_reminder(
    db: Session,
    reminder: ReminderCreate,
    current_user: User
):

    medicine = (
        db.query(Medicine)
        .join(Medicine.treatment)
        .filter(
            Medicine.id == reminder.medicine_id
        )
        .first()
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found."
        )

    if medicine.treatment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    new_reminder = Reminder(
        medicine_id=reminder.medicine_id,
        reminder_time=reminder.reminder_time,
        repeat_type=reminder.repeat_type,
        notification_enabled=reminder.notification_enabled,
        snooze_minutes=reminder.snooze_minutes,
        next_trigger_at=calculate_next_trigger(
            reminder.reminder_time,
            reminder.repeat_type
        ),
        status=reminder.status
    )

    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)

    return new_reminder


# ==========================================================
# Get All Reminders for the Current User
# ==========================================================

def get_all_user_reminders(
    db: Session,
    current_user: User
):

    reminders = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Medicine.treatment)
        .filter(
            Treatment.user_id == current_user.id
        )
        .order_by(
            Reminder.reminder_time.asc()
        )
        .all()
    )

    return reminders


# ==========================================================
# Get All Reminders for a Medicine
# ==========================================================

def get_all_reminders(
    medicine_id: int,
    db: Session,
    current_user: User
):

    medicine = (
        db.query(Medicine)
        .join(Medicine.treatment)
        .filter(
            Medicine.id == medicine_id
        )
        .first()
    )

    if not medicine:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found."
        )

    if medicine.treatment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    return (
        db.query(Reminder)
        .filter(
            Reminder.medicine_id == medicine_id
        )
        .order_by(
            Reminder.reminder_time.asc()
        )
        .all()
    )


# ==========================================================
# Get Reminder By ID
# ==========================================================

def get_reminder_by_id(
    reminder_id: int,
    db: Session,
    current_user: User
):

    reminder = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Medicine.treatment)
        .filter(
            Reminder.id == reminder_id
        )
        .first()
    )

    if not reminder:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found."
        )

    if reminder.medicine.treatment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    return reminder


# ==========================================================
# Update Reminder
# ==========================================================

def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    db: Session,
    current_user: User
):

    reminder = get_reminder_by_id(
        reminder_id,
        db,
        current_user
    )

    update_data = reminder_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(reminder, key, value)

    if "reminder_time" in update_data or "repeat_type" in update_data:
        reminder.next_trigger_at = calculate_next_trigger(
            reminder.reminder_time,
            reminder.repeat_type
        )

    db.commit()
    db.refresh(reminder)

    return reminder


# ==========================================================
# Delete Reminder
# ==========================================================

def delete_reminder(
    reminder_id: int,
    db: Session,
    current_user: User
):

    reminder = get_reminder_by_id(
        reminder_id,
        db,
        current_user
    )

    db.delete(reminder)
    db.commit()

    return {
        "message": "Reminder deleted successfully."
    }


# ==========================================================
# Snooze Reminder
# ==========================================================

def snooze_reminder(
    reminder_id: int,
    minutes: int,
    db: Session,
    current_user: User
):

    reminder = get_reminder_by_id(
        reminder_id,
        db,
        current_user
    )

    now = datetime.now().astimezone()
    reminder.next_trigger_at = now + timedelta(minutes=minutes)

    history_entry = History(
        user_id=reminder.medicine.treatment.user_id,
        treatment_id=reminder.medicine.treatment_id,
        medicine_id=reminder.medicine_id,
        reminder_id=reminder.id,
        scheduled_time=now,
        action_time=now,
        status="Snoozed",
        notes=f"Snoozed for {minutes} minutes"
    )
    db.add(history_entry)

    db.commit()
    db.refresh(reminder)

    return reminder