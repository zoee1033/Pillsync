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


# ==========================================================
# Refill Prediction Engine
# ==========================================================

def get_refill_predictions(db: Session, current_user: User):
    """
    Calculates stock countdown, estimated finish date, and refill recommended dates dynamically.
    Daily Consumption = Dose * Doses Per Day
    Remaining Days = Current Stock / Daily Consumption
    Refill Date = Today + Remaining Days (Formatted e.g. '30 Aug')
    Thresholds: >15 Days (Healthy/Green), 8-15 Days (Refill Soon/Yellow), 4-7 Days (Urgent/Orange), <=3 Days (Critical/Red)
    """
    from datetime import datetime, timedelta
    import re
    from app.models.reminder import Reminder

    medicines = get_all_user_medicines(db, current_user)
    predictions = []
    now = datetime.now()

    for med in medicines:
        reminders = db.query(Reminder).filter(Reminder.medicine_id == med.id, Reminder.status == "Active").all()

        dose_match = re.search(r'(\d+)', med.dosage or "1")
        dose_per_intake = int(dose_match.group(1)) if dose_match else 1
        if dose_per_intake <= 0:
            dose_per_intake = 1

        times_per_day = len(reminders) if reminders else 1
        daily_consumption = dose_per_intake * times_per_day
        remaining_tablets = max(0, med.quantity)

        remaining_days = int(remaining_tablets / daily_consumption) if daily_consumption > 0 else 30

        refill_dt = now + timedelta(days=remaining_days)
        refill_date_str = refill_dt.strftime("%d %b")

        # 4-Tier Refill Status Classification
        if remaining_days > 15:
            status_category = "Healthy"
            progress_color = "Green"
            hex_color = "#10B981"
            badge_icon = "🟢"
        elif 8 <= remaining_days <= 15:
            status_category = "Refill Soon"
            progress_color = "Yellow"
            hex_color = "#F59E0B"
            badge_icon = "🟡"
        elif 4 <= remaining_days <= 7:
            status_category = "Urgent"
            progress_color = "Orange"
            hex_color = "#F97316"
            badge_icon = "🟠"
        else:
            status_category = "Critical"
            progress_color = "Red"
            hex_color = "#EF4444"
            badge_icon = "🔴"

        # Stock ratio percentage (assuming 30 or current max stock)
        estimated_initial_stock = max(remaining_tablets, 30)
        progress_percent = min(100, max(0, int((remaining_tablets / estimated_initial_stock) * 100)))

        predictions.append({
            "medicine_id": med.id,
            "medicine_name": med.medicine_name,
            "medicine_type": med.medicine_type,
            "current_stock": remaining_tablets,
            "dose_per_intake": dose_per_intake,
            "times_per_day": times_per_day,
            "daily_consumption": daily_consumption,
            "remaining_days": remaining_days,
            "refill_date": refill_date_str,
            "estimated_finish_date": refill_dt.strftime("%Y-%m-%d"),
            "refill_recommended_date": refill_date_str,
            "status_category": status_category,
            "progress_color": progress_color,
            "hex_color": hex_color,
            "badge_icon": badge_icon,
            "progress_percent": progress_percent,
            "is_low_stock": remaining_days <= 7
        })

    return predictions


# ==========================================================
# Dosage Analysis
# ==========================================================

def get_dosage_analysis(medicine_id: int, db: Session, current_user: User):
    """
    Returns dosage breakdown, dose execution stats, and visual timeline per time slot.
    """
    medicine = get_medicine_by_id(medicine_id, db, current_user)
    history_records = db.query(History).filter(History.medicine_id == medicine_id).all()

    completed_doses = sum(1 for h in history_records if h.status == HistoryStatus.TAKEN.value)
    missed_doses = sum(1 for h in history_records if h.status == HistoryStatus.MISSED.value)
    skipped_doses = sum(1 for h in history_records if h.status == HistoryStatus.SKIPPED.value)

    total_doses = completed_doses + missed_doses + skipped_doses + max(0, medicine.quantity)

    # Time slot visual timeline (Morning, Afternoon, Night)
    from datetime import datetime
    now_hour = datetime.now().hour

    morning_status = "Completed" if completed_doses > 0 else ("Missed" if now_hour > 12 else "Upcoming")
    afternoon_status = "Completed" if completed_doses > 1 else ("Missed" if now_hour > 17 else "Upcoming")
    night_status = "Upcoming" if now_hour < 21 else "Completed"

    timeline = [
        {"slot": "Morning", "time": "08:00 AM", "status": morning_status},
        {"slot": "Afternoon", "time": "02:00 PM", "status": afternoon_status},
        {"slot": "Night", "time": "08:00 PM", "status": night_status}
    ]

    return {
        "medicine_id": medicine.id,
        "medicine_name": medicine.medicine_name,
        "total_prescribed_doses": total_doses,
        "completed_doses": completed_doses,
        "missed_doses": missed_doses,
        "skipped_doses": skipped_doses,
        "remaining_schedule": medicine.quantity,
        "visual_timeline": timeline
    }