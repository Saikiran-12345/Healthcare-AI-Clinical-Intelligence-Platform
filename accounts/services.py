"""
Authentication and User Account Management Service.
Coordinates registration, password verification, profile updates, and role-based record linking.
"""

from typing import Any, Dict, Optional, Tuple
from accounts.auth import JsonUser, PasswordHasher
from core.audit import AuditAction, AuditLogger
from core.exceptions import AuthenticationError, RecordAlreadyExistsError, ValidationError
from core.storage import db, utc_now_iso
from core.validators import Validator


class AuthService:
    """Service layer for authentication, identity management, and credential lifecycle."""

    @staticmethod
    def register_user(
        username: str,
        email: str,
        password: str,
        role: str = "patient",
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
        specialization: str = "",
        license_number: str = "",
        date_of_birth: str = "",
        gender: str = "",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """
        Register a new user, hash password, validate uniqueness, and initialize
        corresponding patient or doctor domain entity.
        """
        # Validate inputs
        clean_username = Validator.validate_username(username)
        clean_email = Validator.validate_email(email)
        clean_password = Validator.validate_password(password)
        clean_role = Validator.validate_role(role)
        clean_first_name = Validator.validate_name(first_name, "First Name") if first_name else ""
        clean_last_name = Validator.validate_name(last_name, "Last Name") if last_name else ""
        clean_phone = Validator.validate_phone(phone) if phone else ""

        # Check existing user
        if db.users.exists(filters={"username": clean_username}):
            raise ValidationError("A user with this username already exists.")
        if db.users.exists(filters={"email": clean_email}):
            raise ValidationError("A user with this email address already exists.")

        # Hash password
        password_hash = PasswordHasher.hash_password(clean_password)

        # Create user record
        user_record = {
            "username": clean_username,
            "email": clean_email,
            "password_hash": password_hash,
            "role": clean_role,
            "first_name": clean_first_name,
            "last_name": clean_last_name,
            "phone": clean_phone,
            "is_active": True,
            "failed_login_attempts": 0,
            "last_login": None,
        }

        created_user = db.users.insert(user_record)
        user_id = created_user["id"]

        # Link to domain-specific table
        if clean_role == "patient":
            patient_record = {
                "user_id": user_id,
                "username": clean_username,
                "full_name": f"{clean_first_name} {clean_last_name}".strip() or clean_username,
                "email": clean_email,
                "phone": clean_phone,
                "date_of_birth": date_of_birth or "1990-01-01",
                "gender": gender.lower() if gender else "other",
                "emergency_contact": "",
                "blood_group": "O+",
                "assigned_doctor_id": None,
                "health_status": "Active",
            }
            db.patients.insert(patient_record)

        elif clean_role == "doctor":
            doctor_record = {
                "user_id": user_id,
                "username": clean_username,
                "full_name": f"{clean_first_name} {clean_last_name}".strip() or f"Dr. {clean_username}",
                "email": clean_email,
                "phone": clean_phone,
                "specialization": specialization or "General Medicine",
                "license_number": license_number or f"MED-{clean_username.upper()}-2026",
                "department": "Primary Care",
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "consultation_hours": "09:00 - 17:00",
                "rating": 4.9,
                "is_available": True,
            }
            db.doctors.insert(doctor_record)

        # Audit log registration
        AuditLogger.log(
            action=AuditAction.REGISTER,
            actor_id=user_id,
            actor_name=clean_username,
            actor_role=clean_role,
            target_entity="users",
            target_id=user_id,
            ip_address=ip_address,
            details={"email": clean_email, "role": clean_role},
        )

        return created_user

    @staticmethod
    def authenticate(username_or_email: str, password: str, ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Authenticate user credentials against users.json.
        Tracks failed login attempts and updates last_login timestamp.
        """
        if not username_or_email or not password:
            raise AuthenticationError("Username/Email and Password are required.")

        identifier = username_or_email.strip().lower()
        # Find by username or email
        user_record = db.users.find_one(filter_func=lambda u: u.get("username", "").lower() == identifier or u.get("email", "").lower() == identifier)

        if not user_record:
            AuditLogger.log(
                action=AuditAction.LOGIN_FAILED,
                actor_name=username_or_email,
                actor_role="guest",
                ip_address=ip_address,
                status="FAILURE",
                details={"reason": "User not found"},
            )
            raise AuthenticationError("Invalid username or password.")

        if not user_record.get("is_active", True):
            AuditLogger.log(
                action=AuditAction.LOGIN_FAILED,
                actor_id=user_record["id"],
                actor_name=user_record["username"],
                actor_role=user_record.get("role", "patient"),
                ip_address=ip_address,
                status="FAILURE",
                details={"reason": "Account is disabled"},
            )
            raise AuthenticationError("This account has been deactivated. Please contact support.")

        stored_hash = user_record.get("password_hash", "")
        if not PasswordHasher.verify_password(password, stored_hash):
            failed_attempts = user_record.get("failed_login_attempts", 0) + 1
            db.users.update(user_record["id"], {"failed_login_attempts": failed_attempts})

            AuditLogger.log(
                action=AuditAction.LOGIN_FAILED,
                actor_id=user_record["id"],
                actor_name=user_record["username"],
                actor_role=user_record.get("role", "patient"),
                ip_address=ip_address,
                status="FAILURE",
                details={"failed_attempts": failed_attempts},
            )
            raise AuthenticationError("Invalid username or password.")

        # Success - Reset failed attempts & stamp last_login
        now = utc_now_iso()
        db.users.update(user_record["id"], {
            "failed_login_attempts": 0,
            "last_login": now,
        })
        user_record["last_login"] = now

        AuditLogger.log(
            action=AuditAction.LOGIN_SUCCESS,
            actor_id=user_record["id"],
            actor_name=user_record["username"],
            actor_role=user_record.get("role", "patient"),
            ip_address=ip_address,
            status="SUCCESS",
        )

        return user_record

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str, ip_address: str = "127.0.0.1") -> bool:
        """Change user password after verifying old password."""
        user = db.users.get_by_id(user_id)
        if not PasswordHasher.verify_password(old_password, user.get("password_hash", "")):
            raise ValidationError("Current password does not match.")

        clean_new_password = Validator.validate_password(new_password)
        new_hash = PasswordHasher.hash_password(clean_new_password)
        db.users.update(user_id, {"password_hash": new_hash})

        AuditLogger.log(
            action=AuditAction.PASSWORD_CHANGE,
            actor_id=user_id,
            actor_name=user["username"],
            actor_role=user.get("role", "patient"),
            ip_address=ip_address,
            status="SUCCESS",
        )
        return True

    @staticmethod
    def update_profile(user_id: str, profile_data: Dict[str, Any], ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """Update general user profile and synchronized patient/doctor records."""
        user = db.users.get_by_id(user_id)

        user_updates = {}
        if "first_name" in profile_data:
            user_updates["first_name"] = Validator.validate_name(profile_data["first_name"], "First Name")
        if "last_name" in profile_data:
            user_updates["last_name"] = Validator.validate_name(profile_data["last_name"], "Last Name")
        if "phone" in profile_data:
            user_updates["phone"] = Validator.validate_phone(profile_data["phone"])

        updated_user = db.users.update(user_id, user_updates)
        full_name = f"{updated_user.get('first_name', '')} {updated_user.get('last_name', '')}".strip()

        # Update linked entity
        if user.get("role") == "patient":
            patient = db.patients.find_one(filters={"user_id": user_id})
            if patient:
                patient_updates = {"full_name": full_name, "phone": updated_user.get("phone", "")}
                if "date_of_birth" in profile_data and profile_data["date_of_birth"]:
                    patient_updates["date_of_birth"] = Validator.validate_date_string(profile_data["date_of_birth"], "Birth Date")
                if "gender" in profile_data and profile_data["gender"]:
                    patient_updates["gender"] = Validator.validate_gender(profile_data["gender"])
                if "blood_group" in profile_data:
                    patient_updates["blood_group"] = profile_data["blood_group"]
                if "emergency_contact" in profile_data:
                    patient_updates["emergency_contact"] = profile_data["emergency_contact"]
                db.patients.update(patient["id"], patient_updates)

        elif user.get("role") == "doctor":
            doctor = db.doctors.find_one(filters={"user_id": user_id})
            if doctor:
                doc_updates = {"full_name": full_name, "phone": updated_user.get("phone", "")}
                if "specialization" in profile_data and profile_data["specialization"]:
                    doc_updates["specialization"] = profile_data["specialization"]
                if "department" in profile_data and profile_data["department"]:
                    doc_updates["department"] = profile_data["department"]
                if "consultation_hours" in profile_data and profile_data["consultation_hours"]:
                    doc_updates["consultation_hours"] = profile_data["consultation_hours"]
                db.doctors.update(doctor["id"], doc_updates)

        AuditLogger.log(
            action=AuditAction.PROFILE_UPDATE,
            actor_id=user_id,
            actor_name=user["username"],
            actor_role=user.get("role", "patient"),
            ip_address=ip_address,
            status="SUCCESS",
        )

        return updated_user

    @staticmethod
    def seed_initial_accounts() -> None:
        """Seed default admin, doctor, and demo patient accounts if table is empty."""
        if db.users.count() == 0:
            # 1. System Administrator
            AuthService.register_user(
                username="admin",
                email="admin@healthcare.local",
                password="AdminPassword123!",
                role="admin",
                first_name="System",
                last_name="Administrator",
                phone="+1-800-555-0100",
            )
            # 2. Senior Clinical Doctor
            AuthService.register_user(
                username="dr_sarah",
                email="dr.sarah@healthcare.local",
                password="DoctorPassword123!",
                role="doctor",
                first_name="Sarah",
                last_name="Jenkins",
                phone="+1-800-555-0101",
                specialization="Cardiology & Internal Medicine",
                license_number="MED-CARD-9921",
            )
            # 3. Demo Patient
            AuthService.register_user(
                username="john_doe",
                email="john.doe@healthcare.local",
                password="PatientPassword123!",
                role="patient",
                first_name="John",
                last_name="Doe",
                phone="+1-800-555-0102",
                date_of_birth="1984-06-15",
                gender="male",
            )
