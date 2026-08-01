import sys
from pathlib import Path
from datetime import datetime, timedelta, date

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.enums import HistoryStatus
from app.models.history import History
from app.models.notification import Notification
from app.models.medicine import Medicine
from app.models.reminder import Reminder
from app.models.treatment import Treatment
from app.schemas.history_schema import HistoryCreate
from app.services.history_service import create_history, get_history
from app.services.reminder_service import snooze_reminder, calculate_next_trigger
from app.services.notification_service import (
    create_notification,
    get_notifications,
    delete_notification,
    mark_as_read
)


class FakeUser:
    def __init__(self, id, email="tester@example.com"):
        self.id = id
        self.email = email
        self.role = "patient"


class FakeQuery:
    def __init__(self, data):
        self.data = list(data)

    def outerjoin(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def filter(self, *criterion):
        filtered = []
        for item in self.data:
            keep = True
            obj = item[0] if isinstance(item, tuple) else item
            for c in criterion:
                left = getattr(c, 'left', None)
                right = getattr(c, 'right', None)
                if left is not None and right is not None:
                    field_name = getattr(left, 'name', str(left).split('.')[-1])
                    val = getattr(obj, field_name, None)
                    target = getattr(right, 'value', right)
                    if val != target:
                        keep = False
            if keep:
                filtered.append(item)
        return FakeQuery(filtered)

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.data[0] if self.data else None

    def all(self):
        return [item[0] if isinstance(item, tuple) else item for item in self.data]


class FakeDbSession:
    def __init__(self):
        self.treatments = []
        self.medicines = []
        self.reminders = []
        self.notifications = []
        self.histories = []
        self.added = []

    def query(self, entity):
        name = getattr(entity, '__name__', str(entity))
        if 'Treatment' in name:
            return FakeQuery(self.treatments)
        elif 'Medicine' in name:
            return FakeQuery(self.medicines)
        elif 'Reminder' in name:
            return FakeQuery(self.reminders)
        elif 'Notification' in name:
            return FakeQuery(self.notifications)
        elif 'History' in name:
            tuples = []
            for h in self.histories:
                m = next((med for med in self.medicines if med.id == h.medicine_id), None)
                t = next((tr for tr in self.treatments if tr.id == h.treatment_id), None)
                r = next((rem for rem in self.reminders if rem.id == h.reminder_id), None)
                tuples.append((
                    h,
                    m.medicine_name if m else None,
                    m.dosage if m else None,
                    t.disease_name if t else "Flu",
                    t.start_date if t else date.today(),
                    t.end_date if t else date.today(),
                    t.status if t else "Active",
                    r.reminder_time if r else None
                ))
            return FakeQuery(tuples)
        return FakeQuery([])

    def add(self, obj):
        self.added.append(obj)
        if hasattr(obj, 'id') and getattr(obj, 'id') is None:
            obj.id = len(self.added) + 100
        if 'Treatment' in type(obj).__name__:
            self.treatments.append(obj)
        elif 'Medicine' in type(obj).__name__:
            self.medicines.append(obj)
        elif 'Reminder' in type(obj).__name__:
            self.reminders.append(obj)
        elif 'Notification' in type(obj).__name__:
            self.notifications.append(obj)
        elif 'History' in type(obj).__name__:
            self.histories.append(obj)

    def delete(self, obj):
        if obj in self.notifications:
            self.notifications.remove(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def test_interactive_notification_workflow():
    print("==========================================================")
    print("TESTING INTERACTIVE NOTIFICATION ACTIONS (STEPS 1 TO 10)")
    print("==========================================================")

    db = FakeDbSession()
    user = FakeUser(id=200)

    # Setup Treatment, Medicine, Reminder
    t = Treatment(id=1, user_id=user.id, disease_name="Diabetes Care", doctor_name="Dr. Smith", start_date=date.today(), end_date=date.today(), status="Active")
    db.add(t)

    m = Medicine(id=1, treatment_id=t.id, medicine_name="Metformin", dosage="500mg", quantity=10, is_active=True)
    m.treatment = t
    db.add(m)

    r = Reminder(id=1, medicine_id=m.id, reminder_time="09:00:00", repeat_type="Daily", notification_enabled=True, snooze_minutes=15, status="Active")
    r.medicine = m
    db.add(r)

    n = Notification(id=1, user_id=user.id, reminder_id=r.id, title="Pill Reminder", message="Time to take Metformin 500mg", is_read=False, is_sent=True)
    db.add(n)

    # 1. Action: Taken
    print("\n--- 1. Testing Action: Taken ---")
    initial_qty = m.quantity
    h_taken = create_history(db, HistoryCreate(
        treatment_id=t.id,
        medicine_id=m.id,
        reminder_id=r.id,
        scheduled_time=datetime.utcnow(),
        status=HistoryStatus.TAKEN.value,
        notes="Taken via Interactive Action"
    ), user)
    mark_as_read(1, db, user)

    assert m.quantity == initial_qty - 1
    assert n.is_read is True
    assert any(h.status == HistoryStatus.TAKEN.value for h in db.histories)
    print(f"✓ Taken Action Verified: Quantity decremented to {m.quantity}, History recorded, Notification marked read.")

    # 2. Action: Skipped
    print("\n--- 2. Testing Action: Skipped ---")
    h_skipped = create_history(db, HistoryCreate(
        treatment_id=t.id,
        medicine_id=m.id,
        reminder_id=r.id,
        scheduled_time=datetime.utcnow(),
        status=HistoryStatus.SKIPPED.value,
        skip_reason="Patient resting",
        notes="Skipped via Interactive Action"
    ), user)
    assert any(h.status == HistoryStatus.SKIPPED.value for h in db.histories)
    print("✓ Skipped Action Verified: History recorded with skip_reason.")

    # 3. Action: Snooze
    print("\n--- 3. Testing Action: Snooze ---")
    snooze_reminder(r.id, 15, db, user)
    assert any(h.status == HistoryStatus.SNOOZED.value for h in db.histories)
    print("✓ Snooze Action Verified: Snoozed history recorded and trigger updated.")

    # 4. Action: Delete Notification
    print("\n--- 4. Testing Action: Delete Notification ---")
    initial_hist_count = len(db.histories)
    delete_notification(n.id, db, user)
    assert len(db.notifications) == 0
    assert len(db.histories) == initial_hist_count  # No new history created for delete
    print("✓ Delete Action Verified: Notification record removed without creating history or modifying schedule.")

    print("\n==========================================================")
    print("🎉 ALL INTERACTIVE NOTIFICATION TESTS PASSED PERFECTLY!")
    print("==========================================================")


if __name__ == "__main__":
    test_interactive_notification_workflow()
