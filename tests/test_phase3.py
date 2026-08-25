"""
Phase 3 Unit Tests: Patient Management, Health Profiles, Medical History, and Symptom Logging.
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
from core.exceptions import ValidationError


class TestPatientService(unittest.TestCase):
    """Test patient health profile calculations, medical history, and symptom tracking."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from core import storage
        self.orig_db = storage.db
        storage.db = JsonDatabase(self.temp_dir)
        import accounts.services, patients.services
        accounts.services.db = storage.db
        patients.services.db = storage.db

        # Create demo patient user
        self.user = AuthService.register_user(
            username="patient_test",
            email="patient.test@example.com",
            password="TestPassword123!",
            role="patient",
            first_name="Test",
            last_name="Patient",
        )
        self.patient = PatientService.get_patient_by_user_id(self.user["id"])

    def tearDown(self):
        from core import storage
        storage.db = self.orig_db
        import accounts.services, patients.services
        accounts.services.db = self.orig_db
        patients.services.db = self.orig_db
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_health_profile_and_bmi_calculation(self):
        profile_data = {
            "age": 40,
            "gender": "female",
            "height_cm": 160.0,
            "weight_kg": 64.0,  # BMI = 64 / (1.6^2) = 25.0 (Overweight borderline)
            "systolic_bp": 125,
            "diastolic_bp": 82,
            "heart_rate": 74,
            "blood_glucose": 98.0,
            "cholesterol": 190.0,
            "sleep_hours": 8.0,
            "water_intake_liters": 2.2,
            "exercise_frequency_days": 4,
            "stress_level": 3,
        }
        profile = PatientService.save_health_profile(
            patient_id=self.patient["id"],
            user_id=self.user["id"],
            profile_data=profile_data
        )

        self.assertEqual(profile["bmi"], 25.0)
        self.assertEqual(profile["bmi_category"], "Overweight")
        self.assertEqual(profile["systolic_bp"], 125)

        latest = PatientService.get_latest_health_profile(self.patient["id"])
        self.assertIsNotNone(latest)
        self.assertEqual(latest["id"], profile["id"])

    def test_medical_history_lifecycle(self):
        history = PatientService.add_medical_history(
            patient_id=self.patient["id"],
            user_id=self.user["id"],
            condition="Hypertension Stage 1",
            diagnosis_date="2024-01-15",
            status="Managed",
            severity="Moderate",
            notes="Prescribed ACE inhibitor daily.",
        )
        self.assertEqual(history["condition"], "Hypertension Stage 1")

        records = PatientService.get_medical_history(self.patient["id"])
        self.assertEqual(len(records), 1)

        # Delete record
        deleted = PatientService.delete_medical_history(history["id"], self.patient["id"])
        self.assertTrue(deleted)
        self.assertEqual(len(PatientService.get_medical_history(self.patient["id"])), 0)

    def test_symptom_logging(self):
        sym = PatientService.log_symptom_entry(
            patient_id=self.patient["id"],
            user_id=self.user["id"],
            symptom_name="Headache with Dizziness",
            category="Neurological",
            severity=4,
            duration_days=3,
            frequency="Daily",
        )
        self.assertEqual(sym["symptom_name"], "Headache with Dizziness")
        self.assertEqual(sym["severity"], 4)

        symptoms = PatientService.get_patient_symptoms(self.patient["id"])
        self.assertEqual(len(symptoms), 1)

    def test_dashboard_data_aggregation(self):
        dash_data = PatientService.get_patient_dashboard_data(self.user["id"])
        self.assertIn("patient", dash_data)
        self.assertIn("health_score", dash_data)
        self.assertTrue(0 <= dash_data["health_score"] <= 100)


if __name__ == '__main__':
    unittest.main()
