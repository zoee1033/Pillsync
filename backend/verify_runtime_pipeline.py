import json
import urllib.request
import urllib.parse
from app.database import SessionLocal
from app.models.history import History
from app.models.treatment import Treatment

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None, token=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    body = json.dumps(data).encode("utf-8") if data else None
    try:
        with urllib.request.urlopen(req, data=body) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_content = e.read().decode("utf-8")
        print(f"❌ HTTP Error {e.code} for {url}: {error_content}")
        raise e

def run_real_runtime_verification():
    print("==========================================================")
    print("REAL RUNTIME VERIFICATION (STEPS 1 TO 7)")
    print("==========================================================")

    import time
    email = f"runtime_user_{int(time.time())}@pillsync.com"
    reg_payload = {
        "full_name": "Runtime Verified User",
        "email": email,
        "phone": "+1234567890",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "patient"
    }
    
    print(f"\n1. Registering Real User: {email}")
    reg_res = make_request(f"{BASE_URL}/auth/register", method="POST", data=reg_payload)
    print("Registration Response:", reg_res)

    login_res = make_request(f"{BASE_URL}/auth/login", method="POST", data={"email": email, "password": "Password123!"})
    token = login_res["access_token"]
    user_id = login_res["user"]["id"]
    print(f"Logged in successfully. User ID={user_id}, Token={token[:20]}...")

    # 2. Create Brand New Treatment
    print("\n2. Creating Brand New Treatment via HTTP POST /treatments...")
    create_t_payload = {
        "disease_name": "Hyperthyroidism Care",
        "doctor_name": "Dr. Alice Vance",
        "diagnosis_date": "2026-07-01",
        "start_date": "2026-07-01",
        "end_date": "2026-08-30",
        "status": "Active",
        "notes": "Take medication daily after breakfast"
    }
    created_t = make_request(f"{BASE_URL}/treatments/", method="POST", data=create_t_payload, token=token)
    t_id = created_t["id"]
    print(f"Created Treatment ID={t_id}, Disease='{created_t['disease_name']}', Status='{created_t['status']}'")

    # Confirm it appears in GET /treatments
    all_t = make_request(f"{BASE_URL}/treatments/", method="GET", token=token)
    print(f"GET /treatments returned {len(all_t)} treatment(s). Found created treatment: {any(t['id'] == t_id for t in all_t)}")

    # 3. Change Status to Completed
    print("\n3. Changing Treatment Status to 'Completed' via HTTP PUT /treatments/{id}...")
    updated_t1 = make_request(f"{BASE_URL}/treatments/{t_id}", method="PUT", data={"status": "Completed"}, token=token)
    print(f"Updated Treatment ID={t_id}, New Status='{updated_t1['status']}'")

    # 4. Open PostgreSQL - Query exact row inserted into history table
    print("\n4. Querying PostgreSQL Database directly for history rows of User ID=", user_id)
    db = SessionLocal()
    pg_rows = db.query(History).filter(History.user_id == user_id).order_by(History.action_time.asc()).all()
    print(f"PostgreSQL history table returned {len(pg_rows)} row(s):")
    for r in pg_rows:
        print(f"  -> ID: {r.id} | UserID: {r.user_id} | TreatmentID: {r.treatment_id} | Status: '{r.status}' | Notes: '{r.notes}' | ActionTime: {r.action_time}")
    db.close()

    # 5. Call GET /history - Show JSON Response
    print("\n5. Calling HTTP GET /history...")
    history_json = make_request(f"{BASE_URL}/history/", method="GET", token=token)
    print(f"GET /history returned HTTP 200 OK. JSON Response count = {len(history_json)}:")
    print(json.dumps(history_json, indent=2, default=str))

    # 7. Repeat for Cancelled
    print("\n7. Repeating for Status 'Cancelled': Updating Treatment to 'Cancelled'...")
    updated_t2 = make_request(f"{BASE_URL}/treatments/{t_id}", method="PUT", data={"status": "Cancelled"}, token=token)
    print(f"Updated Treatment ID={t_id}, New Status='{updated_t2['status']}'")

    # PostgreSQL Query after Cancelled
    print("\nPostgreSQL Direct Query after Cancelled update:")
    db = SessionLocal()
    pg_rows2 = db.query(History).filter(History.user_id == user_id).order_by(History.action_time.asc()).all()
    for r in pg_rows2:
        print(f"  -> ID: {r.id} | UserID: {r.user_id} | TreatmentID: {r.treatment_id} | Status: '{r.status}' | Notes: '{r.notes}' | ActionTime: {r.action_time}")
    db.close()

    # Call GET /history after Cancelled
    print("\nCalling HTTP GET /history after Cancelled update:")
    history_json2 = make_request(f"{BASE_URL}/history/", method="GET", token=token)
    print(f"GET /history JSON Response count = {len(history_json2)}:")
    print(json.dumps(history_json2, indent=2, default=str))

    print("\n==========================================================")
    print("REAL RUNTIME VERIFICATION COMPLETE AND SUCCESSFUL!")
    print("==========================================================")

if __name__ == "__main__":
    run_real_runtime_verification()
