"""
Doctor Views: Clinical Dashboard, Patient Roster, Longitudinal Chart, and High-Risk Triage.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from accounts.decorators import doctor_required
from core.exceptions import ValidationError
from doctors.forms import ClinicalNoteForm, DoctorProfileForm, PatientSearchForm
from doctors.services import DoctorService


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


@doctor_required
def doctor_dashboard_view(request):
    """Render clinical doctor portal overview and risk distributions."""
    stats = DoctorService.get_doctor_dashboard_stats(request.user.id)
    return render(request, 'doctors/dashboard.html', stats)


@doctor_required
def patient_roster_view(request):
    """Display searchable, filterable list of all registered patients."""
    search_form = PatientSearchForm(request.GET or None)
    search_query = request.GET.get('q', '').strip()
    risk_filter = request.GET.get('risk_level', 'ALL')

    doctor = DoctorService.get_doctor_or_create(request.user.id)
    roster = DoctorService.get_patient_roster(
        search_query=search_query,
        risk_filter=risk_filter,
        doctor_id=doctor["id"]
    )

    context = {
        'roster': roster,
        'search_form': search_form,
        'total_count': len(roster),
    }
    return render(request, 'doctors/patient_roster.html', context)


@doctor_required
def patient_detail_chart_view(request, patient_id):
    """Render comprehensive longitudinal chart and health records for a patient."""
    chart_data = DoctorService.get_patient_clinical_chart(patient_id)
    note_form = ClinicalNoteForm()

    context = {
        'chart': chart_data,
        'note_form': note_form,
    }
    return render(request, 'doctors/patient_detail.html', context)


@doctor_required
def add_clinical_note_view(request, patient_id):
    """Add a structured SOAP clinical observation note to a patient's chart."""
    if request.method == 'POST':
        form = ClinicalNoteForm(request.POST)
        if form.is_valid():
            doctor = DoctorService.get_doctor_or_create(request.user.id)
            cleaned = form.cleaned_data
            try:
                DoctorService.add_clinical_note(
                    doctor_id=doctor["id"],
                    doctor_name=doctor["full_name"],
                    patient_id=patient_id,
                    subjective=cleaned.get("subjective", ""),
                    assessment=cleaned["assessment"],
                    plan=cleaned.get("plan", ""),
                    prescriptions=cleaned.get("prescriptions", ""),
                    follow_up_date=cleaned.get("follow_up_date"),
                    ip_address=get_client_ip(request),
                )
                messages.success(request, "Clinical note successfully appended to patient chart.")
            except ValidationError as e:
                messages.error(request, e.message)
            except Exception as ex:
                messages.error(request, f"Error saving clinical note: {str(ex)}")
        else:
            messages.error(request, "Please provide valid clinical assessment details.")

    return redirect(f"/doctors/patients/{patient_id}/")


@doctor_required
def high_risk_monitoring_view(request):
    """Surveillance board for patients flagged with HIGH risk predictions."""
    high_risk_patients = DoctorService.get_high_risk_patients()
    context = {
        'high_risk_patients': high_risk_patients,
        'count': len(high_risk_patients),
    }
    return render(request, 'doctors/risk_monitoring.html', context)


@doctor_required
def doctor_profile_view(request):
    """Manage doctor clinical credentials and availability."""
    doctor = DoctorService.get_doctor_or_create(request.user.id)

    initial_data = {
        'specialization': doctor.get('specialization', ''),
        'department': doctor.get('department', ''),
        'license_number': doctor.get('license_number', ''),
        'consultation_hours': doctor.get('consultation_hours', '09:00 - 17:00'),
        'is_available': doctor.get('is_available', True),
    }

    form = DoctorProfileForm(request.POST or None, initial=initial_data)
    if request.method == 'POST' and form.is_valid():
        from core.storage import db
        db.doctors.update(doctor["id"], form.cleaned_data)
        messages.success(request, "Clinical profile updated.")
        return redirect('/doctors/profile/')

    context = {
        'doctor': doctor,
        'form': form,
    }
    return render(request, 'doctors/profile.html', context)
