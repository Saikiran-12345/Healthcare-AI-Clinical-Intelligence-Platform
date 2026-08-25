"""
Phase 2 Unit Tests: Authentication, User Registration, RBAC, Passwords, and Profile Updates.
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
from accounts.auth import JsonUser, AnonymousUser, PasswordHasher
from core.exceptions import AuthenticationError, ValidationError


class TestAuthenticationService(unittest.TestCase):
    """Test user registration, authentication, and role assignment."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Patch the db instance in accounts.services with temporary db
        from core import storage
        self.orig_db = storage.db
        storage.db = JsonDatabase(self.temp_dir)
        import accounts.services
        accounts.services.db = storage.db

    def tearDown(self):
        from core import storage
        storage.db = self.orig_db
        import accounts.services
        accounts.services.db = self.orig_db
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_patient_registration_and_authentication(self):
        user = AuthService.register_user(
            username="patient_bob",
            email="bob@example.com",
            password="SecurePassword123!",
            role="patient",
            first_name="Bob",
            last_name="Smith",
        )
        self.assertEqual(user["username"], "patient_bob")
        self.assertEqual(user["role"], "patient")

        # Check linked patient record
        from core.storage import db
        patient = db.patients.find_one(filters={"user_id": user["id"]})
        self.assertIsNotNone(patient)
        self.assertEqual(patient["full_name"], "Bob Smith")

        # Authenticate with valid credentials
        auth_user = AuthService.authenticate("patient_bob", "SecurePassword123!")
        self.assertEqual(auth_user["id"], user["id"])
        self.assertIsNotNone(auth_user["last_login"])

        # Authenticate with email
        auth_email_user = AuthService.authenticate("bob@example.com", "SecurePassword123!")
        self.assertEqual(auth_email_user["id"], user["id"])

        # Authenticate with invalid password
        with self.assertRaises(AuthenticationError):
            AuthService.authenticate("patient_bob", "WrongPassword123!")

    def test_duplicate_registration_prevention(self):
        AuthService.register_user(
            username="patient_alice",
            email="alice@example.com",
            password="Password123!",
        )
        # Duplicate username
        with self.assertRaises(ValidationError):
            AuthService.register_user(
                username="patient_alice",
                email="other_alice@example.com",
                password="Password123!",
            )
        # Duplicate email
        with self.assertRaises(ValidationError):
            AuthService.register_user(
                username="another_alice",
                email="alice@example.com",
                password="Password123!",
            )

    def test_doctor_registration(self):
        doc = AuthService.register_user(
            username="dr_watson",
            email="watson@clinic.local",
            password="DocPassword123!",
            role="doctor",
            first_name="John",
            last_name="Watson",
            specialization="General Medicine",
        )
        from core.storage import db
        doctor_rec = db.doctors.find_one(filters={"user_id": doc["id"]})
        self.assertIsNotNone(doctor_rec)
        self.assertEqual(doctor_rec["specialization"], "General Medicine")

    def test_password_change(self):
        user = AuthService.register_user(
            username="user_pass",
            email="pass@example.com",
            password="InitialPassword123!",
        )
        # Verify old password error
        with self.assertRaises(ValidationError):
            AuthService.change_password(user["id"], "IncorrectOldPwd!", "NewSecurePassword456!")

        # Success password change
        res = AuthService.change_password(user["id"], "InitialPassword123!", "NewSecurePassword456!")
        self.assertTrue(res)

        # Authenticate with new password
        auth_user = AuthService.authenticate("user_pass", "NewSecurePassword456!")
        self.assertEqual(auth_user["id"], user["id"])

    def test_profile_update(self):
        user = AuthService.register_user(
            username="profile_user",
            email="prof@example.com",
            password="Password123!",
            role="patient",
            first_name="Old",
            last_name="Name",
        )
        AuthService.update_profile(user["id"], {
            "first_name": "New",
            "last_name": "Updated",
            "phone": "+1-555-9999",
            "blood_group": "AB+",
        })
        from core.storage import db
        updated_user = db.users.get_by_id(user["id"])
        self.assertEqual(updated_user["first_name"], "New")
        self.assertEqual(updated_user["last_name"], "Updated")
        self.assertEqual(updated_user["phone"], "+1-555-9999")

        patient = db.patients.find_one(filters={"user_id": user["id"]})
        self.assertEqual(patient["blood_group"], "AB+")
        self.assertEqual(patient["full_name"], "New Updated")


if __name__ == '__main__':
    unittest.main()
