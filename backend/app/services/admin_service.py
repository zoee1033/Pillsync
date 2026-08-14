from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.caregiver_patient import CaregiverPatient
from app.models.treatment import Treatment
from app.models.medicine import Medicine
from app.models.reminder import Reminder
from app.models.history import History
from app.models.notification import Notification
from app.services.medicine_service import get_refill_predictions


def get_admin_dashboard_data(db: Session) -> Dict[str, Any]:
    total_users = db.query(User).count()
    patients_count = db.query(User).filter(User.role.ilike("patient")).count()
    caregivers_count = db.query(User).filter(User.role.ilike("caregiver")).count()
    admins_count = db.query(User).filter(User.role.ilike("admin")).count()

    active_medicines = db.query(Medicine).filter(Medicine.is_active == True).count()
    active_treatments = db.query(Treatment).filter(Treatment.status.ilike("active")).count()
    active_reminders = db.query(Reminder).filter(Reminder.status == "Active").count()

    # Medication Health System-Wide using standard get_refill_predictions
    all_patients = db.query(User).filter(User.role.ilike("patient")).all()
    healthy_cnt = 0
    needs_refill_cnt = 0
    critical_cnt = 0
    critical_alerts = []

    for p in all_patients:
        preds = get_refill_predictions(db, p)
        for pred in preds:
            cat = pred.get("status_category", "Healthy")
            if cat == "Healthy":
                healthy_cnt += 1
            elif cat in ["Needs Refill", "Refill Soon", "Urgent"]:
                needs_refill_cnt += 1
            elif cat == "Critical":
                critical_cnt += 1
                critical_alerts.append({
                    "patient_name": p.full_name,
                    "medicine_name": pred.get("medicine_name"),
                    "days_remaining": pred.get("remaining_days"),
                    "status": "Critical"
                })

    # Recent System Activity from real history table
    recent_history = (
        db.query(History)
        .order_by(History.scheduled_time.desc())
        .limit(10)
        .all()
    )
    u_ids = [h.user_id for h in recent_history]
    u_map = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(u_ids)).all()} if u_ids else {}
    m_ids = [h.medicine_id for h in recent_history if h.medicine_id]
    m_map = {m.id: m.medicine_name for m in db.query(Medicine).filter(Medicine.id.in_(m_ids)).all()} if m_ids else {}

    activity_feed = []
    for h in recent_history:
        activity_feed.append({
            "id": h.id,
            "timestamp": h.scheduled_time.strftime("%d %b %H:%M") if h.scheduled_time else "",
            "user_name": u_map.get(h.user_id, f"User #{h.user_id}"),
            "action": f"Dose {h.status}",
            "target": m_map.get(h.medicine_id, "Medication"),
            "status": h.status
        })

    return {
        "total_users": total_users,
        "patients_count": patients_count,
        "caregivers_count": caregivers_count,
        "admins_count": admins_count,
        "active_medicines": active_medicines,
        "active_treatments": active_treatments,
        "active_reminders": active_reminders,
        "medication_health": {
            "healthy": healthy_cnt,
            "needs_refill": needs_refill_cnt,
            "critical": critical_cnt
        },
        "critical_alerts": critical_alerts[:5],
        "activity_feed": activity_feed
    }


def get_admin_users_list(db: Session, role_filter: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    query = db.query(User)
    if role_filter and role_filter != "all":
        query = query.filter(User.role.ilike(role_filter))

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(s)) | (User.email.ilike(s)))

    users = query.order_by(User.created_at.desc()).all()
    return [{
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "phone": u.phone,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else ""
    } for u in users]


def update_user_status_role(db: Session, user_id: int, role: Optional[str] = None, is_active: Optional[bool] = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if role:
        user.role = role.lower()
    if is_active is not None:
        user.is_active = is_active

    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully.", "user_id": user.id, "role": user.role, "is_active": user.is_active}


def get_admin_patients_list(db: Session) -> List[Dict[str, Any]]:
    patients = db.query(User).filter(User.role.ilike("patient")).all()
    links = db.query(CaregiverPatient).all()
    cg_map = {}
    for l in links:
        cg_map[l.patient_id] = l.caregiver.full_name if l.caregiver else f"Caregiver #{l.caregiver_id}"

    out = []
    for p in patients:
        preds = get_refill_predictions(db, p)
        statuses = [pr.get("status_category", "Healthy") for pr in preds]
        med_status = "Critical" if "Critical" in statuses else "Needs Refill" if ("Needs Refill" in statuses or "Refill Soon" in statuses) else "Healthy"
        t_count = db.query(Treatment).filter(Treatment.user_id == p.id, Treatment.status.ilike("active")).count()

        out.append({
            "id": p.id,
            "full_name": p.full_name,
            "email": p.email,
            "phone": p.phone,
            "assigned_caregiver": cg_map.get(p.id, "Unassigned"),
            "active_medicines": len(preds),
            "active_treatments": t_count,
            "medication_status": med_status,
            "is_active": p.is_active
        })
    return out


def get_admin_caregivers_list(db: Session) -> List[Dict[str, Any]]:
    caregivers = db.query(User).filter(User.role.ilike("caregiver")).all()
    links = db.query(CaregiverPatient).all()
    assigned_map = {}
    for l in links:
        if l.caregiver_id not in assigned_map:
            assigned_map[l.caregiver_id] = []
        assigned_map[l.caregiver_id].append({
            "id": l.patient_id,
            "full_name": l.patient.full_name if l.patient else f"Patient #{l.patient_id}"
        })

    return [{
        "id": c.id,
        "full_name": c.full_name,
        "email": c.email,
        "phone": c.phone,
        "assigned_patients": assigned_map.get(c.id, []),
        "assigned_count": len(assigned_map.get(c.id, [])),
        "is_active": c.is_active
    } for c in caregivers]


def assign_caregiver(db: Session, caregiver_id: int, patient_id: int):
    cg = db.query(User).filter(User.id == caregiver_id, User.role.ilike("caregiver")).first()
    if not cg:
        raise HTTPException(status_code=404, detail="Caregiver user not found.")

    p = db.query(User).filter(User.id == patient_id, User.role.ilike("patient")).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient user not found.")

    existing = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == caregiver_id, CaregiverPatient.patient_id == patient_id).first()
    if existing:
        return {"message": "Assignment already exists."}

    link = CaregiverPatient(caregiver_id=caregiver_id, patient_id=patient_id, status="active")
    db.add(link)
    db.commit()
    return {"message": f"Successfully assigned patient '{p.full_name}' to caregiver '{cg.full_name}'."}
