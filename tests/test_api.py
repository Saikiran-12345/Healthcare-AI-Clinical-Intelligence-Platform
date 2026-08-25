"""Tests for patient-facing JSON integrations."""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.test import RequestFactory

from core.api import patient_summary_api


class TestPatientSummaryApi(unittest.TestCase):
    def test_returns_compact_patient_payload(self):
        request = RequestFactory().get("/api/patient/summary/")
        request.user = SimpleNamespace(id="user-1", role="patient", is_authenticated=True)
        dashboard = {
            "patient": {"id": "patient-1", "full_name": "A Patient", "health_status": "Active"},
            "health_score": 84,
            "latest_profile": {
                "bmi": 23.5,
                "bmi_category": "Normal Weight",
                "systolic_bp": 118,
                "diastolic_bp": 76,
                "heart_rate": 68,
                "blood_glucose": 91,
                "cholesterol": 170,
                "recorded_at": "2026-08-25T10:00:00Z",
                "private_field": "excluded",
            },
            "appointments": [{
                "id": "appointment-1",
                "doctor_name": "Dr. Example",
                "appointment_date": "2026-09-01",
                "appointment_time": "09:00",
                "status": "Approved",
                "priority": "Standard",
                "private_field": "excluded",
            }],
            "recent_predictions": [],
            "recommendations": [],
        }

        with patch("core.api.PatientService.get_patient_dashboard_data", return_value=dashboard):
            response = patient_summary_api(request)

        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["health_score"], 84)
        self.assertNotIn("private_field", payload["latest_profile"])
        self.assertEqual(payload["appointments"][0]["status"], "Approved")


if __name__ == "__main__":
    unittest.main()