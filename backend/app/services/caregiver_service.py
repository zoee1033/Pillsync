from datetime import datetime, date
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.caregiver_patient import CaregiverPatient
from app.models.treatment import Treatment
from app.models.medicine import Medicine
from app.models.reminder import Reminder
from app.models.history import History
from app.models.notification import Notification
from app.models.enums import HistoryStatus
from app.services.medicine_service import get_refill_predictions
from app.middleware.auth import verify_caregiver_patient_access


def get_assigned_patients(db: Session, caregiver_user: User) -> List[User]:
    """
    Returns list of User objects assigned to caregiver_user.
    If caregiver_user is admin, returns all patients.
    """
    user_role = (caregiver_user.role or "patient").lower()
    if user_role == "admin":
        return db.query(User).filter(User.role.ilike("patient")).all()

    links = db.query(CaregiverPatient).filter(
        CaregiverPatient.caregiver_id == caregiver_user.id,
        (CaregiverPatient.status == "active") | (CaregiverPatient.status == None)
    ).all()
    patient_ids = [l.patient_id for l in links]
    if not patient_ids:
        return []

    return db.query(User).filter(User.id.in_(patient_ids)).all()


def _compute_patient_summary(db: Session, patient: User) -> Dict[str, Any]:
    """
    Computes real summary metrics for a single patient using existing medicine & reminder logic.
    """
    # Active medicines & refill predictions
    predictions = get_refill_predictions(db, patient)
    active_med_count = len(predictions)

    statuses = [p.get("status_category", "Healthy") for p in predictions]
    if "Critical" in statuses:
        overall_status = "Critical"
    elif "Needs Refill" in statuses or "Urgent" in statuses or "Refill Soon" in statuses:
        overall_status = "Needs Refill"
    else:
        overall_status = "Healthy"

    # Today's history/progress
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_history = db.query(History).filter(
        History.user_id == patient.id,
        History.scheduled_time >= today_start
    ).all()

    completed = sum(1 for h in today_history if h.status in [HistoryStatus.TAKEN.value, "Completed", "Taken"])
    missed = sum(1 for h in today_history if h.status in [HistoryStatus.MISSED.value, "Missed"])

    # Reminders
    reminders = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Medicine.treatment)
        .filter(Treatment.user_id == patient.id, Reminder.status == "Active", Medicine.is_active == True)
        .order_by(Reminder.reminder_time.asc())
        .all()
    )
    total_reminders = len(reminders)
    scheduled_count = max(total_reminders, completed + missed)
    today_progress_pct = Math_round((completed / scheduled_count) * 100) if scheduled_count > 0 else 100

    next_reminder_str = "None Scheduled"
    if reminders:
        r = reminders[0]
        rem_time = r.reminder_time.strftime("%I:%M %p") if hasattr(r.reminder_time, 'strftime') else str(r.reminder_time)
        med_name = r.medicine.medicine_name if r.medicine else "Medicine"
        next_reminder_str = f"{rem_time} - {med_name}"

    has_attention = overall_status in ["Critical", "Needs Refill"] or missed > 0

    return {
        "patient_id": patient.id,
        "full_name": patient.full_name,
        "email": patient.email,
        "phone": patient.phone,
        "gender": patient.gender,
        "age": patient.age,
        "blood_group": patient.blood_group,
        "active_medicine_count": active_med_count,
        "medication_status": overall_status,
        "today_progress_pct": today_progress_pct,
        "today_completed": completed,
        "today_missed": missed,
        "next_reminder": next_reminder_str,
        "attention_indicator": has_attention,
        "predictions": predictions
    }


def Math_round(val):
    return int(round(val))


