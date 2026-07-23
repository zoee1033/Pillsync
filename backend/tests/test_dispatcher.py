from types import SimpleNamespace

from app.models.device_token import DeviceToken
from app.scheduler import dispatcher


class FakeDB:
    def __init__(self):
        self.queries = []
        self.added = None
        self.committed = 0

    def query(self, model):
        self.queries.append(model)
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        if self.queries[-1] is DeviceToken:
            return SimpleNamespace(fcm_token="abc123")
        return SimpleNamespace(id=7)

    def add(self, obj):
        self.added = obj

    def commit(self):
        self.committed += 1

    def refresh(self, obj):
        return None


def test_dispatch_reminder_creates_and_marks_notification(monkeypatch):
    created = {}
    marked = {}

    def fake_create_notification(db, notification, current_user):
        created["notification"] = notification
        created["user"] = current_user
        return SimpleNamespace(id=42)

    def fake_mark_as_sent(notification_id, db):
        marked["notification_id"] = notification_id
        return SimpleNamespace(id=notification_id)

    def fake_send_push_notification(**kwargs):
        return "ok"

    monkeypatch.setattr(dispatcher, "create_notification", fake_create_notification)
    monkeypatch.setattr(dispatcher, "mark_as_sent", fake_mark_as_sent)
    monkeypatch.setattr(dispatcher, "send_push_notification", fake_send_push_notification)

    reminder = SimpleNamespace(
        id=11,
        medicine=SimpleNamespace(
            medicine_name="Paracetamol",
            treatment=SimpleNamespace(user_id=7),
            id=3,
        ),
    )

    fake_db = FakeDB()
    dispatcher.dispatch_reminder(fake_db, reminder)

    assert created["notification"].reminder_id == 11
    assert created["user"].id == 7
    assert marked["notification_id"] == 42
