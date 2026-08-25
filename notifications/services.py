"""
Event-Driven Notification Service for Healthcare AI Application.
Dispatches and manages notifications for clinical events, appointment status changes,
high-risk prediction alerts, assessment reminders, and system announcements.
All notifications are persisted in local JSON storage.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from core.storage import db, utc_now_iso
from core.audit import AuditLogger, AuditAction


# ──────────────────────────────────────────────────
# Notification Type Constants
# ──────────────────────────────────────────────────

class NotificationType:
    """Enumeration of all supported notification categories."""
    # Appointment-related
    APPOINTMENT_REQUESTED = "APPOINTMENT_REQUESTED"
    APPOINTMENT_APPROVED = "APPOINTMENT_APPROVED"
    APPOINTMENT_REJECTED = "APPOINTMENT_REJECTED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_COMPLETED = "APPOINTMENT_COMPLETED"
    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"

    # Clinical & ML Predictions
    HIGH_RISK_ALERT = "HIGH_RISK_ALERT"
    PREDICTION_READY = "PREDICTION_READY"
    RISK_LEVEL_CHANGE = "RISK_LEVEL_CHANGE"

    # Health Profile
    HEALTH_ASSESSMENT_DUE = "HEALTH_ASSESSMENT_DUE"
    HEALTH_SCORE_DROP = "HEALTH_SCORE_DROP"
    VITAL_ABNORMALITY = "VITAL_ABNORMALITY"

    # Recommendations
    NEW_RECOMMENDATIONS = "NEW_RECOMMENDATIONS"
    RECOMMENDATION_REMINDER = "RECOMMENDATION_REMINDER"

    # NLP / Symptom Analysis
    SYMPTOM_ANALYSIS_COMPLETE = "SYMPTOM_ANALYSIS_COMPLETE"
    URGENT_SYMPTOM_DETECTED = "URGENT_SYMPTOM_DETECTED"

    # Account & System
    WELCOME = "WELCOME"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    SYSTEM_ANNOUNCEMENT = "SYSTEM_ANNOUNCEMENT"
    ACCOUNT_ACTIVITY = "ACCOUNT_ACTIVITY"


class NotificationPriority:
    """Priority levels that determine display order and visual emphasis."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

    PRIORITY_ORDER = {"critical": 4, "high": 3, "normal": 2, "low": 1}


# ──────────────────────────────────────────────────
# Icon & Color Mapping for Frontend Rendering
# ──────────────────────────────────────────────────

NOTIFICATION_DISPLAY = {
    NotificationType.APPOINTMENT_REQUESTED: {"icon": "📅", "color": "#3498db", "label": "Appointment Request"},
    NotificationType.APPOINTMENT_APPROVED: {"icon": "✅", "color": "#27ae60", "label": "Appointment Confirmed"},
    NotificationType.APPOINTMENT_REJECTED: {"icon": "❌", "color": "#e74c3c", "label": "Appointment Declined"},
    NotificationType.APPOINTMENT_CANCELLED: {"icon": "🚫", "color": "#e67e22", "label": "Appointment Cancelled"},
    NotificationType.APPOINTMENT_COMPLETED: {"icon": "🏥", "color": "#2ecc71", "label": "Visit Complete"},
    NotificationType.APPOINTMENT_REMINDER: {"icon": "⏰", "color": "#f39c12", "label": "Appointment Reminder"},
    NotificationType.HIGH_RISK_ALERT: {"icon": "🚨", "color": "#e74c3c", "label": "High-Risk Alert"},
    NotificationType.PREDICTION_READY: {"icon": "🤖", "color": "#9b59b6", "label": "Prediction Ready"},
    NotificationType.RISK_LEVEL_CHANGE: {"icon": "📈", "color": "#e67e22", "label": "Risk Level Changed"},
    NotificationType.HEALTH_ASSESSMENT_DUE: {"icon": "📋", "color": "#3498db", "label": "Assessment Due"},
    NotificationType.HEALTH_SCORE_DROP: {"icon": "📉", "color": "#e74c3c", "label": "Health Score Alert"},
    NotificationType.VITAL_ABNORMALITY: {"icon": "💓", "color": "#e74c3c", "label": "Vital Sign Alert"},
    NotificationType.NEW_RECOMMENDATIONS: {"icon": "💡", "color": "#2ecc71", "label": "New Recommendations"},
    NotificationType.RECOMMENDATION_REMINDER: {"icon": "🔔", "color": "#f1c40f", "label": "Recommendation Reminder"},
    NotificationType.SYMPTOM_ANALYSIS_COMPLETE: {"icon": "🔬", "color": "#9b59b6", "label": "Analysis Complete"},
    NotificationType.URGENT_SYMPTOM_DETECTED: {"icon": "⚠️", "color": "#e74c3c", "label": "Urgent Symptoms"},
    NotificationType.WELCOME: {"icon": "👋", "color": "#2ecc71", "label": "Welcome"},
    NotificationType.PASSWORD_CHANGED: {"icon": "🔒", "color": "#3498db", "label": "Security Update"},
    NotificationType.SYSTEM_ANNOUNCEMENT: {"icon": "📢", "color": "#34495e", "label": "System Announcement"},
    NotificationType.ACCOUNT_ACTIVITY: {"icon": "👤", "color": "#7f8c8d", "label": "Account Activity"},
}


