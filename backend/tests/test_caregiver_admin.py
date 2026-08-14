import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.treatment import Treatment
from app.models.medicine import Medicine
from app.models.reminder import Reminder
from app.models.caregiver_patient import CaregiverPatient
from app.utils.password import hash_password
from app.utils.jwt_handler import create_access_token


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_caregiver_admin.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_db():
    import os
    if os.path.exists("./test_caregiver_admin.db"):
        try:
            os.remove("./test_caregiver_admin.db")
        except Exception:
            pass

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create Patient, Caregiver, and Admin users
    patient = User(full_name="Test Patient", email="patient@test.com", password=hash_password("Pass123!"), role="patient")
    caregiver = User(full_name="Test Caregiver", email="caregiver@test.com", password=hash_password("Pass123!"), role="caregiver")
    admin = User(full_name="Test Admin", email="admin@test.com", password=hash_password("Pass123!"), role="admin")

    unrelated_patient = User(full_name="Unrelated Patient", email="unrelated@test.com", password=hash_password("Pass123!"), role="patient")

    db.add_all([patient, caregiver, admin, unrelated_patient])
    db.commit()

    # Link Caregiver to Patient
    link = CaregiverPatient(caregiver_id=caregiver.id, patient_id=patient.id)
    db.add(link)

    # Add treatment & medicine for patient
    now_d = date.today()
    treatment = Treatment(
        user_id=patient.id,
        disease_name="Hypertension",
        start_date=now_d,
        end_date=now_d + timedelta(days=3),
        status="Active"
    )
    db.add(treatment)
    db.commit()

    med = Medicine(treatment_id=treatment.id, medicine_name="Amlodipine", medicine_type="Tablet", quantity=10, dosage="1 tablet", instructions="3 days", is_active=True)
    db.add(med)
    db.commit()

    db.close()

    def override_get_db():
        try:
            db_session = TestingSessionLocal()
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_caregiver_admin.db"):
        try:
            os.remove("./test_caregiver_admin.db")
        except Exception:
            pass


def get_headers(email: str, role: str, user_id: int):
    token = create_access_token({"sub": email, "role": role, "id": user_id})
    return {"Authorization": f"Bearer {token}"}


def test_caregiver_dashboard_access(setup_db):
    client = TestClient(app)

    db = TestingSessionLocal()
    cg = db.query(User).filter(User.email == "caregiver@test.com").first()
    pat = db.query(User).filter(User.email == "patient@test.com").first()
    db.close()

    headers = get_headers(cg.email, cg.role, cg.id)
    res = client.get("/caregiver/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["caregiver_name"] == "Test Caregiver"
    assert data["total_patients"] == 1


def test_caregiver_patient_authorization(setup_db):
    client = TestClient(app)

    db = TestingSessionLocal()
    cg = db.query(User).filter(User.email == "caregiver@test.com").first()
    pat = db.query(User).filter(User.email == "patient@test.com").first()
    unrel = db.query(User).filter(User.email == "unrelated@test.com").first()
    db.close()

    headers = get_headers(cg.email, cg.role, cg.id)

    # Access assigned patient -> 200 OK
    res_ok = client.get(f"/caregiver/patients/{pat.id}", headers=headers)
    assert res_ok.status_code == 200

    # Access unrelated patient -> 403 FORBIDDEN
    res_forbidden = client.get(f"/caregiver/patients/{unrel.id}", headers=headers)
    assert res_forbidden.status_code == 403


def test_admin_dashboard_and_rbac(setup_db):
    client = TestClient(app)

    db = TestingSessionLocal()
    adm = db.query(User).filter(User.email == "admin@test.com").first()
    pat = db.query(User).filter(User.email == "patient@test.com").first()
    db.close()

    admin_headers = get_headers(adm.email, adm.role, adm.id)
    patient_headers = get_headers(pat.email, pat.role, pat.id)

    # Patient attempting admin route -> 403 FORBIDDEN
    res_pat_admin = client.get("/admin/dashboard", headers=patient_headers)
    assert res_pat_admin.status_code == 403

    # Admin accessing admin route -> 200 OK
    res_admin_ok = client.get("/admin/dashboard", headers=admin_headers)
    assert res_admin_ok.status_code == 200
    data = res_admin_ok.status_code == 200
    assert res_admin_ok.json()["patients_count"] >= 2
