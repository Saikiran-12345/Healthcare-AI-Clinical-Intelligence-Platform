"""
Patient Views: Dashboard, Longitudinal Health Metrics, Medical History, and Symptom Logging.
"""

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from accounts.decorators import patient_required
from core.csv_storage import CsvStorage
from core.exceptions import ValidationError
from patients.forms import (
    HealthAssessmentForm,
    MedicalHistoryForm,
    SymptomEntryForm,
)
from patients.services import PatientService


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


@patient_required
def patient_dashboard_view(request):
    """Render comprehensive patient dashboard with health score, vitals, and predictions."""
    data = PatientService.get_patient_dashboard_data(request.user.id)
    return render(request, 'patients/dashboard.html', data)


@patient_required
def health_assessment_form_view(request):
    """Record a comprehensive physiological and lifestyle health profile."""
    patient = PatientService.get_patient_or_create(request.user.id)
    latest_profile = PatientService.get_latest_health_profile(patient["id"])

    initial_data = {}
    if latest_profile:
        initial_data = {
            'age': latest_profile.get('age', 35),
            'gender': latest_profile.get('gender', 'male'),
            'height_cm': latest_profile.get('height_cm', 175.0),
            'weight_kg': latest_profile.get('weight_kg', 72.0),
            'systolic_bp': latest_profile.get('systolic_bp', 120),
            'diastolic_bp': latest_profile.get('diastolic_bp', 80),
            'heart_rate': latest_profile.get('heart_rate', 72),
            'blood_glucose': latest_profile.get('blood_glucose', 95.0),
            'cholesterol': latest_profile.get('cholesterol', 185.0),
            'smoking_status': latest_profile.get('smoking_status', 'never'),
            'alcohol_consumption': latest_profile.get('alcohol_consumption', 'none'),
            'physical_activity_level': latest_profile.get('physical_activity_level', 'moderate'),
            'exercise_frequency_days': latest_profile.get('exercise_frequency_days', 3),
            'sleep_hours': latest_profile.get('sleep_hours', 7.5),
            'water_intake_liters': latest_profile.get('water_intake_liters', 2.5),
            'stress_level': latest_profile.get('stress_level', 4),
            'diet_type': latest_profile.get('diet_type', 'balanced'),
        }

    form = HealthAssessmentForm(request.POST or None, initial=initial_data)

    if request.method == 'POST' and form.is_valid():
        try:
            cleaned = form.cleaned_data
            # Extract family history flags
            fam_history = []
            if cleaned.get('fam_diabetes'): fam_history.append('Diabetes')
            if cleaned.get('fam_heart_disease'): fam_history.append('Heart Disease')
            if cleaned.get('fam_hypertension'): fam_history.append('Hypertension')
            if cleaned.get('fam_kidney_disease'): fam_history.append('Kidney Disease')
            cleaned['family_history'] = fam_history

            saved_profile = PatientService.save_health_profile(
                patient_id=patient["id"],
                user_id=request.user.id,
                profile_data=cleaned,
                ip_address=get_client_ip(request),
            )

            messages.success(request, f"Health assessment saved! Calculated BMI: {saved_profile['bmi']} ({saved_profile['bmi_category']}).")
            return redirect('/patients/dashboard/')

        except (ValidationError, Exception) as e:
            messages.error(request, str(e))

    context = {
        'form': form,
        'patient': patient,
        'latest_profile': latest_profile,
    }
    return render(request, 'patients/health_assessment.html', context)


@patient_required
def medical_history_list_view(request):
    """View and manage patient medical conditions history."""
    patient = PatientService.get_patient_or_create(request.user.id)
    records = PatientService.get_medical_history(patient["id"])
    form = MedicalHistoryForm()

    context = {
        'patient': patient,
        'records': records,
        'form': form,
    }
    return render(request, 'patients/medical_history.html', context)


@patient_required
def medical_history_create_view(request):
    """Add new medical condition entry."""
    if request.method == 'POST':
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            patient = PatientService.get_patient_or_create(request.user.id)
            data = form.cleaned_data
            try:
                PatientService.add_medical_history(
                    patient_id=patient["id"],
                    user_id=request.user.id,
                    condition=data["condition"],
                    diagnosis_date=data["diagnosis_date"],
                    status=data["status"],
                    severity=data["severity"],
                    notes=data.get("notes", ""),
                    ip_address=get_client_ip(request),
                )
                messages.success(request, f"Medical condition '{data['condition']}' recorded.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Invalid medical history submission.")

    return redirect('/patients/medical-history/')


@patient_required
def medical_history_delete_view(request, history_id):
    """Delete a medical history entry."""
    patient = PatientService.get_patient_or_create(request.user.id)
    try:
        PatientService.delete_medical_history(history_id, patient["id"])
        messages.info(request, "Medical record removed.")
    except Exception as e:
        messages.error(request, f"Could not remove record: {str(e)}")

    return redirect('/patients/medical-history/')


@patient_required
def symptom_log_view(request):
    """View logged symptoms and report new symptoms."""
    patient = PatientService.get_patient_or_create(request.user.id)
    symptoms = PatientService.get_patient_symptoms(patient["id"])
    form = SymptomEntryForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            PatientService.log_symptom_entry(
                patient_id=patient["id"],
                user_id=request.user.id,
                symptom_name=data["symptom_name"],
                category=data["category"],
                severity=data["severity"],
                duration_days=data["duration_days"],
                frequency=data["frequency"],
                notes=data.get("notes", ""),
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"Symptom '{data['symptom_name']}' logged successfully.")
            return redirect('/patients/symptoms/')
        except Exception as e:
            messages.error(request, str(e))

    context = {
        'patient': patient,
        'symptoms': symptoms,
        'form': form,
    }
    return render(request, 'patients/symptoms.html', context)


@patient_required
def export_patient_data_view(request):
    """Export patient health records in CSV format."""
    patient = PatientService.get_patient_or_create(request.user.id)
    profiles = PatientService.get_health_profile_history(patient["id"], limit=100)

    csv_content = CsvStorage.export_to_csv_string(profiles)
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="health_records_{patient["username"]}.csv"'
    return response
