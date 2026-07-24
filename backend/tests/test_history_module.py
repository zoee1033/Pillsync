import sys
from pathlib import Path
from datetime import datetime, timedelta
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.history_schema import HistoryCreate, HistoryResponse
from app.services.history_service import create_history, get_history
from app.services.reminder_service import snooze_reminder
from app.services.device_token_service import register_device_token
from app.schemas.device_token_schema import DeviceTokenCreate


class FakeQuery:
    def __init__(self, data):
        self.data = list(data)

    def join(self, *args, **kwargs):
        return self

    def filter(self, *criterion):
        # Dummy evaluator for test_history_module assertions
        filtered = []
        for item in self.data:
            keep = True
            for c in criterion:
                left = getattr(c, 'left', None)
                right = getattr(c, 'right', None)
                op = getattr(c, 'operator', None)
                if left is not None and right is not None:
                    field_name = getattr(left, 'name', str(left).split('.')[-1])
                    val = getattr(item, field_name, None)
                    target = getattr(right, 'value', right)
                    if hasattr(op, '__name__') and op.__name__ == 'ne':
                        if val == target:
                            keep = False
                    elif val != target:
                        keep = False
            if keep:
                filtered.append(item)
        return FakeQuery(filtered)

    def outerjoin(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.data[0] if self.data else None

    def all(self):
        return self.data


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.treatments = {}
        self.medicines = {}
        self.reminders = {}
        self.histories = []
        self.tokens = []

    def query(self, model):
        name = getattr(model, '__name__', str(model))
        if 'Treatment' in name:
            return FakeQuery(list(self.treatments.values()))
        elif 'Medicine' in name:
            return FakeQuery(list(self.medicines.values()))
        elif 'Reminder' in name:
            return FakeQuery(list(self.reminders.values()))
        elif 'History' in name:
            tuples = []
            for h in self.histories:
                m_name = self.medicines.get(h.medicine_id).medicine_name if h.medicine_id in self.medicines else "MedA"
                t_name = self.treatments.get(h.treatment_id).disease_name if h.treatment_id in self.treatments else "TreatA"
                r_time = str(self.reminders.get(h.reminder_id).reminder_time) if h.reminder_id in self.reminders else "08:00:00"
                tuples.append((h, m_name, t_name, r_time))
            return FakeQuery(tuples)
        elif 'DeviceToken' in name:
            return FakeQuery(self.tokens)
        return FakeQuery([])

    def add(self, obj):
        self.added.append(obj)
        if hasattr(obj, 'id') and getattr(obj, 'id') is None:
            obj.id = len(self.added)
        if 'History' in type(obj).__name__:
            self.histories.append(obj)
        if 'DeviceToken' in type(obj).__name__:
            self.tokens.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass


def test_history_creation_and_ownership():
    db = FakeSession()
    user = SimpleNamespace(id=6)
    
    treatment = SimpleNamespace(id=1, user_id=6, disease_name="Diabetes")
    medicine = SimpleNamespace(id=10, treatment_id=1, medicine_name="Metformin")
    reminder = SimpleNamespace(id=100, medicine_id=10, reminder_time="09:00:00", next_trigger_at=datetime.utcnow())
    
    db.treatments[1] = treatment
    db.medicines[10] = medicine
    db.reminders[100] = reminder

    payload = HistoryCreate(
        treatment_id=1,
        medicine_id=10,
        reminder_id=100,
        scheduled_time=datetime.utcnow(),
        status="Taken"
    )

    history = create_history(db=db, history=payload, current_user=user)
    assert history.user_id == 6
    assert history.treatment_id == 1
    assert history.medicine_id == 10
    assert history.reminder_id == 100
    assert history.status == "Taken"
    assert history.medicine_name == "Metformin"
    assert history.treatment_name == "Diabetes"
    print("✓ History creation & ownership test passed.")


def test_snooze_creates_history():
    db = FakeSession()
    user = SimpleNamespace(id=6)
    
    treatment = SimpleNamespace(id=1, user_id=6, disease_name="Hypertension")
    medicine = SimpleNamespace(id=10, treatment_id=1, treatment=treatment, medicine_name="Amlodipine")
    reminder = SimpleNamespace(id=100, medicine_id=10, medicine=medicine, reminder_time="08:00:00", next_trigger_at=datetime.utcnow())
    
    db.treatments[1] = treatment
    db.medicines[10] = medicine
    db.reminders[100] = reminder

    updated_reminder = snooze_reminder(reminder_id=100, minutes=10, db=db, current_user=user)
    assert len(db.histories) == 1
    snoozed_hist = db.histories[0]
    assert snoozed_hist.user_id == 6
    assert snoozed_hist.status == "Snoozed"
    print("✓ Snooze creates history test passed.")


def test_device_token_replacement():
    db = FakeSession()
    user = SimpleNamespace(id=6)

    tok1 = SimpleNamespace(id=1, user_id=6, fcm_token="fcm_token_sample_string_old1", browser="Chrome", is_active=True)
    db.tokens.append(tok1)

    new_tok_data = DeviceTokenCreate(
        fcm_token="fcm_token_sample_string_new2",
        device_name="Browser",
        browser="Chrome",
        platform="Win32"
    )

    registered = register_device_token(db=db, token_data=new_tok_data, current_user=user)
    assert tok1.is_active is False
    assert registered.fcm_token == "fcm_token_sample_string_new2"
    assert registered.is_active is True
    print("✓ Device token replacement for same browser test passed.")


if __name__ == "__main__":
    test_history_creation_and_ownership()
    test_snooze_creates_history()
    test_device_token_replacement()
    print("ALL TESTS PASSED CLEANLY!")
