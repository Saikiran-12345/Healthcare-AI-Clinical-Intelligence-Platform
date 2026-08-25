"""Notifications URL routing."""
from django.urls import path
from notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_center_view, name='center'),
    path('<str:notification_id>/', views.notification_detail_view, name='detail'),
    path('<str:notification_id>/read/', views.mark_read_view, name='mark_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('<str:notification_id>/archive/', views.archive_notification_view, name='archive'),
    path('<str:notification_id>/delete/', views.delete_notification_view, name='delete'),
    # JSON APIs
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/recent/', views.api_recent_notifications, name='api_recent'),
    path('api/<str:notification_id>/read/', views.api_mark_read, name='api_mark_read'),
]