def get_caregiver_dashboard_data(db: Session, caregiver_user: User) -> Dict[str, Any]:
    patients = get_assigned_patients(db, caregiver_user)
    summaries = [_compute_patient_summary(db, p) for p in patients]

    total_patients = len(summaries)
    healthy_patients = sum(1 for s in summaries if s["medication_status"] == "Healthy")
    needs_attention = sum(1 for s in summaries if s["medication_status"] == "Needs Refill")
    critical_patients = sum(1 for s in summaries if s["medication_status"] == "Critical")

    attention_required = [s for s in summaries if s["attention_indicator"]]

    # Today's activity across assigned patients
    patient_ids = [p.id for p in patients]
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    activities = []
    if patient_ids:
        hist_records = (
            db.query(History)
            .filter(History.user_id.in_(patient_ids), History.scheduled_time >= today_start)
            .order_by(History.scheduled_time.desc())
            .limit(10)
            .all()
        )
        p_map = {p.id: p.full_name for p in patients}
        m_ids = [h.medicine_id for h in hist_records if h.medicine_id]
        meds = db.query(Medicine).filter(Medicine.id.in_(m_ids)).all() if m_ids else []
        m_map = {m.id: m.medicine_name for m in meds}

        for h in hist_records:
            activities.append({
                "id": h.id,
                "patient_name": p_map.get(h.user_id, f"Patient #{h.user_id}"),
                "medicine_name": m_map.get(h.medicine_id, "Medication"),
                "time": h.scheduled_time.strftime("%I:%M %p") if h.scheduled_time else "",
                "status": h.status,
                "notes": h.notes
            })

    # Upcoming reminders across assigned patients
    upcoming_reminders = []
    if patient_ids:
        rems = (
            db.query(Reminder)
            .join(Reminder.medicine)
            .join(Medicine.treatment)
            .filter(Treatment.user_id.in_(patient_ids), Reminder.status == "Active", Medicine.is_active == True)
            .order_by(Reminder.reminder_time.asc())
            .limit(10)
            .all()
        )
        p_map = {p.id: p.full_name for p in patients}
        for r in rems:
            rem_time = r.reminder_time.strftime("%I:%M %p") if hasattr(r.reminder_time, 'strftime') else str(r.reminder_time)
            patient_owner = r.medicine.treatment.user if r.medicine and r.medicine.treatment else None
            p_name = patient_owner.full_name if patient_owner else "Patient"
            upcoming_reminders.append({
                "id": r.id,
                "patient_name": p_name,
                "medicine_name": r.medicine.medicine_name if r.medicine else "Medicine",
                "reminder_time": rem_time,
                "status": r.status,
                "repeat_type": r.repeat_type
            })

    return {
        "caregiver_name": caregiver_user.full_name,
        "total_patients": total_patients,
        "healthy_patients": healthy_patients,
        "needs_attention": needs_attention,
        "critical_patients": critical_patients,
        "my_patients": summaries,
        "attention_required": attention_required,
        "today_activity": activities,
        "upcoming_reminders": upcoming_reminders
    }


def get_patient_detail_for_caregiver(db: Session, caregiver_user: User, patient_id: int) -> Dict[str, Any]:
    verify_caregiver_patient_access(db, caregiver_user, patient_id)

    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    summary = _compute_patient_summary(db, patient)

    # All patient reminders with real times
    reminders = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Medicine.treatment)
        .filter(Treatment.user_id == patient_id, Medicine.is_active == True)
        .all()
    )
    reminder_list = []
    for r in reminders:
        rem_time = r.reminder_time.strftime("%I:%M %p") if hasattr(r.reminder_time, 'strftime') else str(r.reminder_time)
        reminder_list.append({
            "id": r.id,
            "medicine_id": r.medicine_id,
            "medicine_name": r.medicine.medicine_name if r.medicine else "Medicine",
            "reminder_time": rem_time,
            "status": r.status,
            "repeat_type": r.repeat_type
        })

    # History
    history_records = (
        db.query(History)
        .filter(History.user_id == patient_id)
        .order_by(History.scheduled_time.desc())
        .limit(20)
        .all()
    )
    m_ids = [h.medicine_id for h in history_records if h.medicine_id]
    meds = db.query(Medicine).filter(Medicine.id.in_(m_ids)).all() if m_ids else []
    m_map = {m.id: m.medicine_name for m in meds}

    hist_list = []
    for h in history_records:
        hist_list.append({
            "id": h.id,
            "medicine_name": m_map.get(h.medicine_id, "Medication"),
            "date": h.scheduled_time.strftime("%Y-%m-%d") if h.scheduled_time else "",
            "scheduled_time": h.scheduled_time.strftime("%I:%M %p") if h.scheduled_time else "",
            "status": h.status,
            "notes": h.notes
        })

    # Notifications
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == patient_id)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )
    notif_list = [{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "created_at": n.created_at.isoformat() if n.created_at else "",
        "is_read": n.is_read
    } for n in notifications]

    return {
        "patient_profile": {
            "id": patient.id,
            "full_name": patient.full_name,
            "email": patient.email,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "weight": patient.weight,
            "height": patient.height,
            "medical_conditions": patient.medical_conditions,
            "allergies": patient.allergies,
            "emergency_contact": patient.emergency_contact,
            "primary_doctor": patient.primary_doctor,
            "hospital": patient.hospital
        },
        "medication_health": summary,
        "active_medicines": summary["predictions"],
        "today_reminders": reminder_list,
        "medication_history": hist_list,
        "notifications": notif_list
    }


