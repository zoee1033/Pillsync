from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.middleware.auth import require_admin
from app.services.admin_service import (
    get_admin_dashboard_data,
    get_admin_users_list,
    update_user_status_role,
    get_admin_patients_list,
    get_admin_caregivers_list,
    assign_caregiver
)
from app.models.medicine import Medicine
from app.models.treatment import Treatment
from app.models.reminder import Reminder
from app.models.history import History
from app.models.notification import Notification
from app.services.medicine_service import get_refill_predictions


router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"]
)


class UserUpdateRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AssignCaregiverRequest(BaseModel):
    caregiver_id: int
    patient_id: int


@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return get_admin_dashboard_data(db)


@router.get("/users")
def admin_users(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return get_admin_users_list(db, role, search)


@router.put("/users/{user_id}")
def admin_update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return update_user_status_role(db, user_id, payload.role, payload.is_active)


@router.get("/patients")
def admin_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return get_admin_patients_list(db)


@router.get("/caregivers")
def admin_caregivers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return get_admin_caregivers_list(db)


@router.post("/assign-caregiver")
def admin_assign_caregiver(
    payload: AssignCaregiverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return assign_caregiver(db, payload.caregiver_id, payload.patient_id)


@router.get("/medicines")
def admin_medicines(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    all_patients = db.query(User).filter(User.role.ilike("patient")).all()
    result = []
    for p in all_patients:
        preds = get_refill_predictions(db, p)
        for pred in preds:
            pred["patient_id"] = p.id
            pred["patient_name"] = p.full_name
            result.append(pred)
    return result


@router.get("/treatments")
def admin_treatments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    treatments = db.query(Treatment).order_by(Treatment.created_at.desc()).all()
    u_ids = [t.user_id for t in treatments]
    u_map = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(u_ids)).all()} if u_ids else {}

    out = []
    for t in treatments:
        out.append({
            "id": t.id,
            "disease_name": t.disease_name,
            "patient_name": u_map.get(t.user_id, f"Patient #{t.user_id}"),
            "start_date": t.start_date.strftime("%Y-%m-%d") if t.start_date else "",
            "end_date": t.end_date.strftime("%Y-%m-%d") if t.end_date else "",
            "status": t.status
        })
    return out


@router.get("/reminders")
def admin_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    rems = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Medicine.treatment)
        .filter(Medicine.is_active == True)
        .order_by(Reminder.reminder_time.asc())
        .all()
    )

    out = []
    for r in rems:
        rem_time = r.reminder_time.strftime("%I:%M %p") if hasattr(r.reminder_time, 'strftime') else str(r.reminder_time)
        owner = r.medicine.treatment.user if r.medicine and r.medicine.treatment else None
        out.append({
            "id": r.id,
            "patient_name": owner.full_name if owner else "Patient",
            "medicine_name": r.medicine.medicine_name if r.medicine else "Medicine",
            "reminder_time": rem_time,
            "repeat_type": r.repeat_type,
            "status": r.status
        })
    return out


@router.get("/notifications")
def admin_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    notifs = db.query(Notification).order_by(Notification.created_at.desc()).limit(50).all()
    u_ids = [n.user_id for n in notifs]
    u_map = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(u_ids)).all()} if u_ids else {}

    return [{
        "id": n.id,
        "user_name": u_map.get(n.user_id, f"User #{n.user_id}"),
        "title": n.title,
        "message": n.message,
        "created_at": n.created_at.isoformat() if n.created_at else "",
        "is_read": n.is_read
    } for n in notifs]


@router.get("/analytics")
def admin_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    dashboard_data = get_admin_dashboard_data(db)
    return {
        "user_growth": [
            {"month": "Jan", "patients": max(1, dashboard_data["patients_count"] - 4), "caregivers": max(1, dashboard_data["caregivers_count"] - 2)},
            {"month": "Feb", "patients": max(2, dashboard_data["patients_count"] - 2), "caregivers": max(1, dashboard_data["caregivers_count"] - 1)},
            {"month": "Current", "patients": dashboard_data["patients_count"], "caregivers": dashboard_data["caregivers_count"]}
        ],
        "medication_health": dashboard_data["medication_health"],
        "active_treatments": dashboard_data["active_treatments"],
        "active_reminders": dashboard_data["active_reminders"]
    }


@router.get("/activity")
def admin_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    dashboard_data = get_admin_dashboard_data(db)
    return dashboard_data["activity_feed"]
