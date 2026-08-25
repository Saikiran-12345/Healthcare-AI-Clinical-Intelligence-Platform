"""
Health Calculator & Physiological Indicator Views.
Provides dedicated interactive web views and real-time JSON API endpoints for clinical calculations.
"""

import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from health.calculators import HealthCalculators


def calculators_hub_view(request):
    """Render main directory hub for all available health calculators."""
    return render(request, 'health/calculators_hub.html')


def bmi_calculator_view(request):
    """Interactive Body Mass Index (BMI) & ideal weight calculator."""
    result = None
    height = request.GET.get('height', '175')
    weight = request.GET.get('weight', '70')

    try:
        h = float(height)
        w = float(weight)
        if h > 0 and w > 0:
            result = HealthCalculators.calculate_bmi(h, w)
    except Exception:
        result = None

    context = {
        'height': height,
        'weight': weight,
        'result': result,
    }
    return render(request, 'health/bmi_calculator.html', context)


def bmr_tdee_calculator_view(request):
    """Interactive Basal Metabolic Rate (BMR) & TDEE Calorie Calculator."""
    result = None
    height = request.GET.get('height', '175')
    weight = request.GET.get('weight', '70')
    age = request.GET.get('age', '30')
    gender = request.GET.get('gender', 'male')
    activity = request.GET.get('activity', 'moderate')

    try:
        h = float(height)
        w = float(weight)
        a = int(age)
        bmr_res = HealthCalculators.calculate_bmr(h, w, a, gender)
        tdee_res = HealthCalculators.calculate_tdee(bmr_res['bmr_calories'], activity)
        result = {
            'bmr': bmr_res,
            'tdee': tdee_res,
        }
    except Exception:
        result = None

    context = {
        'height': height,
        'weight': weight,
        'age': age,
        'gender': gender,
        'activity': activity,
        'result': result,
    }
    return render(request, 'health/bmr_calculator.html', context)


def blood_pressure_analyzer_view(request):
    """Interactive Blood Pressure (AHA 2017) & MAP Calculator."""
    result = None
    systolic = request.GET.get('systolic', '120')
    diastolic = request.GET.get('diastolic', '80')

    try:
        sys_val = int(systolic)
        dia_val = int(diastolic)
        if sys_val > dia_val:
            result = HealthCalculators.classify_blood_pressure(sys_val, dia_val)
    except Exception:
        result = None

    context = {
        'systolic': systolic,
        'diastolic': diastolic,
        'result': result,
    }
    return render(request, 'health/bp_analyzer.html', context)


def heart_rate_zones_view(request):
    """Resting heart rate evaluation and aerobic training zones."""
    result = None
    resting_hr = request.GET.get('resting_hr', '72')
    age = request.GET.get('age', '30')

    try:
        r_hr = int(resting_hr)
        a = int(age)
        result = HealthCalculators.classify_heart_rate(r_hr, a)
    except Exception:
        result = None

    context = {
        'resting_hr': resting_hr,
        'age': age,
        'result': result,
    }
    return render(request, 'health/heart_rate_zones.html', context)


def health_score_analyzer_view(request):
    """Holistic Multi-Dimensional Health Score Analyzer."""
    result = None
    if request.method == 'POST' or request.GET:
        params = request.POST if request.method == 'POST' else request.GET
        if params:
            try:
                result = HealthCalculators.calculate_composite_health_score(params)
            except Exception:
                result = None

    context = {
        'result': result,
    }
    return render(request, 'health/health_score_analyzer.html', context)


def api_calculate_all(request):
    """JSON API endpoint allowing client-side JS to execute composite calculations dynamically."""
    try:
        payload = json.loads(request.body) if request.body else request.GET.dict()
        result = HealthCalculators.calculate_composite_health_score(payload)
        return JsonResponse({'status': 'success', 'data': result})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
