"""
Machine Learning & Risk Prediction Views.
"""

import json
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import login_required_json
from core.exceptions import PredictionError
from core.storage import db
from ml.prediction.predictor import UnifiedPredictionEngine
from patients.services import PatientService


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


@login_required_json
def risk_assessment_view(request):
    """Interactive multi-disease risk assessment interface."""
    patient = None
    latest_profile = None
    if request.user.role == 'patient':
        patient = PatientService.get_patient_or_create(request.user.id)
        latest_profile = PatientService.get_latest_health_profile(patient["id"])

    selected_disease = request.GET.get('disease', 'Diabetes')
    result = None

    if request.method == 'POST':
        selected_disease = request.POST.get('disease_type', 'Diabetes')
        metrics = {
            'age': request.POST.get('age', 45),
            'gender': request.POST.get('gender', 'male'),
            'height_cm': request.POST.get('height_cm', 175),
            'weight_kg': request.POST.get('weight_kg', 75),
            'bmi': request.POST.get('bmi', 24.5),
            'systolic_bp': request.POST.get('systolic_bp', 120),
            'diastolic_bp': request.POST.get('diastolic_bp', 80),
            'blood_glucose': request.POST.get('blood_glucose', 95),
            'glucose': request.POST.get('blood_glucose', 95),
            'cholesterol': request.POST.get('cholesterol', 185),
            'heart_rate': request.POST.get('heart_rate', 72),
            'smoking': request.POST.get('smoking', 'never'),
            'alcohol': request.POST.get('alcohol', 'none'),
            'exercise_frequency': request.POST.get('exercise_frequency', 3),
            'water_intake': request.POST.get('water_intake', 2.5),
            'stress_level': request.POST.get('stress_level', 4),
            'family_history': [selected_disease] if request.POST.get('family_history') == 'yes' else [],
        }

        try:
            result = UnifiedPredictionEngine.predict_risk(
                disease_type=selected_disease,
                patient_id=patient["id"] if patient else None,
                health_metrics=metrics,
                actor_id=request.user.id,
                actor_role=request.user.role,
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"AI risk prediction generated for {selected_disease}: {result['risk_level']} Risk ({result['probability_pct']}%).")
        except PredictionError as e:
            messages.error(request, e.message)
        except Exception as ex:
            messages.error(request, f"Prediction failed: {str(ex)}")

    context = {
        'selected_disease': selected_disease,
        'patient': patient,
        'latest_profile': latest_profile,
        'result': result,
        'available_diseases': ['Diabetes', 'Heart Disease', 'Hypertension', 'Kidney Disease'],
    }
    return render(request, 'predictions/assess.html', context)


@login_required_json
def prediction_history_view(request):
    """View chronological risk assessment history."""
    if request.user.role == 'patient':
        patient = PatientService.get_patient_or_create(request.user.id)
        predictions = db.predictions.find_all(
            filters={"patient_id": patient["id"]},
            sort_by="created_at",
            reverse=True
        )
    else:
        predictions = db.predictions.find_all(sort_by="created_at", reverse=True, limit=50)

    context = {
        'predictions': predictions,
    }
    return render(request, 'predictions/history.html', context)


@login_required_json
def prediction_detail_view(request, prediction_id):
    """Detailed clinical report for an individual prediction run."""
    prediction = db.predictions.get_by_id(prediction_id)
    patient = db.patients.find_by_id(prediction.get("patient_id", ""))

    context = {
        'prediction': prediction,
        'patient': patient,
    }
    return render(request, 'predictions/detail.html', context)


def api_predict_disease(request):
    """JSON API endpoint for headless prediction calls."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        disease_type = data.get('disease_type', 'Diabetes')
        metrics = data.get('metrics', {})
        result = UnifiedPredictionEngine.predict_risk(disease_type=disease_type, health_metrics=metrics)
        return JsonResponse({'status': 'success', 'data': result})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
