"""
Core Input & Clinical Data Validators for Healthcare AI Application.
Provides rigorous verification for physiological metrics, user inputs, and clinical records.
"""

import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from core.exceptions import ValidationError


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-()]{7,20}$')


class Validator:
    """Central validator utility class with static validation methods."""

    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username format (3-30 chars, alphanumeric and underscore)."""
        if not username or not isinstance(username, str):
            raise ValidationError("Username is required.")
        username = username.strip()
        if not USERNAME_REGEX.match(username):
            raise ValidationError(
                "Username must be 3-30 characters long and contain only letters, numbers, and underscores."
            )
        return username

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format and length."""
        if not email or not isinstance(email, str):
            raise ValidationError("Email address is required.")
        email = email.strip().lower()
        if len(email) > 120 or not EMAIL_REGEX.match(email):
            raise ValidationError("Please provide a valid email address.")
        return email

    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength (min 8 chars, at least one digit and letter)."""
        if not password or not isinstance(password, str):
            raise ValidationError("Password is required.")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit.")
        if not any(c.isalpha() for c in password):
            raise ValidationError("Password must contain at least one letter.")
        return password

    @staticmethod
    def validate_name(name: str, field_name: str = "Name") -> str:
        """Validate full name."""
        if not name or not isinstance(name, str):
            raise ValidationError(f"{field_name} is required.")
        name = name.strip()
        if len(name) < 2 or len(name) > 100:
            raise ValidationError(f"{field_name} must be between 2 and 100 characters.")
        return name

    @staticmethod
    def validate_phone(phone: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided."""
        if not phone:
            return ""
        phone = phone.strip()
        if not PHONE_REGEX.match(phone):
            raise ValidationError("Please enter a valid phone number.")
        return phone

    @staticmethod
    def validate_role(role: str) -> str:
        """Validate allowed system role."""
        allowed_roles = {'patient', 'doctor', 'admin'}
        if not role or role.lower() not in allowed_roles:
            raise ValidationError(f"Role must be one of: {', '.join(allowed_roles)}")
        return role.lower()

    @staticmethod
    def validate_age(age: Any) -> int:
        """Validate age between 1 and 120."""
        try:
            val = int(age)
        except (ValueError, TypeError):
            raise ValidationError("Age must be a valid integer.")
        if val < 1 or val > 120:
            raise ValidationError("Age must be between 1 and 120 years.")
        return val

    @staticmethod
    def validate_gender(gender: str) -> str:
        """Validate gender."""
        allowed = {'male', 'female', 'other'}
        if not gender or gender.lower() not in allowed:
            raise ValidationError(f"Gender must be one of: {', '.join(allowed)}")
        return gender.lower()

    @staticmethod
    def validate_height(height_cm: Any) -> float:
        """Validate height in centimeters (50 cm - 250 cm)."""
        try:
            val = float(height_cm)
        except (ValueError, TypeError):
            raise ValidationError("Height must be a valid number in cm.")
        if val < 50.0 or val > 250.0:
            raise ValidationError("Height must be between 50.0 cm and 250.0 cm.")
        return round(val, 2)

    @staticmethod
    def validate_weight(weight_kg: Any) -> float:
        """Validate weight in kilograms (2.0 kg - 350.0 kg)."""
        try:
            val = float(weight_kg)
        except (ValueError, TypeError):
            raise ValidationError("Weight must be a valid number in kg.")
        if val < 2.0 or val > 350.0:
            raise ValidationError("Weight must be between 2.0 kg and 350.0 kg.")
        return round(val, 2)

    @staticmethod
    def validate_blood_pressure(systolic: Any, diastolic: Any) -> Tuple[int, int]:
        """Validate systolic and diastolic blood pressure readings."""
        try:
            sys_val = int(systolic)
            dia_val = int(diastolic)
        except (ValueError, TypeError):
            raise ValidationError("Blood pressure values must be integers.")

        if sys_val < 60 or sys_val > 260:
            raise ValidationError("Systolic blood pressure must be between 60 and 260 mmHg.")
        if dia_val < 40 or dia_val > 160:
            raise ValidationError("Diastolic blood pressure must be between 40 and 160 mmHg.")
        if dia_val >= sys_val:
            raise ValidationError("Systolic blood pressure must be strictly greater than diastolic blood pressure.")

        return sys_val, dia_val

    @staticmethod
    def validate_heart_rate(hr: Any) -> int:
        """Validate resting heart rate (30 - 220 bpm)."""
        try:
            val = int(hr)
        except (ValueError, TypeError):
            raise ValidationError("Heart rate must be an integer.")
        if val < 30 or val > 220:
            raise ValidationError("Heart rate must be between 30 and 220 bpm.")
        return val

    @staticmethod
    def validate_glucose(glucose_mg_dl: Any) -> float:
        """Validate fasting blood glucose level (40.0 - 500.0 mg/dL)."""
        try:
            val = float(glucose_mg_dl)
        except (ValueError, TypeError):
            raise ValidationError("Glucose must be a valid number in mg/dL.")
        if val < 40.0 or val > 500.0:
            raise ValidationError("Glucose level must be between 40.0 and 500.0 mg/dL.")
        return round(val, 2)

    @staticmethod
    def validate_cholesterol(cholesterol_mg_dl: Any) -> float:
        """Validate total cholesterol (80.0 - 500.0 mg/dL)."""
        try:
            val = float(cholesterol_mg_dl)
        except (ValueError, TypeError):
            raise ValidationError("Cholesterol must be a valid number in mg/dL.")
        if val < 80.0 or val > 500.0:
            raise ValidationError("Cholesterol level must be between 80.0 and 500.0 mg/dL.")
        return round(val, 2)

    @staticmethod
    def validate_sleep_hours(sleep_hours: Any) -> float:
        """Validate sleep duration per day (0.0 - 24.0 hours)."""
        try:
            val = float(sleep_hours)
        except (ValueError, TypeError):
            raise ValidationError("Sleep duration must be a valid number.")
        if val < 0.0 or val > 24.0:
            raise ValidationError("Sleep hours must be between 0 and 24 hours.")
        return round(val, 1)

    @staticmethod
    def validate_water_intake(liters: Any) -> float:
        """Validate water intake per day (0.0 - 15.0 liters)."""
        try:
            val = float(liters)
        except (ValueError, TypeError):
            raise ValidationError("Water intake must be a valid number.")
        if val < 0.0 or val > 15.0:
            raise ValidationError("Water intake must be between 0.0 and 15.0 liters.")
        return round(val, 2)

    @staticmethod
    def validate_exercise_frequency(freq_days: Any) -> int:
        """Validate weekly exercise frequency (0 - 7 days)."""
        try:
            val = int(freq_days)
        except (ValueError, TypeError):
            raise ValidationError("Exercise frequency must be an integer.")
        if val < 0 or val > 7:
            raise ValidationError("Exercise frequency must be between 0 and 7 days per week.")
        return val

    @staticmethod
    def validate_stress_level(stress: Any) -> int:
        """Validate stress rating on a scale from 1 (lowest) to 10 (highest)."""
        try:
            val = int(stress)
        except (ValueError, TypeError):
            raise ValidationError("Stress level must be an integer.")
        if val < 1 or val > 10:
            raise ValidationError("Stress level must be rated between 1 and 10.")
        return val

    @staticmethod
    def validate_date_string(date_str: str, field_name: str = "Date") -> str:
        """Validate ISO format date (YYYY-MM-DD)."""
        if not date_str:
            raise ValidationError(f"{field_name} is required.")
        try:
            parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            return parsed.isoformat()
        except ValueError:
            raise ValidationError(f"{field_name} must follow YYYY-MM-DD format.")

    @staticmethod
    def validate_future_date_string(date_str: str, field_name: str = "Appointment Date") -> str:
        """Validate that date is today or in the future."""
        iso_str = Validator.validate_date_string(date_str, field_name)
        parsed = datetime.strptime(iso_str, "%Y-%m-%d").date()
        if parsed < date.today():
            raise ValidationError(f"{field_name} cannot be in the past.")
        return iso_str

    @staticmethod
    def validate_time_string(time_str: str, field_name: str = "Time") -> str:
        """Validate HH:MM time format (24-hour)."""
        if not time_str:
            raise ValidationError(f"{field_name} is required.")
        try:
            parsed = datetime.strptime(time_str.strip(), "%H:%M").time()
            return parsed.strftime("%H:%M")
        except ValueError:
            raise ValidationError(f"{field_name} must follow HH:MM format (e.g., 14:30).")


def validate_payload(data: Dict[str, Any], rules: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Validate a dictionary of data against a mapping of field names to validator callables.
    Returns (cleaned_data, errors_dict).
    """
    cleaned: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    for field, validator_func in rules.items():
        val = data.get(field)
        try:
            cleaned[field] = validator_func(val)
        except ValidationError as e:
            errors[field] = e.message
        except Exception as ex:
            errors[field] = f"Invalid input: {str(ex)}"

    return cleaned, errors
