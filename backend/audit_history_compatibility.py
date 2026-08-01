import json
import time
import urllib.request
import urllib.parse
from app.database import SessionLocal
from app.models.history import History

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None, token=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    body = json.dumps(data).encode("utf-8") if data else None
    with urllib.request.urlopen(req, data=body) as resp:
        return json.loads(resp.read().decode("utf-8"))

def audit_pipeline():
    print("==========================================================")
    print("AUDITING STEP 1, 2, 3: REAL RUNTIME PIPELINE EXECUTION")
    print("==========================================================")

    # 1. Register & Login Audit User
    email = f"audit_user_{int(time.time())}@pillsync.com"
    make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "full_name": "Audit Test User",
        "email": email,
        "phone": "+1999888777",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "patient"
    })

    login_res = make_request(f"{BASE_URL}/auth/login", method="POST", data={"email": email, "password": "Password123!"})
    token = login_res["access_token"]
    user_id = login_res["user"]["id"]
    print(f"Registered & Logged in Audit User ID: {user_id}")

    # Treatment 1: Create -> Complete
    t1 = make_request(f"{BASE_URL}/treatments/", method="POST", data={
        "disease_name": "Asthma Care",
        "doctor_name": "Dr. House",
        "diagnosis_date": "2026-06-01",
        "start_date": "2026-06-01",
        "end_date": "2026-07-01",
        "status": "Active",
        "notes": "Use inhaler when needed"
    }, token=token)
    t1_id = t1["id"]
    print(f"Created Treatment 1 ID: {t1_id} ('Asthma Care')")

    make_request(f"{BASE_URL}/treatments/{t1_id}", method="PUT", data={"status": "Completed"}, token=token)
    print(f"Updated Treatment 1 ID: {t1_id} to 'Completed'")

    # Treatment 2: Create -> Cancel
    t2 = make_request(f"{BASE_URL}/treatments/", method="POST", data={
        "disease_name": "Migraine Treatment",
        "doctor_name": "Dr. Strange",
        "diagnosis_date": "2026-07-10",
        "start_date": "2026-07-10",
        "end_date": "2026-08-10",
        "status": "Active",
        "notes": "Avoid bright lights"
    }, token=token)
    t2_id = t2["id"]
    print(f"Created Treatment 2 ID: {t2_id} ('Migraine Treatment')")

    make_request(f"{BASE_URL}/treatments/{t2_id}", method="PUT", data={"status": "Cancelled"}, token=token)
    print(f"Updated Treatment 2 ID: {t2_id} to 'Cancelled'")

    # Add Medicine & Reminder to Treatment 1
    m1 = make_request(f"{BASE_URL}/medicines/", method="POST", data={
        "treatment_id": t1_id,
        "medicine_name": "Salbutamol Inhaler",
        "medicine_type": "Inhaler",
        "dosage": "2 puffs",
        "quantity": 10,
        "instructions": "Inhale deeply",
        "is_active": True
    }, token=token)
    m1_id = m1["id"]
    print(f"Created Medicine ID: {m1_id} ('Salbutamol Inhaler') for Treatment 1")

    r1 = make_request(f"{BASE_URL}/reminders/", method="POST", data={
        "medicine_id": m1_id,
        "reminder_time": "08:00:00",
        "repeat_type": "Daily",
        "notification_enabled": True,
        "snooze_minutes": 15,
        "status": "Active"
    }, token=token)
    r1_id = r1["id"]
    print(f"Created Reminder ID: {r1_id} for Medicine {m1_id}")

    # Create History entries for Taken, Skipped, Snoozed
    h_taken = make_request(f"{BASE_URL}/history/", method="POST", data={
        "treatment_id": t1_id,
        "medicine_id": m1_id,
        "reminder_id": r1_id,
        "scheduled_time": "2026-07-29T08:00:00Z",
        "status": "Taken",
        "notes": "Morning dose taken"
    }, token=token)
    print("Created 'Taken' History record ID:", h_taken["id"])

    h_skipped = make_request(f"{BASE_URL}/history/", method="POST", data={
        "treatment_id": t1_id,
        "medicine_id": m1_id,
        "reminder_id": r1_id,
        "scheduled_time": "2026-07-29T14:00:00Z",
        "status": "Skipped",
        "skip_reason": "Out of house",
        "notes": "Skipped afternoon dose"
    }, token=token)
    print("Created 'Skipped' History record ID:", h_skipped["id"])

    h_snoozed = make_request(f"{BASE_URL}/history/snooze?reminder_id={r1_id}" if False else f"{BASE_URL}/history/", method="POST", data={
        "treatment_id": t1_id,
        "medicine_id": m1_id,
        "reminder_id": r1_id,
        "scheduled_time": "2026-07-29T20:00:00Z",
        "status": "Snoozed",
        "notes": "Snoozed by 15 mins"
    }, token=token)
    print("Created 'Snoozed' History record ID:", h_snoozed["id"])

    # STEP 2: Query PostgreSQL directly
    print("\n==========================================================")
    print("STEP 2: POSTGRESQL DIRECT QUERY ROWS FOR USER", user_id)
    print("==========================================================")
    db = SessionLocal()
    pg_rows = db.query(History).filter(History.user_id == user_id).order_by(History.action_time.asc()).all()
    print(f"Found {len(pg_rows)} PostgreSQL history table rows:")
    for r in pg_rows:
        print(f"  -> ID: {r.id} | UserID: {r.user_id} | TreatmentID: {r.treatment_id} | MedID: {r.medicine_id} | RemID: {r.reminder_id} | Status: '{r.status}' | Notes: '{r.notes}' | ActionTime: {r.action_time}")
    db.close()

    # STEP 3: Call GET /history - Print EXACT JSON
    print("\n==========================================================")
    print("STEP 3: CALL GET /history - EXACT JSON RESPONSE")
    print("==========================================================")
    history_json = make_request(f"{BASE_URL}/history/", method="GET", token=token)
    print(json.dumps(history_json, indent=2, default=str))

if __name__ == "__main__":
    audit_pipeline()
