"""
Phase 6 Unit Tests: Appointments, Conflict Prevention, Status Transitions, and Notifications.
"""

from datetime import date, timedelta
import os
import shutil
import tempfile
import unittest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.storage import JsonDatabase
from accounts.services import AuthService
from patients.services import PatientService
from doctors.services import DoctorService
from appointments.services import AppointmentService
from core.exceptions import AppointmentConflictError
from notifications.services import NotificationService, NotificationType


class TestAppointmentService(unittest.TestCase):
    """Test booking, double-booking prevention, approvals, and status transitions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from core import storage
        self.orig_db = storage.db
        storage.db = JsonDatabase(self.temp_dir)
        import accounts.services, patients.services, doctors.services, appointments.services, notifications.services
        accounts.services.db = storage.db
        patients.services.db = storage.db
        doctors.services.db = storage.db
        appointments.services.db = storage.db
        notifications.services.db = storage.db

        # Register doctor
        self.doc_user = AuthService.register_user(
            username="dr_curie",
            email="dr.curie@clinic.local",
            password="DocPassword123!",
            role="doctor",
            first_name="Marie",
            last_name="Curie",
            specialization="Oncology",
        )
        self.doctor = DoctorService.get_doctor_by_user_id(self.doc_user["id"])

        # Register patient 1
        self.pat_user1 = AuthService.register_user(
            username="patient_p1",
            email="p1@example.com",
            password="PatientPassword123!",
            role="patient",
            first_name="Patient",
            last_name="One",
        )
        self.patient1 = PatientService.get_patient_by_user_id(self.pat_user1["id"])

        # Register patient 2
        self.pat_user2 = AuthService.register_user(
            username="patient_p2",
            email="p2@example.com",
            password="PatientPassword123!",
            role="patient",
            first_name="Patient",
            last_name="Two",
        )
        self.patient2 = PatientService.get_patient_by_user_id(self.pat_user2["id"])

        self.future_date = (date.today() + timedelta(days=5)).isoformat()

    def tearDown(self):
        from core import storage
        storage.db = self.orig_db
        import accounts.services, patients.services, doctors.services, appointments.services, notifications.services
        accounts.services.db = self.orig_db
        patients.services.db = self.orig_db
        doctors.services.db = self.orig_db
        appointments.services.db = self.orig_db
        notifications.services.db = self.orig_db
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_booking_and_conflict_detection(self):
        # Book slot for patient 1
        appt1 = AppointmentService.book_appointment(
            patient_id=self.patient1["id"],
            doctor_id=self.doctor["id"],
            date_str=self.future_date,
            time_str="10:00",
            reason="Cardiovascular consultation",
        )
        self.assertEqual(appt1["status"], "Pending")

        # Double booking by patient 2 at same date and time should raise conflict
        with self.assertRaises(AppointmentConflictError):
            AppointmentService.book_appointment(
                patient_id=self.patient2["id"],
                doctor_id=self.doctor["id"],
                date_str=self.future_date,
                time_str="10:00",
                reason="Routine checkup",
            )

        # Patient 2 booking a different time slot succeeds
        appt2 = AppointmentService.book_appointment(
            patient_id=self.patient2["id"],
            doctor_id=self.doctor["id"],
            date_str=self.future_date,
            time_str="11:00",
            reason="Routine checkup",
        )
        self.assertEqual(appt2["status"], "Pending")

    def test_appointment_approval_and_completion_workflow(self):
        appt = AppointmentService.book_appointment(
            patient_id=self.patient1["id"],
            doctor_id=self.doctor["id"],
            date_str=self.future_date,
            time_str="14:00",
            reason="Blood pressure review",
        )

        # Doctor approves
        approved = AppointmentService.approve_appointment(
            appointment_id=appt["id"],
            doctor_id=self.doctor["id"],
            notes="Confirmed. Please bring recent BP logs.",
        )
        self.assertEqual(approved["status"], "Approved")

        # Doctor completes
        completed = AppointmentService.complete_appointment(
            appointment_id=appt["id"],
            doctor_id=self.doctor["id"],
            notes="Consultation concluded. Prescribed lifestyle changes.",
        )
        self.assertEqual(completed["status"], "Completed")

    def test_available_slots_query(self):
        AppointmentService.book_appointment(
            patient_id=self.patient1["id"],
            doctor_id=self.doctor["id"],
            date_str=self.future_date,
            time_str="09:00",
            reason="Checkup",
        )
        slots = AppointmentService.get_doctor_available_slots(self.doctor["id"], self.future_date)
        self.assertNotIn("09:00", slots)
        self.assertIn("09:30", slots)

    def test_notification_type_filter(self):
        NotificationService.create(
            recipient_id=self.pat_user1["id"],
            notification_type=NotificationType.APPOINTMENT_APPROVED,
            title="Appointment Confirmed",
            message="Your appointment was approved.",
        )
        NotificationService.create(
            recipient_id=self.pat_user1["id"],
            notification_type=NotificationType.HIGH_RISK_ALERT,
            title="Risk Alert",
            message="Review your latest assessment.",
        )

        alerts = NotificationService.get_user_notifications(
            self.pat_user1["id"], notification_type=NotificationType.HIGH_RISK_ALERT
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["type"], NotificationType.HIGH_RISK_ALERT)


if __name__ == '__main__':
    unittest.main()
