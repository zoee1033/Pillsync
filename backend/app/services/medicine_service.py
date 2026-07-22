from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.medicine import Medicine
from app.models.treatment import Treatment
from app.models.user import User

from app.schemas.medicine_schema import (
    MedicineCreate,
    MedicineUpdate
)


# ==========================================================
# Create Medicine
# ==========================================================

def create_medicine(
    db: Session,
    medicine: MedicineCreate,
    current_user: User
):

    treatment = (
        db.query(Treatment)
        .filter(
            Treatment.id == medicine.treatment_id,
            Treatment.user_id == current_user.id
        )
        .first()
    )

    if not treatment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found."
        )

    new_medicine = Medicine(
        treatment_id=medicine.treatment_id,
        medicine_name=medicine.medicine_name,
        medicine_type=medicine.medicine_type,
        dosage=medicine.dosage,
        quantity=medicine.quantity,
        instructions=medicine.instructions,
        is_active=medicine.is_active
    )

    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)

    return new_medicine


# ==========================================================
# Get All Medicines of a Treatment
# ==========================================================

def get_all_medicines(
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

    medicines = (
        db.query(Medicine)
        .filter(
            Medicine.treatment_id == treatment_id
        )
        .order_by(
            Medicine.created_at.desc()
        )
        .all()
    )

    return medicines


# ==========================================================
# Get Medicine By ID
# ==========================================================

def get_medicine_by_id(
    medicine_id: int,
    db: Session,
    current_user: User
):

    medicine = (
        db.query(Medicine)
        .join(Treatment)
        .filter(
            Medicine.id == medicine_id,
            Treatment.user_id == current_user.id
        )
        .first()
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found."
        )

    return medicine


# ==========================================================
# Update Medicine
# ==========================================================

def update_medicine(
    medicine_id: int,
    medicine_data: MedicineUpdate,
    db: Session,
    current_user: User
):

    medicine = get_medicine_by_id(
        medicine_id,
        db,
        current_user
    )

    update_data = medicine_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(medicine, key, value)

    db.commit()
    db.refresh(medicine)

    return medicine


# ==========================================================
# Delete Medicine
# ==========================================================

def delete_medicine(
    medicine_id: int,
    db: Session,
    current_user: User
):

    medicine = get_medicine_by_id(
        medicine_id,
        db,
        current_user
    )

    db.delete(medicine)
    db.commit()

    return {
        "message": "Medicine deleted successfully."
    }