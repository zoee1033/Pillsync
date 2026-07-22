from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.history import History
from app.models.medicine import Medicine
from app.models.reminder import Reminder
from app.models.treatment import Treatment
from app.models.user import User

from app.schemas.history_schema import (
    HistoryCreate,
    HistoryUpdate
)


# ==========================================================
# Create History Record
# ==========================================================

def create_history(
    db: Session,
    history: HistoryCreate,
    current_user: User
):

    treatment = (
        db.query(Treatment)
        .filter(
            Treatment.id == history.treatment_id,
            Treatment.user_id == current_user.id
        )
        .first()
    )

    if not treatment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found."
        )

    medicine = (
        db.query(Medicine)
        .filter(
            Medicine.id == history.medicine_id,
            Medicine.treatment_id == treatment.id
        )
        .first()
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found."
        )

    reminder = (
        db.query(Reminder)
        .filter(
            Reminder.id == history.reminder_id,
            Reminder.medicine_id == medicine.id
        )
        .first()
    )

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found."
        )

    new_history = History(
        user_id=current_user.id,
        treatment_id=history.treatment_id,
        medicine_id=history.medicine_id,
        reminder_id=history.reminder_id,
        scheduled_time=history.scheduled_time,
        action_time=datetime.utcnow(),
        status=history.status,
        skip_reason=history.skip_reason,
        notes=history.notes
    )

    db.add(new_history)
    db.commit()
    db.refresh(new_history)

    return new_history


# ==========================================================
# Get User History
# ==========================================================

def get_history(
    db: Session,
    current_user: User
):

    return (
        db.query(History)
        .filter(
            History.user_id == current_user.id
        )
        .order_by(
            History.action_time.desc()
        )
        .all()
    )


# ==========================================================
# Get History By ID
# ==========================================================

def get_history_by_id(
    history_id: int,
    db: Session,
    current_user: User
):

    history = (
        db.query(History)
        .filter(
            History.id == history_id,
            History.user_id == current_user.id
        )
        .first()
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History record not found."
        )

    return history


# ==========================================================
# Update History
# ==========================================================

def update_history(
    history_id: int,
    history_data: HistoryUpdate,
    db: Session,
    current_user: User
):

    history = get_history_by_id(
        history_id,
        db,
        current_user
    )

    update_data = history_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(history, key, value)

    db.commit()
    db.refresh(history)

    return history


# ==========================================================
# Delete History
# ==========================================================

def delete_history(
    history_id: int,
    db: Session,
    current_user: User
):

    history = get_history_by_id(
        history_id,
        db,
        current_user
    )

    db.delete(history)
    db.commit()

    return {
        "message": "History deleted successfully."
    }


# ==========================================================
# Mark Medicine Taken
# ==========================================================

def mark_taken(
    history_id: int,
    db: Session,
    current_user: User
):

    history = get_history_by_id(
        history_id,
        db,
        current_user
    )

    history.status = "Taken"
    history.action_time = datetime.utcnow()

    db.commit()
    db.refresh(history)

    return history


# ==========================================================
# Mark Medicine Skipped
# ==========================================================

def mark_skipped(
    history_id: int,
    reason: str,
    db: Session,
    current_user: User
):

    history = get_history_by_id(
        history_id,
        db,
        current_user
    )

    history.status = "Skipped"
    history.skip_reason = reason
    history.action_time = datetime.utcnow()

    db.commit()
    db.refresh(history)

    return history


# ==========================================================
# Mark Medicine Missed
# ==========================================================

def mark_missed(
    history_id: int,
    db: Session,
    current_user: User
):

    history = get_history_by_id(
        history_id,
        db,
        current_user
    )

    history.status = "Missed"
    history.action_time = datetime.utcnow()

    db.commit()
    db.refresh(history)

    return history