# ──────────────────────────────────────────────────
# Notification Service
# ──────────────────────────────────────────────────

class NotificationService:
    """
    Central notification service managing creation, delivery, read-status tracking,
    and aggregation of user notifications. All data persisted via JsonTable.
    """

    # ─── Creation ─────────────────────────────────

    @staticmethod
    def create(
        recipient_id: str,
        notification_type: str,
        title: str,
        message: str,
        priority: str = NotificationPriority.NORMAL,
        sender_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        link: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create and persist a new notification for a user.

        Args:
            recipient_id: Target user's UUID.
            notification_type: One of NotificationType constants.
            title: Short notification heading.
            message: Detailed notification body.
            priority: One of NotificationPriority constants.
            sender_id: Optional originator user ID.
            sender_name: Optional originator display name.
            link: Optional URL the user should navigate to.
            metadata: Optional dict of extra contextual data.

        Returns:
            The created notification record dict.
        """
        display = NOTIFICATION_DISPLAY.get(notification_type, {"icon": "🔔", "color": "#7f8c8d", "label": "Notification"})

        record = {
            "recipient_id": recipient_id,
            "type": notification_type,
            "title": title,
            "message": message,
            "priority": priority,
            "priority_order": NotificationPriority.PRIORITY_ORDER.get(priority, 2),
            "sender_id": sender_id or "system",
            "sender_name": sender_name or "HealthAI System",
            "link": link or "",
            "metadata": metadata or {},
            "is_read": False,
            "is_archived": False,
            "icon": display["icon"],
            "color": display["color"],
            "label": display["label"],
            "read_at": None,
        }

        return db.notifications.insert(record)

    # ─── Bulk Creation ────────────────────────────

    @staticmethod
    def notify_multiple(
        recipient_ids: List[str],
        notification_type: str,
        title: str,
        message: str,
        priority: str = NotificationPriority.NORMAL,
        sender_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        link: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Send identical notification to multiple recipients."""
        results = []
        for rid in recipient_ids:
            notif = NotificationService.create(
                recipient_id=rid,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                sender_id=sender_id,
                sender_name=sender_name,
                link=link,
                metadata=metadata,
            )
            results.append(notif)
        return results

    # ─── Retrieval ────────────────────────────────

    @staticmethod
    def get_user_notifications(
        user_id: str,
        include_read: bool = True,
        include_archived: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve notifications for a user, ordered by priority (desc) then creation time (desc).
        """
        def _filter(rec: Dict[str, Any]) -> bool:
            if rec.get("recipient_id") != user_id:
                return False
            if not include_read and rec.get("is_read"):
                return False
            if not include_archived and rec.get("is_archived"):
                return False
            if notification_type and rec.get("type") != notification_type:
                return False
            return True

        notifications = db.notifications.find_all(
            filter_func=_filter,
            sort_by="created_at",
            reverse=True,
            limit=limit * 2,  # Fetch extra for priority sorting
        )

        # Secondary sort by priority_order descending
        notifications.sort(
            key=lambda n: (
                -n.get("priority_order", 2),
                n.get("created_at", ""),
            ),
            reverse=False,
        )
        # Reverse so highest priority + latest first
        notifications.sort(
            key=lambda n: (-n.get("priority_order", 2), ""),
        )

        return notifications[:limit]

    @staticmethod
    def get_unread_notifications(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get only unread notifications for badge counts and dropdowns."""
        return NotificationService.get_user_notifications(
            user_id=user_id,
            include_read=False,
            include_archived=False,
            limit=limit,
        )

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Fast count of unread notifications for a user (used in nav badge)."""
        return len(db.notifications.find_all(
            filters={"recipient_id": user_id, "is_read": False}
        ))

    @staticmethod
    def get_notification_by_id(notification_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single notification by its ID."""
        return db.notifications.find_by_id(notification_id)

    # ─── Status Management ────────────────────────

    @staticmethod
    def mark_as_read(notification_id: str) -> Dict[str, Any]:
        """Mark a single notification as read and record the timestamp."""
        return db.notifications.update(notification_id, {
            "is_read": True,
            "read_at": utc_now_iso(),
        })

    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        """Mark all unread notifications for a user as read. Returns count updated."""
        return db.notifications.update_where(
            filters={"recipient_id": user_id, "is_read": False},
            updates={"is_read": True, "read_at": utc_now_iso()},
        )

    @staticmethod
    def archive_notification(notification_id: str) -> Dict[str, Any]:
        """Archive (soft-delete) a notification."""
        return db.notifications.update(notification_id, {
            "is_archived": True,
            "is_read": True,
            "read_at": utc_now_iso(),
        })

    @staticmethod
    def delete_notification(notification_id: str) -> bool:
        """Permanently remove a notification."""
        return db.notifications.delete(notification_id)

    # ─── Aggregation & Statistics ─────────────────

    @staticmethod
    def get_notification_stats(user_id: str) -> Dict[str, Any]:
        """
        Compute aggregate notification statistics for a user.
        Returns counts grouped by type, priority, and read-status.
        """
        all_notifs = db.notifications.find_all(
            filters={"recipient_id": user_id}
        )

        total = len(all_notifs)
        unread = sum(1 for n in all_notifs if not n.get("is_read"))
        archived = sum(1 for n in all_notifs if n.get("is_archived"))

        by_type: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}

        for n in all_notifs:
            ntype = n.get("type", "UNKNOWN")
            npri = n.get("priority", "normal")
            by_type[ntype] = by_type.get(ntype, 0) + 1
            by_priority[npri] = by_priority.get(npri, 0) + 1

        critical_unread = sum(
            1 for n in all_notifs
            if not n.get("is_read") and n.get("priority") == "critical"
        )

        return {
            "total": total,
            "unread": unread,
            "read": total - unread,
            "archived": archived,
            "critical_unread": critical_unread,
            "by_type": by_type,
            "by_priority": by_priority,
        }

    # ─── Convenience Event Dispatchers ────────────

    @staticmethod
    def send_welcome(user_id: str, user_name: str) -> Dict[str, Any]:
        """Send a welcome notification to a newly registered user."""
        return NotificationService.create(
            recipient_id=user_id,
            notification_type=NotificationType.WELCOME,
            title=f"Welcome to HealthAI, {user_name}!",
            message=(
                "Thank you for joining our AI-powered healthcare platform. "
                "Start by completing your health profile assessment to receive "
                "personalized predictions and recommendations."
            ),
            priority=NotificationPriority.NORMAL,
            link="/patients/profile/",
        )

    @staticmethod
    def send_high_risk_alert(
        patient_id: str,
        disease: str,
        risk_level: str,
        probability: float,
        doctor_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send high-risk alerts to patient and their assigned doctors.
        """
        results = []

        # Notify the patient
        patient_notif = NotificationService.create(
            recipient_id=patient_id,
            notification_type=NotificationType.HIGH_RISK_ALERT,
            title=f"High Risk Detected: {disease}",
            message=(
                f"Your AI risk assessment indicates {risk_level} risk for {disease} "
                f"(probability: {probability:.1f}%). Please consult a healthcare "
                f"professional for further evaluation."
            ),
            priority=NotificationPriority.CRITICAL,
            link="/predictions/history/",
            metadata={"disease": disease, "risk_level": risk_level, "probability": probability},
        )
        results.append(patient_notif)

        # Notify assigned doctors
        if doctor_ids:
            for doc_id in doctor_ids:
                doc_notif = NotificationService.create(
                    recipient_id=doc_id,
                    notification_type=NotificationType.HIGH_RISK_ALERT,
                    title=f"Patient High-Risk Alert: {disease}",
                    message=(
                        f"A patient has been flagged as {risk_level} risk for {disease} "
                        f"(probability: {probability:.1f}%). Clinical review recommended."
                    ),
                    priority=NotificationPriority.HIGH,
                    link="/doctors/risk-monitoring/",
                    metadata={"disease": disease, "risk_level": risk_level, "probability": probability, "patient_id": patient_id},
                )
                results.append(doc_notif)

        return results

    @staticmethod
    def send_appointment_notification(
        recipient_id: str,
        notification_type: str,
        appointment_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send appointment-related notification."""
        status_messages = {
            NotificationType.APPOINTMENT_REQUESTED: "A new appointment request has been submitted.",
            NotificationType.APPOINTMENT_APPROVED: "Your appointment has been approved and confirmed.",
            NotificationType.APPOINTMENT_REJECTED: "Your appointment request has been declined.",
            NotificationType.APPOINTMENT_CANCELLED: "An appointment has been cancelled.",
            NotificationType.APPOINTMENT_COMPLETED: "Your appointment visit has been marked as complete.",
            NotificationType.APPOINTMENT_REMINDER: "You have an upcoming appointment scheduled.",
        }

        display = NOTIFICATION_DISPLAY.get(notification_type, {})
        title = display.get("label", "Appointment Update")
        message = status_messages.get(notification_type, "Appointment status updated.")

        date_str = appointment_details.get("date", "")
        time_str = appointment_details.get("time_slot", "")
        if date_str:
            message += f" Date: {date_str}"
        if time_str:
            message += f" | Time: {time_str}"

        priority = NotificationPriority.NORMAL
        if notification_type in (NotificationType.APPOINTMENT_REJECTED, NotificationType.APPOINTMENT_CANCELLED):
            priority = NotificationPriority.HIGH

        return NotificationService.create(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            link="/appointments/",
            metadata=appointment_details,
        )

    @staticmethod
    def send_prediction_ready(patient_id: str, disease: str, risk_level: str) -> Dict[str, Any]:
        """Notify patient that a new ML prediction result is available."""
        return NotificationService.create(
            recipient_id=patient_id,
            notification_type=NotificationType.PREDICTION_READY,
            title=f"New Prediction Result: {disease}",
            message=(
                f"Your AI risk prediction for {disease} is ready. "
                f"Result: {risk_level} Risk. View the detailed report for "
                f"personalized recommendations."
            ),
            priority=NotificationPriority.NORMAL if risk_level == "LOW" else NotificationPriority.HIGH,
            link="/predictions/history/",
            metadata={"disease": disease, "risk_level": risk_level},
        )

    @staticmethod
    def send_new_recommendations(patient_id: str, count: int) -> Dict[str, Any]:
        """Notify patient that new health recommendations have been generated."""
        return NotificationService.create(
            recipient_id=patient_id,
            notification_type=NotificationType.NEW_RECOMMENDATIONS,
            title=f"{count} New Health Recommendations",
            message=(
                f"Based on your latest health assessment, {count} personalized "
                f"recommendations have been generated across nutrition, exercise, "
                f"sleep, and lifestyle categories."
            ),
            priority=NotificationPriority.NORMAL,
            link="/recommendations/",
        )

    @staticmethod
    def send_symptom_analysis_complete(patient_id: str, urgency: str, top_condition: str) -> Dict[str, Any]:
        """Notify patient that NLP symptom analysis is complete."""
        ntype = NotificationType.SYMPTOM_ANALYSIS_COMPLETE
        priority = NotificationPriority.NORMAL

        if urgency in ("URGENT", "EMERGENCY"):
            ntype = NotificationType.URGENT_SYMPTOM_DETECTED
            priority = NotificationPriority.CRITICAL

        return NotificationService.create(
            recipient_id=patient_id,
            notification_type=ntype,
            title=f"Symptom Analysis Complete — {urgency}",
            message=(
                f"Your symptom analysis has been completed. Top correlated condition: "
                f"{top_condition}. Urgency level: {urgency}. "
                f"Please review the full report and consult a healthcare professional if needed."
            ),
            priority=priority,
            link="/nlp/symptom-checker/",
            metadata={"urgency": urgency, "top_condition": top_condition},
        )

    @staticmethod
    def send_system_announcement(title: str, message: str, recipient_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Broadcast a system announcement to specified users or all users.
        """
        if recipient_ids is None:
            all_users = db.users.find_all()
            recipient_ids = [u["id"] for u in all_users]

        return NotificationService.notify_multiple(
            recipient_ids=recipient_ids,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title=title,
            message=message,
            priority=NotificationPriority.LOW,
        )

    # ─── Cleanup & Maintenance ────────────────────

    @staticmethod
    def cleanup_old_notifications(days: int = 90) -> int:
        """
        Remove notifications older than the specified number of days.
        Returns count of deleted notifications.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        def _is_old(rec: Dict[str, Any]) -> bool:
            created = rec.get("created_at", "")
            return bool(created and created < cutoff)

        old_records = db.notifications.find_all(filter_func=_is_old)
        deleted = 0
        for rec in old_records:
            try:
                db.notifications.delete(rec["id"])
                deleted += 1
            except Exception:
                continue
        return deleted

    @staticmethod
    def get_recent_activity(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get notifications from the last N hours for activity feed."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        def _is_recent(rec: Dict[str, Any]) -> bool:
            if rec.get("recipient_id") != user_id:
                return False
            created = rec.get("created_at", "")
            return bool(created and created >= cutoff)

        return db.notifications.find_all(
            filter_func=_is_recent,
            sort_by="created_at",
            reverse=True,
        )
