"""
Phase 4 Unit Tests: Doctor Management, Patient Roster, Clinical Notes, and High-Risk Triage.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.storage import JsonDatabase
from accounts.services import AuthService
from patients.services import PatientService
from doctors.services import DoctorService


class TestDoctorService(unittest.TestCase):
    """Test doctor clinical workflows, notes, patient charts, and risk monitoring."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from core import storage
        self.orig_db = storage.db
        storage.db = JsonDatabase(self.temp_dir)
        import accounts.services, patients.services, doctors.services
        accounts.services.db = storage.db
        patients.services.db = storage.db
        doctors.services.db = storage.db

        # Register a doctor
        self.doc_user = AuthService.register_user(
            username="dr_house",
            email="dr.house@clinic.local",
            password="DocPassword123!",
            role="doctor",
            first_name="Gregory",
            last_name="House",
            specialization="Diagnostic Medicine",
        )
        self.doctor = DoctorService.get_doctor_by_user_id(self.doc_user["id"])

        # Register a patient
        self.pat_user = AuthService.register_user(
            username="patient_chase",
            email="chase@patient.local",
            password="PatientPassword123!",
            role="patient",
            first_name="Robert",
            last_name="Chase",
        )
        self.patient = PatientService.get_patient_by_user_id(self.pat_user["id"])

    def tearDown(self):
        from core import storage
        storage.db = self.orig_db
        import accounts.services, patients.services, doctors.services
        accounts.services.db = self.orig_db
        patients.services.db = self.orig_db
        doctors.services.db = self.orig_db
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_all_doctors(self):
        docs = DoctorService.get_all_doctors()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["specialization"], "Diagnostic Medicine")

    def test_patient_roster_and_search(self):
        roster = DoctorService.get_patient_roster()
        self.assertEqual(len(roster), 1)
        self.assertEqual(roster[0]["patient"]["full_name"], "Robert Chase")

        # Search by keyword match
        matched = DoctorService.get_patient_roster(search_query="robert")
        self.assertEqual(len(matched), 1)

        # Search non-match
        unmatched = DoctorService.get_patient_roster(search_query="nonexistent_name")
        self.assertEqual(len(unmatched), 0)

    def test_clinical_notes_addition_and_chart(self):
        note = DoctorService.add_clinical_note(
            doctor_id=self.doctor["id"],
            doctor_name=self.doctor["full_name"],
            patient_id=self.patient["id"],
            subjective="Patient reports occasional morning headaches.",
            assessment="Essential Hypertension Stage 1 suspected.",
            plan="Initiate DASH diet and monitor BP daily.",
            prescriptions="Amlodipine 5mg OD",
            follow_up_date="2026-09-15",
        )
        self.assertIn("id", note)
        self.assertEqual(note["prescriptions"], "Amlodipine 5mg OD")

        chart = DoctorService.get_patient_clinical_chart(self.patient["id"])
        self.assertEqual(len(chart["clinical_notes"]), 1)
        self.assertEqual(chart["clinical_notes"][0]["assessment"], "Essential Hypertension Stage 1 suspected.")

    def test_high_risk_surveillance_detection(self):
        # Insert a high-risk prediction for this patient
        from core.storage import db
        db.predictions.insert({
            "patient_id": self.patient["id"],
            "disease_type": "Heart Disease",
            "risk_level": "HIGH",
            "probability_pct": 87.5,
        })

        high_risk_cases = DoctorService.get_high_risk_patients()
        self.assertEqual(len(high_risk_cases), 1)
        self.assertEqual(high_risk_cases[0]["patient"]["id"], self.patient["id"])
        self.assertIn("Heart Disease", high_risk_cases[0]["all_high_diseases"])


if __name__ == '__main__':
    unittest.main()
