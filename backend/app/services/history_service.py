from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import HistoryStatus
from app.models.history import History
from app.models.medicine import Medicine
from app.models.notification import Notification
from app.models.reminder import Reminder
from app.models.treatment import Treatment
from app.models.user import User

from app.schemas.history_schema import (
    HistoryCreate,
    HistoryUpdate
)


def is_duplicate_history(
    db: Session,
    user_id: int,
    treatment_id: int,
    status_str: str,
    medicine_id: int | None = None
) -> bool:
    """Check if an equivalent automatic history entry already exists."""
    query = db.query(History).filter(
        History.user_id == user_id,
        History.treatment_id == treatment_id,
        History.status == status_str
    )
    if medicine_id is not None:
        query = query.filter(History.medicine_id == medicine_id)
    return query.first() is not None


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

    medicine = None
    if history.medicine_id:
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
                detail="Medicine not found for this treatment."
            )

    reminder = None
    if history.reminder_id:
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine must be specified when reminder is provided."
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
                detail="Reminder not found for this medicine."
            )

    new_history = History(
        user_id=treatment.user_id,
        treatment_id=history.treatment_id,
        medicine_id=history.medicine_id,
        reminder_id=history.reminder_id,
        scheduled_time=history.scheduled_time,
        action_time=datetime.utcnow(),
        status=history.status,
        skip_reason=history.skip_reason,
        notes=history.notes
    )

    if reminder:
        from app.services.reminder_service import calculate_next_trigger
        if history.status in [HistoryStatus.TAKEN.value, HistoryStatus.SKIPPED.value]:
            reminder.next_trigger_at = calculate_next_trigger(
                reminder.reminder_time,
                getattr(reminder, "repeat_type", "Daily")
            )

    if history.status == HistoryStatus.TAKEN.value and medicine:
        med_qty = getattr(medicine, "quantity", None)
        if med_qty and med_qty > 0:
            medicine.quantity = med_qty - 1

            if medicine.quantity <= 3:
                existing_refill = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == current_user.id,
                        Notification.title == "Refill Warning",
                        Notification.message.like(f"%{medicine.medicine_name}%"),
                        Notification.is_read == False
                    )
                    .first()
                )
                if not existing_refill:
                    rem_id = reminder.id if reminder else None
                    refill_notif = Notification(
                        user_id=treatment.user_id,
                        reminder_id=rem_id,
                        title="Refill Warning",
                        message=f"Refill needed for {medicine.medicine_name}. Remaining stock: {medicine.quantity}.",
                        notification_type="Refill",
                        is_read=False
                    )
                    db.add(refill_notif)

    db.add(new_history)
    db.commit()
    db.refresh(new_history)

    new_history.medicine_name = getattr(medicine, "medicine_name", None) if medicine else None
    new_history.dosage = getattr(medicine, "dosage", None) if medicine else None
    new_history.treatment_name = getattr(treatment, "disease_name", None) if treatment else None
    start_d = getattr(treatment, "start_date", None) if treatment else None
    end_d = getattr(treatment, "end_date", None) if treatment else None
    treat_status = getattr(treatment, "status", None) if treatment else None
    new_history.start_date = start_d
    new_history.end_date = end_d
    new_history.completion_date = end_d if treat_status == "Completed" else None
    if start_d and end_d:
        days = (end_d - start_d).days
        new_history.duration = f"{max(days, 1)} days"
    else:
        new_history.duration = None
    new_history.reminder_time = str(reminder.reminder_time) if reminder and getattr(reminder, "reminder_time", None) else None

    return new_history


# ==========================================================
# Get User History
# ==========================================================

def get_history(
    db: Session,
    current_user: User
):

    results = (
        db.query(
            History,
            Medicine.medicine_name,
            Medicine.dosage,
            Treatment.disease_name,
            Treatment.start_date,
            Treatment.end_date,
            Treatment.status.label("treatment_status"),
            Reminder.reminder_time
        )
        .outerjoin(Medicine, History.medicine_id == Medicine.id)
        .outerjoin(Treatment, History.treatment_id == Treatment.id)
        .outerjoin(Reminder, History.reminder_id == Reminder.id)
        .filter(
            History.user_id == current_user.id
        )
        .order_by(
            History.action_time.desc()
        )
        .all()
    )

    history_list = []
    for item, med_name, dosage, treat_name, start_d, end_d, treat_status, rem_time in results:
        item.medicine_name = med_name
        item.dosage = dosage
        item.treatment_name = treat_name
        item.start_date = start_d
        item.end_date = end_d
        item.completion_date = end_d if treat_status == "Completed" else None
        if start_d and end_d:
            days = (end_d - start_d).days
            item.duration = f"{max(days, 1)} days"
        else:
            item.duration = None
        item.reminder_time = str(rem_time) if rem_time is not None else None
        history_list.append(item)

    return history_list


def _populate_history_details(history: History, db: Session) -> History:
    if not history:
        return history
    med = db.query(Medicine).filter(Medicine.id == history.medicine_id).first() if history.medicine_id else None
    treat = db.query(Treatment).filter(Treatment.id == history.treatment_id).first() if history.treatment_id else None
    rem = db.query(Reminder).filter(Reminder.id == history.reminder_id).first() if history.reminder_id else None
    history.medicine_name = med.medicine_name if med else None
    history.dosage = med.dosage if med else None
    history.treatment_name = treat.disease_name if treat else None
    history.start_date = treat.start_date if treat else None
    history.end_date = treat.end_date if treat else None
    history.completion_date = treat.end_date if treat and treat.status == "Completed" else None
    if treat and treat.start_date and treat.end_date:
        days = (treat.end_date - treat.start_date).days
        history.duration = f"{max(days, 1)} days"
    else:
        history.duration = None
    history.reminder_time = str(rem.reminder_time) if rem and rem.reminder_time else None
    return history


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

    return _populate_history_details(history, db)


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

    return _populate_history_details(history, db)


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

    history.status = HistoryStatus.TAKEN.value
    history.action_time = datetime.utcnow()

    db.commit()
    db.refresh(history)

    return _populate_history_details(history, db)


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

    history.status = HistoryStatus.SKIPPED.value
    history.skip_reason = reason
    history.action_time = datetime.utcnow()

    db.commit()
    db.refresh(history)

    return _populate_history_details(history, db)


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

    history.status = HistoryStatus.MISSED.value
    history.action_time = datetime.utcnow()

    db.commit()
    db.refresh(history)

    return _populate_history_details(history, db)