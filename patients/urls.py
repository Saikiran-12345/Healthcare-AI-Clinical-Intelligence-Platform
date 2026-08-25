"""
URL patterns for Patient portal and health records management.
"""

from django.urls import path
from patients import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.patient_dashboard_view, name='dashboard'),
    path('profile/', views.patient_dashboard_view, name='profile'),
    path('assessment/', views.health_assessment_form_view, name='assessment'),
    path('medical-history/', views.medical_history_list_view, name='medical_history'),
    path('medical-history/add/', views.medical_history_create_view, name='medical_history_add'),
    path('medical-history/delete/<str:history_id>/', views.medical_history_delete_view, name='medical_history_delete'),
    path('symptoms/', views.symptom_log_view, name='symptoms'),
    path('export/', views.export_patient_data_view, name='export'),
]