def link_patient_by_email(db: Session, caregiver_user: User, patient_email: str) -> Dict[str, Any]:
    patient = db.query(User).filter(User.email.ilike(patient_email.strip())).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with email '{patient_email}' not found.")

    if (patient.role or "").lower() != "patient":
        raise HTTPException(status_code=400, detail="Target user account is not a patient.")

    if patient.id == caregiver_user.id:
        raise HTTPException(status_code=400, detail="You cannot add yourself as a patient.")

    # Rule: Check if patient already has an active caregiver
    existing_active = db.query(CaregiverPatient).filter(
        CaregiverPatient.patient_id == patient.id,
        CaregiverPatient.status == "active"
    ).first()
    if existing_active:
        raise HTTPException(status_code=400, detail="This patient already has an active caregiver.")

    # Rule: Check if a request already exists between this caregiver and patient
    existing = db.query(CaregiverPatient).filter(
        CaregiverPatient.caregiver_id == caregiver_user.id,
        CaregiverPatient.patient_id == patient.id
    ).first()

    if existing:
        if existing.status == "active":
            raise HTTPException(status_code=400, detail=f"Patient '{patient.full_name}' is already assigned to you.")
        elif existing.status == "pending":
            raise HTTPException(status_code=400, detail="A caregiver request is already pending.")
        elif existing.status == "rejected":
            existing.status = "pending"
            db.commit()
            return {"message": f"Caregiver request sent to '{patient.full_name}'! Waiting for patient approval.", "patient_id": patient.id, "status": "pending"}

    link = CaregiverPatient(
        caregiver_id=caregiver_user.id,
        patient_id=patient.id,
        status="pending"
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return {"message": f"Caregiver request sent to '{patient.full_name}'! Waiting for patient approval.", "patient_id": patient.id, "status": "pending"}


def get_pending_requests_for_patient(db: Session, patient_user: User) -> List[Dict[str, Any]]:
    pending_links = db.query(CaregiverPatient).filter(
        CaregiverPatient.patient_id == patient_user.id,
        CaregiverPatient.status == "pending"
    ).all()

    result = []
    for link in pending_links:
        cg = link.caregiver or db.query(User).filter(User.id == link.caregiver_id).first()
        result.append({
            "id": link.id,
            "caregiver_id": link.caregiver_id,
            "caregiver_name": cg.full_name if cg else "Caregiver",
            "caregiver_email": cg.email if cg else "",
            "status": link.status,
            "created_at": link.created_at.isoformat() if link.created_at else ""
        })
    return result


def get_active_caregiver_for_patient(db: Session, patient_user: User) -> Any:
    active_link = db.query(CaregiverPatient).filter(
        CaregiverPatient.patient_id == patient_user.id,
        CaregiverPatient.status == "active"
    ).first()

    if not active_link:
        return None

    cg = active_link.caregiver or db.query(User).filter(User.id == active_link.caregiver_id).first()
    if not cg:
        return None

    return {
        "id": active_link.id,
        "caregiver_id": cg.id,
        "caregiver_name": cg.full_name,
        "caregiver_email": cg.email,
        "status": "active"
    }


def accept_caregiver_request(db: Session, patient_user: User, request_id: int) -> Dict[str, Any]:
    link = db.query(CaregiverPatient).filter(CaregiverPatient.id == request_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Caregiver request not found.")

    if link.patient_id != patient_user.id:
        raise HTTPException(status_code=403, detail="Access denied. This request does not belong to you.")

    if link.status != "pending":
        raise HTTPException(status_code=400, detail="This caregiver request has already been processed.")

    # Rule: Check if patient already has an active caregiver
    existing_active = db.query(CaregiverPatient).filter(
        CaregiverPatient.patient_id == patient_user.id,
        CaregiverPatient.status == "active"
    ).first()
    if existing_active:
        raise HTTPException(status_code=400, detail="You already have an active caregiver.")

    link.status = "active"
    db.commit()

    return {"message": "Caregiver request accepted! Connection is now active."}


def reject_caregiver_request(db: Session, patient_user: User, request_id: int) -> Dict[str, Any]:
    link = db.query(CaregiverPatient).filter(CaregiverPatient.id == request_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Caregiver request not found.")

    if link.patient_id != patient_user.id:
        raise HTTPException(status_code=403, detail="Access denied. This request does not belong to you.")

    if link.status != "pending":
        raise HTTPException(status_code=400, detail="This caregiver request has already been processed.")

    link.status = "rejected"
    db.commit()

    return {"message": "Caregiver request rejected."}
