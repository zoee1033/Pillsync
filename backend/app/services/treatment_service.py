from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.enums import HistoryStatus
from app.models.history import History
from app.models.treatment import Treatment
from app.models.user import User
from app.schemas.treatment_schema import (
    TreatmentCreate,
    TreatmentUpdate
)
from app.services.history_service import is_duplicate_history


# ==========================================
# Create Treatment
# ==========================================

def create_treatment(
    db: Session,
    treatment: TreatmentCreate,
    current_user: User
):

    new_treatment = Treatment(
        user_id=current_user.id,
        disease_name=treatment.disease_name,
        doctor_name=treatment.doctor_name,
        diagnosis_date=treatment.diagnosis_date,
        start_date=treatment.start_date,
        end_date=treatment.end_date,
        status=treatment.status,
        notes=treatment.notes
    )

    db.add(new_treatment)
    db.commit()
    db.refresh(new_treatment)

    # Log initial treatment creation history
    start_status = HistoryStatus.TREATMENT_STARTED.value
    if not is_duplicate_history(db, current_user.id, new_treatment.id, start_status):
        hist = History(
            user_id=current_user.id,
            treatment_id=new_treatment.id,
            scheduled_time=datetime.utcnow(),
            action_time=datetime.utcnow(),
            status=start_status,
            notes=f"Treatment '{new_treatment.disease_name}' started."
        )
        db.add(hist)
        db.commit()

    if new_treatment.status == HistoryStatus.COMPLETED.value:
        if not is_duplicate_history(db, current_user.id, new_treatment.id, HistoryStatus.COMPLETED.value):
            hist = History(
                user_id=current_user.id,
                treatment_id=new_treatment.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.COMPLETED.value,
                notes="Treatment completed."
            )
            db.add(hist)
            db.commit()
    elif new_treatment.status == "Active" or new_treatment.status == HistoryStatus.TREATMENT_ACTIVE.value:
        if not is_duplicate_history(db, current_user.id, new_treatment.id, HistoryStatus.TREATMENT_ACTIVE.value):
            hist = History(
                user_id=current_user.id,
                treatment_id=new_treatment.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.TREATMENT_ACTIVE.value,
                notes="Treatment is active."
            )
            db.add(hist)
            db.commit()

    return new_treatment


# ==========================================
# Get All Treatments
# ==========================================

def get_all_treatments(
    db: Session,
    current_user: User
):

    return (
        db.query(Treatment)
        .filter(Treatment.user_id == current_user.id)
        .order_by(Treatment.created_at.desc())
        .all()
    )


# ==========================================
# Get Treatment By ID
# ==========================================

def get_treatment_by_id(
    treatment_id: int,
    db: Session,
    current_user: User
):

    treatment = (
        db.query(Treatment)
        .filter(
            Treatment.id == treatment_id,
            Treatment.user_id == current_user.id
        )
        .first()
    )

    if not treatment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found."
        )

    return treatment


# ==========================================
# Update Treatment
# ==========================================

def update_treatment(
    treatment_id: int,
    treatment_data: TreatmentUpdate,
    db: Session,
    current_user: User
):

    treatment = get_treatment_by_id(
        treatment_id,
        db,
        current_user
    )

    update_data = treatment_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(treatment, key, value)

    db.commit()
    db.refresh(treatment)

    if treatment.status == HistoryStatus.COMPLETED.value:
        if not is_duplicate_history(db, current_user.id, treatment.id, HistoryStatus.COMPLETED.value):
            hist = History(
                user_id=current_user.id,
                treatment_id=treatment.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.COMPLETED.value,
                notes="Treatment completed."
            )
            db.add(hist)
            db.commit()
    elif treatment.status == HistoryStatus.CANCELLED.value:
        if not is_duplicate_history(db, current_user.id, treatment.id, HistoryStatus.CANCELLED.value):
            hist = History(
                user_id=current_user.id,
                treatment_id=treatment.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.CANCELLED.value,
                notes="Treatment cancelled."
            )
            db.add(hist)
            db.commit()
    elif treatment.status == HistoryStatus.EXPIRED.value:
        if not is_duplicate_history(db, current_user.id, treatment.id, HistoryStatus.EXPIRED.value):
            hist = History(
                user_id=current_user.id,
                treatment_id=treatment.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.EXPIRED.value,
                notes="Treatment expired."
            )
            db.add(hist)
            db.commit()
    elif treatment.status in ["Active", HistoryStatus.TREATMENT_ACTIVE.value]:
        if not is_duplicate_history(db, current_user.id, treatment.id, HistoryStatus.TREATMENT_ACTIVE.value):
            hist = History(
                user_id=current_user.id,
                treatment_id=treatment.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.TREATMENT_ACTIVE.value,
                notes="Treatment active."
            )
            db.add(hist)
            db.commit()

    return treatment


# ==========================================
# Delete Treatment
# ==========================================

def delete_treatment(
    treatment_id: int,
    db: Session,
    current_user: User
):

    treatment = get_treatment_by_id(
        treatment_id,
        db,
        current_user
    )

    if not is_duplicate_history(db, current_user.id, treatment.id, HistoryStatus.CANCELLED.value):
        hist = History(
            user_id=current_user.id,
            treatment_id=treatment.id,
            scheduled_time=datetime.utcnow(),
            action_time=datetime.utcnow(),
            status=HistoryStatus.CANCELLED.value,
            notes=f"Treatment '{treatment.disease_name}' cancelled/deleted."
        )
        db.add(hist)
        db.commit()

    db.delete(treatment)
    db.commit()

    return {
        "message": "Treatment deleted successfully."
    }