"""
Notification Center Views for Healthcare AI Application.
Provides notification listing, detail view, mark-as-read actions,
and a JSON API for AJAX notification badge updates.
"""

import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from accounts.decorators import login_required_json
from notifications.services import NotificationService


@login_required_json
def notification_center_view(request):
    """
    Main notification center displaying all notifications for the current user.
    Supports filtering by read status and notification type.
    """
    user_id = request.user.id
    filter_type = request.GET.get("filter", "all")  # all, unread, read

    if filter_type == "unread":
        notifications = NotificationService.get_user_notifications(
            user_id=user_id, include_read=False, limit=100,
        )
    elif filter_type == "read":
        all_notifs = NotificationService.get_user_notifications(
            user_id=user_id, include_read=True, limit=100,
        )
        notifications = [n for n in all_notifs if n.get("is_read")]
    else:
        notifications = NotificationService.get_user_notifications(
            user_id=user_id, include_read=True, limit=100,
        )

    stats = NotificationService.get_notification_stats(user_id)

    context = {
        "notifications": notifications,
        "stats": stats,
        "filter_type": filter_type,
    }
    return render(request, "notifications/center.html", context)


@login_required_json
def notification_detail_view(request, notification_id):
    """View a single notification and mark it as read."""
    notification = NotificationService.get_notification_by_id(notification_id)

    if not notification or notification.get("recipient_id") != request.user.id:
        return redirect("/notifications/")

    # Auto-mark as read when viewing
    if not notification.get("is_read"):
        NotificationService.mark_as_read(notification_id)
        notification["is_read"] = True

    context = {
        "notification": notification,
    }
    return render(request, "notifications/detail.html", context)


@login_required_json
def mark_read_view(request, notification_id):
    """Mark a specific notification as read and redirect back."""
    notification = NotificationService.get_notification_by_id(notification_id)
    if notification and notification.get("recipient_id") == request.user.id:
        NotificationService.mark_as_read(notification_id)

    # If notification has a link, redirect there
    link = notification.get("link", "") if notification else ""
    if link:
        return redirect(link)
    return redirect("/notifications/")


@login_required_json
def mark_all_read_view(request):
    """Mark all notifications as read for the current user."""
    NotificationService.mark_all_as_read(request.user.id)
    return redirect("/notifications/")


@login_required_json
def archive_notification_view(request, notification_id):
    """Archive (soft-delete) a notification."""
    notification = NotificationService.get_notification_by_id(notification_id)
    if notification and notification.get("recipient_id") == request.user.id:
        NotificationService.archive_notification(notification_id)
    return redirect("/notifications/")


@login_required_json
def delete_notification_view(request, notification_id):
    """Permanently delete a notification."""
    notification = NotificationService.get_notification_by_id(notification_id)
    if notification and notification.get("recipient_id") == request.user.id:
        NotificationService.delete_notification(notification_id)
    return redirect("/notifications/")


@login_required_json
def api_unread_count(request):
    """JSON API: Returns the unread notification count for nav badge updates."""
    count = NotificationService.get_unread_count(request.user.id)
    return JsonResponse({"unread_count": count})


@login_required_json
def api_recent_notifications(request):
    """JSON API: Returns recent unread notifications for dropdown preview."""
    notifications = NotificationService.get_unread_notifications(
        request.user.id, limit=5
    )
    items = []
    for n in notifications:
        items.append({
            "id": n.get("id", ""),
            "icon": n.get("icon", "🔔"),
            "title": n.get("title", ""),
            "message": n.get("message", "")[:120],
            "priority": n.get("priority", "normal"),
            "created_at": n.get("created_at", ""),
            "link": n.get("link", ""),
        })
    return JsonResponse({"notifications": items, "total_unread": len(notifications)})


@csrf_exempt
@login_required_json
def api_mark_read(request, notification_id):
    """JSON API: Mark a notification as read via AJAX."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    notification = NotificationService.get_notification_by_id(notification_id)
    if not notification or notification.get("recipient_id") != request.user.id:
        return JsonResponse({"error": "Not found"}, status=404)

    NotificationService.mark_as_read(notification_id)
    return JsonResponse({"status": "success", "notification_id": notification_id})
