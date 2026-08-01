from app.database import SessionLocal
from app.models.user import User
from app.models.treatment import Treatment
from app.models.history import History
from app.models.medicine import Medicine
from app.models.reminder import Reminder

db = SessionLocal()

print("==========================================================")
print("INSPECTING ALL EXISTING USERS IN POSTGRESQL DATABASE")
print("==========================================================")

users = db.query(User).all()
for u in users:
    treatments = db.query(Treatment).filter(Treatment.user_id == u.id).all()
    histories = db.query(History).filter(History.user_id == u.id).all()
    medicines = db.query(Medicine).join(Treatment, Medicine.treatment_id == Treatment.id).filter(Treatment.user_id == u.id).all()
    reminders = db.query(Reminder).join(Medicine, Reminder.medicine_id == Medicine.id).join(Treatment, Medicine.treatment_id == Treatment.id).filter(Treatment.user_id == u.id).all()
    
    print(f"\nUser ID: {u.id} | Name: '{u.full_name}' | Email: '{u.email}' | Role: '{u.role}'")
    print(f"  -> Total Treatments: {len(treatments)}")
    for t in treatments:
        print(f"      * Treatment ID={t.id}: Disease='{t.disease_name}', Status='{t.status}', Doctor='{t.doctor_name}'")
    print(f"  -> Total Medicines: {len(medicines)}")
    print(f"  -> Total Reminders: {len(reminders)}")
    print(f"  -> Total History Rows: {len(histories)}")
    for h in histories:
        print(f"      * History ID={h.id}: TreatmentID={h.treatment_id}, MedID={h.medicine_id}, RemID={h.reminder_id}, Status='{h.status}', Notes='{h.notes}'")

db.close()
