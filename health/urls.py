"""
URL routing for Health Calculators and Clinical Indicators.
"""

from django.urls import path
from health import views

app_name = 'health'

urlpatterns = [
    path('calculators/', views.calculators_hub_view, name='hub'),
    path('calculators/bmi/', views.bmi_calculator_view, name='bmi'),
    path('calculators/bmr/', views.bmr_tdee_calculator_view, name='bmr'),
    path('calculators/bp/', views.blood_pressure_analyzer_view, name='bp'),
    path('calculators/heart-rate/', views.heart_rate_zones_view, name='heart_rate'),
    path('calculators/health-score/', views.health_score_analyzer_view, name='health_score'),
    path('api/calculate/', views.api_calculate_all, name='api_calculate'),
]
