from app.database import SessionLocal
from app.models.user import User
from app.models.treatment import Treatment
from app.models.history import History
from app.schemas.treatment_schema import TreatmentUpdate
from app.services.treatment_service import update_treatment
from app.services.history_service import get_history

db = SessionLocal()

print("==========================================================")
print("TESTING STATUS UPDATE FOR EXISTING ACCOUNT (USER 1)")
print("==========================================================")

user1 = db.query(User).filter(User.id == 1).first()
t12 = db.query(Treatment).filter(Treatment.id == 12).first()

print(f"Before update: User 1 history count = {db.query(History).filter(History.user_id == 1).count()}")

# Update Treatment 12 to Completed
update_treatment(12, TreatmentUpdate(status="Completed"), db, user1)

print(f"After update to Completed: User 1 history count = {db.query(History).filter(History.user_id == 1).count()}")

history_items = get_history(db, user1)
print(f"GET /history for User 1 now returns {len(history_items)} item(s):")
for item in history_items:
    print(f"  -> ID={item.id} | Status='{item.status}' | Treatment='{item.treatment_name}' | ActionTime={item.action_time}")

db.close()
