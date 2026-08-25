"""
Comprehensive Audit Logging System for Healthcare AI Application.
Tracks security events, authentication lifecycle, clinical data changes, ML predictions,
administrative actions, and authorization failures.
"""

from typing import Any, Dict, Optional
from core.storage import db, utc_now_iso


class AuditAction:
    # Authentication
    LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    LOGOUT = "AUTH_LOGOUT"
    REGISTER = "AUTH_REGISTER"
    PASSWORD_CHANGE = "AUTH_PASSWORD_CHANGE"

    # Patient & Health Operations
    PROFILE_UPDATE = "PATIENT_PROFILE_UPDATE"
    HEALTH_ASSESSMENT_SUBMIT = "HEALTH_ASSESSMENT_SUBMIT"
    MEDICAL_HISTORY_ADD = "MEDICAL_HISTORY_ADD"
    SYMPTOMS_LOGGED = "SYMPTOMS_LOGGED"

    # ML & Predictions
    PREDICTION_GENERATED = "ML_PREDICTION_GENERATED"
    MODEL_RETRAINED = "ML_MODEL_RETRAINED"
    RECOMMENDATION_VIEWED = "RECOMMENDATION_VIEWED"

    # Appointments
    APPOINTMENT_REQUESTED = "APPOINTMENT_REQUESTED"
    APPOINTMENT_APPROVED = "APPOINTMENT_APPROVED"
    APPOINTMENT_REJECTED = "APPOINTMENT_REJECTED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_COMPLETED = "APPOINTMENT_COMPLETED"

    # Clinical & Doctor Actions
    DOCTOR_NOTE_ADDED = "DOCTOR_NOTE_ADDED"
    PATIENT_REVIEWED = "PATIENT_REVIEWED"

    # Admin & Security
    USER_STATUS_TOGGLED = "ADMIN_USER_STATUS_TOGGLED"
    DATA_EXPORTED = "ADMIN_DATA_EXPORTED"
    UNAUTHORIZED_ACCESS = "SECURITY_UNAUTHORIZED_ACCESS"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class AuditLogger:
    """Central audit service logging all operational events to local JSON."""

    @staticmethod
    def log(
        action: str,
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        actor_role: Optional[str] = None,
        target_entity: Optional[str] = None,
        target_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an immutable audit log entry."""
        entry = {
            "action": action,
            "actor_id": actor_id or "anonymous",
            "actor_name": actor_name or "Anonymous",
            "actor_role": actor_role or "guest",
            "target_entity": target_entity or "",
            "target_id": target_id or "",
            "ip_address": ip_address or "127.0.0.1",
            "status": status,
            "details": details or {},
            "timestamp": utc_now_iso(),
        }

        try:
            return db.audit_logs.insert(entry)
        except Exception:
            # Fallback to avoid breaking application if logging fails
            return entry

    @staticmethod
    def get_recent_logs(limit: int = 50, action_filter: Optional[str] = None) -> list:
        """Fetch latest audit log entries sorted by timestamp descending."""
        filters = {"action": action_filter} if action_filter else None
        return db.audit_logs.find_all(
            filters=filters,
            sort_by="timestamp",
            reverse=True,
            limit=limit
        )

    @staticmethod
    def get_user_activity(user_id: str, limit: int = 20) -> list:
        """Fetch activity history for a specific user."""
        return db.audit_logs.find_all(
            filters={"actor_id": user_id},
            sort_by="timestamp",
            reverse=True,
            limit=limit
        )
