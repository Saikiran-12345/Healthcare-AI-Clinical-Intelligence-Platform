"""
URL routing for Doctor clinical portal and risk monitoring.
"""

from django.urls import path
from doctors import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.doctor_dashboard_view, name='dashboard'),
    path('patients/', views.patient_roster_view, name='patient_roster'),
    path('patients/<str:patient_id>/', views.patient_detail_chart_view, name='patient_detail'),
    path('patients/<str:patient_id>/add-note/', views.add_clinical_note_view, name='add_note'),
    path('risk-monitoring/', views.high_risk_monitoring_view, name='risk_monitoring'),
    path('profile/', views.doctor_profile_view, name='profile'),
]
