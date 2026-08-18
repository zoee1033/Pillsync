from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user, require_caregiver, verify_caregiver_patient_access
from app.services.caregiver_service import (
    get_caregiver_dashboard_data,
    get_assigned_patients,
    _compute_patient_summary,
    get_patient_detail_for_caregiver,
    link_patient_by_email,
    get_pending_requests_for_patient,
    get_active_caregiver_for_patient,
    accept_caregiver_request,
    reject_caregiver_request
)
from app.models.medicine import Medicine
from app.models.treatment import Treatment
from app.models.reminder import Reminder
from app.models.history import History
from app.models.notification import Notification
from app.services.medicine_service import get_refill_predictions


router = APIRouter(
    prefix="/caregiver",
    tags=["Caregiver Workspace"]
)


class LinkPatientRequest(BaseModel):
    patient_email: str


@router.get("/dashboard")
def caregiver_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    return get_caregiver_dashboard_data(db, current_user)


@router.get("/patients")
def caregiver_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    patients = get_assigned_patients(db, current_user)
    return [_compute_patient_summary(db, p) for p in patients]


@router.get("/patients/{patient_id}")
def caregiver_patient_detail(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    return get_patient_detail_for_caregiver(db, current_user, patient_id)


@router.post("/link-patient")
def caregiver_link_patient(
    payload: LinkPatientRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    return link_patient_by_email(db, current_user, payload.patient_email)


@router.get("/patient-requests")
def patient_caregiver_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_pending_requests_for_patient(db, current_user)


@router.get("/my-caregiver")
def patient_active_caregiver(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_active_caregiver_for_patient(db, current_user)


@router.post("/requests/{request_id}/accept")
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return accept_caregiver_request(db, current_user, request_id)


@router.post("/requests/{request_id}/reject")
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return reject_caregiver_request(db, current_user, request_id)


@router.get("/medicines")
def caregiver_medicines(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    patients = get_assigned_patients(db, current_user)
    result = []
    for p in patients:
        preds = get_refill_predictions(db, p)
        for pred in preds:
            pred["patient_id"] = p.id
            pred["patient_name"] = p.full_name
            result.append(pred)
    return result


@router.get("/reminders")
def caregiver_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    patients = get_assigned_patients(db, current_user)
    p_ids = [p.id for p in patients]
    if not p_ids:
        return []

    rems = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Medicine.treatment)
        .filter(Treatment.user_id.in_(p_ids), Medicine.is_active == True)
        .order_by(Reminder.reminder_time.asc())
        .all()
    )

    out = []
    for r in rems:
        rem_time = r.reminder_time.strftime("%I:%M %p") if hasattr(r.reminder_time, 'strftime') else str(r.reminder_time)
        owner = r.medicine.treatment.user if r.medicine and r.medicine.treatment else None
        out.append({
            "id": r.id,
            "patient_id": owner.id if owner else None,
            "patient_name": owner.full_name if owner else "Patient",
            "medicine_id": r.medicine_id,
            "medicine_name": r.medicine.medicine_name if r.medicine else "Medicine",
            "reminder_time": rem_time,
            "repeat_type": r.repeat_type,
            "status": r.status
        })
    return out


@router.get("/history")
def caregiver_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    patients = get_assigned_patients(db, current_user)
    p_ids = [p.id for p in patients]
    if not p_ids:
        return []

    hist_records = (
        db.query(History)
        .filter(History.user_id.in_(p_ids))
        .order_by(History.scheduled_time.desc())
        .limit(50)
        .all()
    )

    p_map = {p.id: p.full_name for p in patients}
    m_ids = [h.medicine_id for h in hist_records if h.medicine_id]
    meds = db.query(Medicine).filter(Medicine.id.in_(m_ids)).all() if m_ids else []
    m_map = {m.id: m.medicine_name for m in meds}

    out = []
    for h in hist_records:
        out.append({
            "id": h.id,
            "patient_id": h.user_id,
            "patient_name": p_map.get(h.user_id, f"Patient #{h.user_id}"),
            "medicine_name": m_map.get(h.medicine_id, "Medication"),
            "date": h.scheduled_time.strftime("%Y-%m-%d") if h.scheduled_time else "",
            "time": h.scheduled_time.strftime("%I:%M %p") if h.scheduled_time else "",
            "status": h.status,
            "notes": h.notes
        })
    return out


@router.get("/notifications")
def caregiver_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_caregiver)
):
    patients = get_assigned_patients(db, current_user)
    p_ids = [p.id for p in patients]
    if not p_ids:
        return []

    notifs = (
        db.query(Notification)
        .filter(Notification.user_id.in_(p_ids))
        .order_by(Notification.created_at.desc())
        .limit(30)
        .all()
    )
    p_map = {p.id: p.full_name for p in patients}

    return [{
        "id": n.id,
        "patient_name": p_map.get(n.user_id, f"Patient #{n.user_id}"),
        "title": n.title,
        "message": n.message,
        "created_at": n.created_at.isoformat() if n.created_at else "",
        "is_read": n.is_read
    } for n in notifs]
