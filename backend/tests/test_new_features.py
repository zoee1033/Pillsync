import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.enums import HistoryStatus
from app.utils.medicine_validator import validate_medicine_name
from app.services.auth_service import (
    request_password_reset_otp,
    verify_password_reset_otp,
    reset_password_with_otp,
    oauth_login_user,
)


class FakeUser:
    def __init__(self, id, full_name, email, password, role="patient", is_active=True):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.password = password
        self.role = role
        self.is_active = is_active


class FakeOTP:
    def __init__(self, id, email, otp_code, expires_at, is_used=False, created_at=None):
        self.id = id
        self.email = email
        self.otp_code = otp_code
        self.expires_at = expires_at
        self.is_used = is_used
        self.created_at = created_at or datetime.now(timezone.utc)


class FakeQuery:
    def __init__(self, items):
        self.items = list(items)

    def filter(self, *criterion):
        filtered = []
        for item in self.items:
            keep = True
            for c in criterion:
                left = getattr(c, 'left', None)
                right = getattr(c, 'right', None)
                if left is not None and right is not None:
                    field_name = getattr(left, 'name', str(left).split('.')[-1])
                    val = getattr(item, field_name, None)
                    target = getattr(right, 'value', right)
                    if val != target:
                        keep = False
            if keep:
                filtered.append(item)
        return FakeQuery(filtered)

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items


class FakeDbSession:
    def __init__(self):
        self.users = []
        self.otps = []

    def query(self, model):
        name = getattr(model, "__name__", str(model))
        if "User" in name:
            return FakeQuery(self.users)
        elif "PasswordResetOTP" in name:
            return FakeQuery(self.otps)
        return FakeQuery([])

    def add(self, obj):
        if not getattr(obj, "id", None):
            obj.id = len(self.users) + len(self.otps) + 1
        if "User" in type(obj).__name__:
            self.users.append(obj)
        elif "PasswordResetOTP" in type(obj).__name__:
            self.otps.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def test_ai_medicine_validation():
    print("Testing Feature 5: AI Medicine Name Validation...")
    
    # Valid medicines
    valid_names = ["Paracetamol", "Amoxicillin 500mg", "Lipitor", "Ibuprofen", "Aspirin", "Metformin"]
    for name in valid_names:
        is_valid, msg = validate_medicine_name(name)
        assert is_valid is True, f"Expected {name} to be valid"
        assert msg == ""

    # Invalid medicine names
    invalid_names = ["asdfghjkl", "123456", "qwertyuiop", "a"]
    for name in invalid_names:
        is_valid, msg = validate_medicine_name(name)
        assert is_valid is False, f"Expected {name} to be invalid"
        assert "could not be verified" in msg or "required" in msg

    print("✓ AI Medicine Name Validation tests passed cleanly.")


def test_google_and_apple_oauth():
    print("Testing Features 2 & 3: Google & Apple OAuth Flow...")
    db = FakeDbSession()

    # New user registers via Google
    res1 = oauth_login_user(db, email="googleuser@example.com", full_name="Google Tester", provider="google")
    assert "access_token" in res1
    assert res1["user"]["email"] == "googleuser@example.com"
    assert len(db.users) == 1

    # Existing user logs in via Google (no duplicates created)
    res2 = oauth_login_user(db, email="googleuser@example.com", full_name="Google Tester", provider="google")
    assert "access_token" in res2
    assert len(db.users) == 1  # Still 1 user

    # New user registers via Apple
    res3 = oauth_login_user(db, email="appleuser@example.com", full_name="Apple Tester", provider="apple")
    assert "access_token" in res3
    assert res3["user"]["email"] == "appleuser@example.com"
    assert len(db.users) == 2

    print("✓ Google & Apple OAuth tests passed cleanly.")


def test_forgot_password_otp_flow():
    print("Testing Feature 1: Forgot Password Email OTP Flow...")
    db = FakeDbSession()
    
    # Pre-populate user
    user = FakeUser(id=1, full_name="Jane Doe", email="jane@example.com", password="oldpassword123")
    db.users.append(user)

    # 1. Request OTP
    res_req = request_password_reset_otp(db, "jane@example.com")
    assert "OTP sent" in res_req["message"]
    assert len(db.otps) == 1
    generated_otp = db.otps[0].otp_code

    # 2. Verify OTP
    res_ver = verify_password_reset_otp(db, "jane@example.com", generated_otp)
    assert "verified" in res_ver["message"]

    # 3. Reset Password
    res_reset = reset_password_with_otp(
        db,
        email="jane@example.com",
        otp=generated_otp,
        new_password="NewSecurePassword123!",
        confirm_password="NewSecurePassword123!"
    )
    assert "successful" in res_reset["message"]
    assert db.otps[0].is_used is True

    print("✓ Forgot Password OTP flow tests passed cleanly.")


def test_enhanced_history_statuses():
    print("Testing Feature 4: Enhanced History Status Enum & Badges...")
    assert HistoryStatus.TREATMENT_STARTED.value == "Treatment Started"
    assert HistoryStatus.TREATMENT_ACTIVE.value == "Treatment Active"
    assert HistoryStatus.COMPLETED.value == "Completed"
    assert HistoryStatus.MEDICINE_ADDED.value == "Medicine Added"
    assert HistoryStatus.MEDICINE_COMPLETED.value == "Medicine Completed"
    assert HistoryStatus.EXPIRED.value == "Expired"
    assert HistoryStatus.CANCELLED.value == "Cancelled"
    assert HistoryStatus.REMINDER_TRIGGERED.value == "Reminder Triggered"
    assert HistoryStatus.TAKEN.value == "Taken"
    assert HistoryStatus.SKIPPED.value == "Skipped"
    assert HistoryStatus.MISSED.value == "Missed"
    assert HistoryStatus.SNOOZED.value == "Snoozed"
    print("✓ Enhanced History Statuses passed cleanly.")


if __name__ == "__main__":
    test_ai_medicine_validation()
    test_google_and_apple_oauth()
    test_forgot_password_otp_flow()
    test_enhanced_history_statuses()
    print("\n🎉 ALL NEW FEATURE TESTS PASSED CLEANLY!")
