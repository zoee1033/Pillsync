import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.models.user import User
from app.models.caregiver_patient import CaregiverPatient
from app.services.caregiver_service import (
    link_patient_by_email,
    get_assigned_patients,
    accept_caregiver_request,
    reject_caregiver_request
)


class TestCaregiverRequestFlow(unittest.TestCase):

    def setUp(self):
        self.caregiver_a = User(id=1, full_name="Caregiver A", email="cg_a@pillsync.ai", role="caregiver")
        self.caregiver_b = User(id=2, full_name="Caregiver B", email="cg_b@pillsync.ai", role="caregiver")
        self.patient_a = User(id=10, full_name="Patient A", email="pt_a@pillsync.ai", role="patient")
        self.patient_b = User(id=11, full_name="Patient B", email="pt_b@pillsync.ai", role="patient")

    def test_flow_1_send_request_creates_pending(self):
        """Caregiver sends request -> PENDING status created. Patient NOT in active list."""
        db = MagicMock()

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = self.patient_a

        cg_query = MagicMock()
        cg_query.filter.return_value.first.return_value = None
        cg_query.filter.return_value.all.return_value = []

        def query_router(model):
            if model == User:
                return user_query
            return cg_query

        db.query.side_effect = query_router

        res = link_patient_by_email(db, self.caregiver_a, "pt_a@pillsync.ai")
        self.assertEqual(res["status"], "pending")
        self.assertIn("Waiting for patient approval", res["message"])

        # Verify active patients list is empty
        active_pts = get_assigned_patients(db, self.caregiver_a)
        self.assertEqual(len(active_pts), 0)

    def test_flow_2_patient_accept_creates_active_connection(self):
        """Patient accepts request -> Status becomes active. Patient appears in My Patients."""
        db = MagicMock()
        link_req = CaregiverPatient(id=100, caregiver_id=self.caregiver_a.id, patient_id=self.patient_a.id, status="pending")

        cg_query = MagicMock()
        # 1st call for request_id lookup returns link_req, 2nd call for active check returns None
        cg_query.filter.return_value.first.side_effect = [link_req, None]

        db.query.return_value = cg_query

        res = accept_caregiver_request(db, self.patient_a, 100)
        self.assertEqual(link_req.status, "active")
        self.assertIn("Connection is now active", res["message"])

    def test_flow_3_patient_reject(self):
        """Patient rejects request -> Status becomes rejected. No active relationship created."""
        db = MagicMock()
        link_req = CaregiverPatient(id=101, caregiver_id=self.caregiver_a.id, patient_id=self.patient_a.id, status="pending")

        cg_query = MagicMock()
        cg_query.filter.return_value.first.return_value = link_req
        db.query.return_value = cg_query

        res = reject_caregiver_request(db, self.patient_a, 101)
        self.assertEqual(link_req.status, "rejected")
        self.assertIn("rejected", res["message"].lower())

    def test_flow_4_one_caregiver_per_patient_rule(self):
        """Patient already has active caregiver -> Second caregiver request fails."""
        db = MagicMock()
        active_link = CaregiverPatient(id=1, caregiver_id=self.caregiver_a.id, patient_id=self.patient_a.id, status="active")

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = self.patient_a

        cg_query = MagicMock()
        cg_query.filter.return_value.first.return_value = active_link

        def query_router(model):
            if model == User:
                return user_query
            return cg_query

        db.query.side_effect = query_router

        with self.assertRaises(HTTPException) as ctx:
            link_patient_by_email(db, self.caregiver_b, "pt_a@pillsync.ai")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already has an active caregiver", ctx.exception.detail)

    def test_flow_5_duplicate_pending_request_protection(self):
        """Caregiver sends duplicate request while one is pending -> Blocked with 400."""
        db = MagicMock()
        pending_link = CaregiverPatient(id=1, caregiver_id=self.caregiver_a.id, patient_id=self.patient_a.id, status="pending")

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = self.patient_a

        cg_query = MagicMock()
        # 1st call (active check): None, 2nd call (existing request check): pending_link
        cg_query.filter.return_value.first.side_effect = [None, pending_link]

        def query_router(model):
            if model == User:
                return user_query
            return cg_query

        db.query.side_effect = query_router

        with self.assertRaises(HTTPException) as ctx:
            link_patient_by_email(db, self.caregiver_a, "pt_a@pillsync.ai")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already pending", ctx.exception.detail)

    def test_flow_6_security_patient_cannot_accept_others_request(self):
        """Patient A trying to accept Patient B's request -> 403 Forbidden."""
        db = MagicMock()
        link_req = CaregiverPatient(id=105, caregiver_id=self.caregiver_a.id, patient_id=self.patient_b.id, status="pending")

        cg_query = MagicMock()
        cg_query.filter.return_value.first.return_value = link_req
        db.query.return_value = cg_query

        with self.assertRaises(HTTPException) as ctx:
            accept_caregiver_request(db, self.patient_a, 105)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access denied", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
