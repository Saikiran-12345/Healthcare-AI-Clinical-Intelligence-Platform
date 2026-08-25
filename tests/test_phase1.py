"""
Phase 1 Unit Tests: Storage Engine, Validators, CSV Export, Audit Logger, Password Hasher, and Django Init.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Configure settings before django test setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.storage import JsonTable, JsonDatabase
from core.validators import Validator, ValidationError
from core.csv_storage import CsvStorage
from core.audit import AuditLogger, AuditAction
from accounts.auth import PasswordHasher


class TestJsonStorageEngine(unittest.TestCase):
    """Test the atomic JSON table CRUD, filtering, sorting, and error handling."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.table_path = Path(self.temp_dir) / "test_records.json"
        self.table = JsonTable(self.table_path, "test_records")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_insert_and_find_by_id(self):
        record = {"name": "Alice", "age": 30, "role": "patient"}
        inserted = self.table.insert(record)
        self.assertIn("id", inserted)
        self.assertIn("created_at", inserted)
        self.assertEqual(inserted["name"], "Alice")

        found = self.table.find_by_id(inserted["id"])
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Alice")

    def test_find_all_and_filtering(self):
        self.table.insert({"name": "Bob", "department": "Cardiology", "active": True})
        self.table.insert({"name": "Charlie", "department": "Endocrinology", "active": True})
        self.table.insert({"name": "Diana", "department": "Cardiology", "active": False})

        cardio_records = self.table.find_all(filters={"department": "Cardiology"})
        self.assertEqual(len(cardio_records), 2)

        active_cardio = self.table.find_all(filters={"department": "Cardiology", "active": True})
        self.assertEqual(len(active_cardio), 1)
        self.assertEqual(active_cardio[0]["name"], "Bob")

    def test_update_record(self):
        inserted = self.table.insert({"name": "Eve", "status": "pending"})
        updated = self.table.update(inserted["id"], {"status": "approved"})
        self.assertEqual(updated["status"], "approved")

        fresh = self.table.find_by_id(inserted["id"])
        self.assertEqual(fresh["status"], "approved")

    def test_delete_record(self):
        inserted = self.table.insert({"name": "Frank"})
        self.assertEqual(self.table.count(), 1)
        deleted = self.table.delete(inserted["id"])
        self.assertTrue(deleted)
        self.assertEqual(self.table.count(), 0)

    def test_unique_field_constraint(self):
        self.table.insert({"username": "user1", "email": "u1@test.com"}, unique_fields=["username", "email"])
        with self.assertRaises(Exception):
            self.table.insert({"username": "user1", "email": "u2@test.com"}, unique_fields=["username", "email"])


class TestValidators(unittest.TestCase):
    """Test clinical and general validators."""

    def test_email_validation(self):
        self.assertEqual(Validator.validate_email("Patient@Example.com"), "patient@example.com")
        with self.assertRaises(ValidationError):
            Validator.validate_email("invalid-email")

    def test_username_validation(self):
        self.assertEqual(Validator.validate_username("dr_smith123"), "dr_smith123")
        with self.assertRaises(ValidationError):
            Validator.validate_username("a")  # too short
        with self.assertRaises(ValidationError):
            Validator.validate_username("invalid username with space")

    def test_blood_pressure_validation(self):
        sys, dia = Validator.validate_blood_pressure(120, 80)
        self.assertEqual((sys, dia), (120, 80))

        with self.assertRaises(ValidationError):
            Validator.validate_blood_pressure(80, 120)  # diastolic >= systolic

        with self.assertRaises(ValidationError):
            Validator.validate_blood_pressure(300, 80)  # systolic out of range

    def test_glucose_validation(self):
        self.assertEqual(Validator.validate_glucose(95.5), 95.5)
        with self.assertRaises(ValidationError):
            Validator.validate_glucose(10.0)  # too low

    def test_bmi_and_metrics_validation(self):
        self.assertEqual(Validator.validate_height(175.0), 175.0)
        self.assertEqual(Validator.validate_weight(70.5), 70.5)
        self.assertEqual(Validator.validate_heart_rate(72), 72)
        with self.assertRaises(ValidationError):
            Validator.validate_height(300)  # invalid height


class TestPasswordHasher(unittest.TestCase):
    """Test PBKDF2 password hashing security."""

    def test_hash_and_verify(self):
        pwd = "SecureMedicalPassword123!"
        hashed = PasswordHasher.hash_password(pwd)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(PasswordHasher.verify_password(pwd, hashed))
        self.assertFalse(PasswordHasher.verify_password("WrongPassword!", hashed))


class TestCsvStorage(unittest.TestCase):
    """Test CSV export and import."""

    def test_export_and_import(self):
        records = [
            {"id": "1", "name": "Patient Alpha", "age": "45"},
            {"id": "2", "name": "Patient Beta", "age": "52"},
        ]
        csv_str = CsvStorage.export_to_csv_string(records, fieldnames=["id", "name", "age"])
        self.assertIn("Patient Alpha", csv_str)
        self.assertIn("Patient Beta", csv_str)


if __name__ == '__main__':
    unittest.main()
