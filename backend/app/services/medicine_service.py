from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.enums import HistoryStatus
from app.models.history import History
from app.models.medicine import Medicine
from app.models.treatment import Treatment
from app.models.user import User

from app.schemas.medicine_schema import (
    MedicineCreate,
    MedicineUpdate
)
from app.services.history_service import is_duplicate_history
from app.utils.medicine_validator import validate_medicine_name


# ==========================================================
# Create Medicine
# ==========================================================

def create_medicine(
    db: Session,
    medicine: MedicineCreate,
    current_user: User
):
    # Validate medicine name before creation
    is_valid, err_msg = validate_medicine_name(medicine.medicine_name)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

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

    # Log Medicine Added history
    if not is_duplicate_history(db, current_user.id, new_medicine.treatment_id, HistoryStatus.MEDICINE_ADDED.value, new_medicine.id):
        hist = History(
            user_id=current_user.id,
            treatment_id=new_medicine.treatment_id,
            medicine_id=new_medicine.id,
            scheduled_time=datetime.utcnow(),
            action_time=datetime.utcnow(),
            status=HistoryStatus.MEDICINE_ADDED.value,
            notes=f"Medicine '{new_medicine.medicine_name}' added to treatment."
        )
        db.add(hist)
        db.commit()

    return new_medicine


# ==========================================================
# Get All Medicines for the Current User
# ==========================================================

def get_all_user_medicines(
    db: Session,
    current_user: User
):

    medicines = (
        db.query(Medicine)
        .join(Medicine.treatment)
        .filter(
            Treatment.user_id == current_user.id
        )
        .order_by(
            Medicine.created_at.desc()
        )
        .all()
    )

    return medicines


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

    if "medicine_name" in update_data and update_data["medicine_name"]:
        is_valid, err_msg = validate_medicine_name(update_data["medicine_name"])
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )

    for key, value in update_data.items():
        setattr(medicine, key, value)

    db.commit()
    db.refresh(medicine)

    if not medicine.is_active or medicine.quantity <= 0:
        user_id = medicine.treatment.user_id
        if not is_duplicate_history(db, user_id, medicine.treatment_id, HistoryStatus.MEDICINE_COMPLETED.value, medicine.id):
            hist = History(
                user_id=user_id,
                treatment_id=medicine.treatment_id,
                medicine_id=medicine.id,
                scheduled_time=datetime.utcnow(),
                action_time=datetime.utcnow(),
                status=HistoryStatus.MEDICINE_COMPLETED.value,
                notes=f"Medicine '{medicine.medicine_name}' course completed."
            )
            db.add(hist)
            db.commit()

        # Check if ALL medicines in treatment are completed
        all_meds = db.query(Medicine).filter(Medicine.treatment_id == medicine.treatment_id).all()
        if all(not m.is_active or m.quantity <= 0 for m in all_meds):
            if not is_duplicate_history(db, user_id, medicine.treatment_id, HistoryStatus.COMPLETED.value):
                t_hist = History(
                    user_id=user_id,
                    treatment_id=medicine.treatment_id,
                    scheduled_time=datetime.utcnow(),
                    action_time=datetime.utcnow(),
                    status=HistoryStatus.COMPLETED.value,
                    notes=f"All medicines completed for treatment '{medicine.treatment.disease_name}'."
                )
                db.add(t_hist)
                medicine.treatment.status = HistoryStatus.COMPLETED.value
                db.commit()

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