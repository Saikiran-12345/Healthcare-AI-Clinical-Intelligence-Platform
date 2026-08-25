"""
URL routing for Machine Learning models and risk prediction reports.
"""

from django.urls import path
from ml import views

app_name = 'ml'

urlpatterns = [
    path('assess/', views.risk_assessment_view, name='assess'),
    path('history/', views.prediction_history_view, name='history'),
    path('detail/<str:prediction_id>/', views.prediction_detail_view, name='detail'),
    path('api/predict/', views.api_predict_disease, name='api_predict'),
]
