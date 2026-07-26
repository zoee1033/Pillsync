import sys
from pathlib import Path
from datetime import datetime, time, date, timedelta
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.enums import HistoryStatus
from app.schemas.history_schema import HistoryCreate, HistoryResponse
from app.services.history_service import create_history, get_history, is_duplicate_history
from app.services.reminder_service import snooze_reminder
from app.scheduler.jobs import check_expired_treatments


class FakeQuery:
    def __init__(self, data):
        self.data = list(data)

    def join(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def filter(self, *criterion):
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
                    op_name = getattr(op, '__name__', str(op))
                    if op_name == 'ne':
                        if val == target:
                            keep = False
                    elif op_name == 'lt':
                        if not (val < target):
                            keep = False
                    elif val != target:
                        keep = False
            if keep:
                filtered.append(item)
        return FakeQuery(filtered)

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
                m_name = self.medicines.get(h.medicine_id).medicine_name if h.medicine_id in self.medicines else None
                m_dosage = self.medicines.get(h.medicine_id).dosage if h.medicine_id in self.medicines else None
                t = self.treatments.get(h.treatment_id)
                t_name = t.disease_name if t else "Treatment A"
                s_date = t.start_date if t else None
                e_date = t.end_date if t else None
                t_status = t.status if t else "Active"
                r_time = str(self.reminders.get(h.reminder_id).reminder_time) if h.reminder_id in self.reminders else None
                tuples.append((h, m_name, m_dosage, t_name, s_date, e_date, t_status, r_time))
            return FakeQuery(tuples)
        return FakeQuery([])

    def add(self, obj):
        self.added.append(obj)
        if hasattr(obj, 'id') and getattr(obj, 'id') is None:
            obj.id = len(self.added)
        if 'History' in type(obj).__name__:
            self.histories.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass


def test_user_action_history_creation():
    db = FakeSession()
    user = SimpleNamespace(id=6)

    treatment = SimpleNamespace(id=1, user_id=6, disease_name="Asthma", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), status="Active")
    medicine = SimpleNamespace(id=10, treatment_id=1, medicine_name="Inhaler", dosage="2 puffs", quantity=10, is_active=True)
    reminder = SimpleNamespace(id=100, medicine_id=10, reminder_time=time(8, 0), repeat_type="Daily", snooze_minutes=15, next_trigger_at=datetime.utcnow())

    db.treatments[1] = treatment
    db.medicines[10] = medicine
    db.reminders[100] = reminder

    payload = HistoryCreate(
        treatment_id=1,
        medicine_id=10,
        reminder_id=100,
        scheduled_time=datetime.utcnow(),
        status=HistoryStatus.TAKEN.value,
        notes="Taken morning dose"
    )

    history = create_history(db=db, history=payload, current_user=user)
    assert history.user_id == 6
    assert history.treatment_id == 1
    assert history.medicine_id == 10
    assert history.reminder_id == 100
    assert history.status == HistoryStatus.TAKEN.value
    assert history.medicine_name == "Inhaler"
    assert history.dosage == "2 puffs"
    print("✓ User action history creation passed.")


def test_treatment_lifecycle_history_without_medicine_id():
    db = FakeSession()
    user = SimpleNamespace(id=6)

    treatment = SimpleNamespace(id=2, user_id=6, disease_name="Flu", start_date=date(2026, 1, 1), end_date=date(2026, 1, 10), status="Completed")
    db.treatments[2] = treatment

    payload = HistoryCreate(
        treatment_id=2,
        medicine_id=None,
        reminder_id=None,
        scheduled_time=datetime.utcnow(),
        status=HistoryStatus.COMPLETED.value,
        notes="Treatment completed successfully"
    )

    history = create_history(db=db, history=payload, current_user=user)
    assert history.user_id == 6
    assert history.treatment_id == 2
    assert history.medicine_id is None
    assert history.reminder_id is None
    assert history.status == HistoryStatus.COMPLETED.value
    print("✓ Treatment lifecycle history (optional medicine_id) passed.")


def test_instant_snooze_uses_configured_minutes():
    db = FakeSession()
    user = SimpleNamespace(id=6)

    treatment = SimpleNamespace(id=1, user_id=6, disease_name="Diabetes", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), status="Active")
    medicine = SimpleNamespace(id=10, treatment_id=1, treatment=treatment, medicine_name="Metformin", dosage="500mg", quantity=30, is_active=True)
    reminder = SimpleNamespace(id=100, medicine_id=10, medicine=medicine, reminder_time="09:00:00", snooze_minutes=15, next_trigger_at=datetime.utcnow())

    db.treatments[1] = treatment
    db.medicines[10] = medicine
    db.reminders[100] = reminder

    before_snooze = datetime.utcnow()
    updated_reminder = snooze_reminder(reminder_id=100, minutes=reminder.snooze_minutes, db=db, current_user=user)

    assert len(db.histories) == 1
    snoozed_hist = db.histories[0]
    assert snoozed_hist.status == HistoryStatus.SNOOZED.value
    assert snoozed_hist.medicine_id == 10
    assert snoozed_hist.reminder_id == 100
    assert "15 minutes" in snoozed_hist.notes
    print("✓ Instant snooze uses configured duration (15m) without popup passed.")


def test_background_treatment_expiry_check():
    db = FakeSession()

    expired_treatment = SimpleNamespace(
        id=3,
        user_id=6,
        disease_name="Old Infection",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 1),
        status="Active"
    )
    db.treatments[3] = expired_treatment

    check_expired_treatments(db)

    assert expired_treatment.status == HistoryStatus.EXPIRED.value
    assert len(db.histories) == 1
    exp_hist = db.histories[0]
    assert exp_hist.status == HistoryStatus.EXPIRED.value
    assert exp_hist.treatment_id == 3
    print("✓ Background treatment expiry check passed.")


if __name__ == "__main__":
    test_user_action_history_creation()
    test_treatment_lifecycle_history_without_medicine_id()
    test_instant_snooze_uses_configured_minutes()
    test_background_treatment_expiry_check()
    print("\n🎉 ALL ENHANCED HISTORY & NOTIFICATION TESTS PASSED CLEANLY!")
