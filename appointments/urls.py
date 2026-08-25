"""
URL routing for Appointments scheduling and consultation triage.
"""

from django.urls import path
from appointments import views

app_name = 'appointments'

urlpatterns = [
    path('my-appointments/', views.patient_appointments_view, name='patient_appointments'),
    path('book/', views.book_appointment_view, name='book'),
    path('cancel/<str:appointment_id>/', views.cancel_appointment_view, name='cancel'),
    path('doctor-schedule/', views.doctor_appointments_view, name='doctor_schedule'),
    path('action/<str:appointment_id>/', views.doctor_appointment_action_view, name='action'),
    path('api/slots/', views.api_available_slots, name='api_slots'),
]
