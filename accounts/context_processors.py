"""
Context processors for authentication state and user notifications.
"""

from typing import Any, Dict


def auth_context(request) -> Dict[str, Any]:
    """Provide authentication context to templates without relying on Django DB auth."""
    user = getattr(request, 'user', None)
    unread_notif_count = 0

    if user and user.is_authenticated:
        try:
            from core.storage import db
            unread_notif_count = db.notifications.count(filters={"user_id": user.id, "read": False})
        except Exception:
            unread_notif_count = 0

    return {
        'user': user,
        'unread_notif_count': unread_notif_count,
    }
