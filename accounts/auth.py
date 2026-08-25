"""
Custom User Models and Authentication Utilities for Zero-DB JSON Architecture.
"""

import hashlib
import os
import secrets
from typing import Any, Dict, Optional
from core.exceptions import AuthenticationError, ValidationError
from core.storage import db, utc_now_iso


class AnonymousUser:
    """Represents an unauthenticated guest user."""
    id: Optional[str] = None
    username: str = ""
    email: str = ""
    role: str = "guest"
    full_name: str = ""
    is_authenticated: bool = False
    is_active: bool = False

    def __str__(self) -> str:
        return "AnonymousUser"


class JsonUser:
    """Represents an authenticated user backed by records in users.json."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.id = data.get("id", "")
        self.username = data.get("username", "")
        self.email = data.get("email", "")
        self.role = data.get("role", "patient")
        self.first_name = data.get("first_name", "")
        self.last_name = data.get("last_name", "")
        self.full_name = f"{self.first_name} {self.last_name}".strip() or self.username
        self.phone = data.get("phone", "")
        self.is_active = data.get("is_active", True)
        self.is_authenticated = True
        self.created_at = data.get("created_at", "")
        self.last_login = data.get("last_login", "")

    def __str__(self) -> str:
        return f"JsonUser({self.username}, role={self.role})"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


class PasswordHasher:
    """Secure PBKDF2-HMAC-SHA256 password hashing utility."""

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash a plaintext password with salt using PBKDF2."""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return f"pbkdf2_sha256$100000${salt}${pwd_hash}"

    @staticmethod
    def verify_password(password: str, encoded: str) -> bool:
        """Verify plaintext password against encoded hash."""
        try:
            algorithm, iterations_str, salt, expected_hash = encoded.split('$', 3)
            iterations = int(iterations_str)
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations
            ).hex()
            return secrets.compare_digest(computed_hash, expected_hash)
        except Exception:
            return False
