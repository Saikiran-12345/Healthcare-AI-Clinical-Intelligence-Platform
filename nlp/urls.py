from django.urls import path
from . import views

app_name = 'nlp'

urlpatterns = [
    path('checker/', views.symptom_checker_view, name='symptom_checker'),
    path('history/', views.symptom_history_view, name='symptom_history'),
    path('detail/<str:analysis_id>/', views.symptom_detail_view, name='symptom_detail'),
    path('api/analyze/', views.api_analyze_symptoms, name='api_analyze'),
]
