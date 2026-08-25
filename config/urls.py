"""
Master URL Configuration for Healthcare AI System.
Routes endpoints to accounts, patients, doctors, health tools, appointments, ML predictions,
NLP symptom analysis, recommendations, notifications, analytics, and administration.
"""

from django.urls import path, include
from core.api import patient_summary_api
from core.views import home_view

urlpatterns = [
    # Core Landing
    path('', home_view, name='home'),
    path('api/patient/summary/', patient_summary_api, name='patient_summary_api'),

    # Modular App Routers
    path('accounts/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('health/', include('health.urls')),
    path('appointments/', include('appointments.urls')),
    path('predictions/', include('ml.urls')),
    path('nlp/', include('nlp.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('notifications/', include('notifications.urls')),
    path('analytics/', include('analytics.urls')),
    path('admin-panel/', include('admin_panel.urls')),
]
