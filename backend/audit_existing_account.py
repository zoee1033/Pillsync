import json
from app.database import SessionLocal
from app.models.user import User
from app.models.treatment import Treatment
from app.models.history import History
from app.services.history_service import get_history

db = SessionLocal()

print("==========================================================")
print("AUDITING PRE-EXISTING USER ACCOUNTS")
print("==========================================================")

# Target user: User ID 1 (zoya@gmail.com)
target_user = db.query(User).filter(User.id == 1).first()

if target_user:
    print(f"\nTarget Account Found: ID={target_user.id} | Email='{target_user.email}' | Name='{target_user.full_name}'")
    
    # 1. Existing Treatments
    user_treatments = db.query(Treatment).filter(Treatment.user_id == target_user.id).all()
    print(f"Treatments in PostgreSQL for User {target_user.id}: {len(user_treatments)}")
    for t in user_treatments:
        print(f"  -> Treatment ID={t.id} | Disease='{t.disease_name}' | Status='{t.status}' | Start='{t.start_date}' | End='{t.end_date}'")

    # 2. PostgreSQL Direct Query for History Table
    user_history_pg = db.query(History).filter(History.user_id == target_user.id).all()
    print(f"\nPostgreSQL History Rows for User {target_user.id}: {len(user_history_pg)}")
    for h in user_history_pg:
        print(f"  -> History ID={h.id} | TreatmentID={h.treatment_id} | Status='{h.status}' | Notes='{h.notes}'")

    # 3. GET /history Service Call Output for User
    api_history = get_history(db, target_user)
    print(f"\nGET /history API returned {len(api_history)} record(s).")
    
    # Convert response objects to dictionary for JSON output
    api_history_json = []
    for item in api_history:
        api_history_json.append({
            "id": item.id,
            "user_id": item.user_id,
            "treatment_id": item.treatment_id,
            "medicine_id": item.medicine_id,
            "reminder_id": item.reminder_id,
            "status": item.status,
            "notes": item.notes,
            "treatment_name": item.treatment_name,
            "start_date": str(item.start_date) if item.start_date else None,
            "end_date": str(item.end_date) if item.end_date else None,
            "action_time": item.action_time.isoformat() if item.action_time else None
        })
        
    print("Exact JSON Output from GET /history:")
    print(json.dumps(api_history_json, indent=2))

db.close()
