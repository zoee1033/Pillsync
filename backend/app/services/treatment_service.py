from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.treatment import Treatment
from app.models.user import User
from app.schemas.treatment_schema import (
    TreatmentCreate,
    TreatmentUpdate
)


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

    db.delete(treatment)
    db.commit()

    return {
        "message": "Treatment deleted successfully."
    }