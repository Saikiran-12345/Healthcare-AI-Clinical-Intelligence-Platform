"""
Appointment Views: Patient Booking, Doctor Schedule Management, Triage, and Time Slot API.
"""

from datetime import date
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from accounts.decorators import doctor_required, login_required_json, patient_required
from appointments.forms import AppointmentActionForm, AppointmentBookingForm
from appointments.services import AppointmentService
from core.exceptions import AppointmentConflictError, ValidationError
from core.storage import db
from doctors.services import DoctorService
from patients.services import PatientService


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


@patient_required
def patient_appointments_view(request):
    """List all upcoming and past appointments for current patient."""
    patient = PatientService.get_patient_or_create(request.user.id)
    appointments = AppointmentService.get_patient_appointments(patient["id"])

    context = {
        'patient': patient,
        'appointments': appointments,
    }
    return render(request, 'appointments/patient_appointments.html', context)


@patient_required
def book_appointment_view(request):
    """Book a new doctor appointment."""
    patient = PatientService.get_patient_or_create(request.user.id)
    form = AppointmentBookingForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cleaned = form.cleaned_data
        try:
            AppointmentService.book_appointment(
                patient_id=patient["id"],
                doctor_id=cleaned["doctor_id"],
                date_str=cleaned["appointment_date"],
                time_str=cleaned["appointment_time"],
                reason=cleaned["reason"],
                priority=cleaned.get("priority", "Standard"),
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"Appointment requested for {cleaned['appointment_date']} at {cleaned['appointment_time']}.")
            return redirect('/appointments/my-appointments/')
        except (AppointmentConflictError, ValidationError) as e:
            messages.error(request, e.message)
        except Exception as ex:
            messages.error(request, f"Booking error: {str(ex)}")

    context = {
        'form': form,
        'today_date': date.today().isoformat(),
    }
    return render(request, 'appointments/book_appointment.html', context)


@login_required_json
def cancel_appointment_view(request, appointment_id):
    """Cancel a booking by either patient, doctor, or admin."""
    try:
        AppointmentService.cancel_appointment(
            appointment_id=appointment_id,
            user_id=request.user.id,
            role=request.user.role,
            ip_address=get_client_ip(request),
        )
        messages.info(request, "Appointment has been cancelled.")
    except Exception as e:
        messages.error(request, f"Could not cancel appointment: {str(e)}")

    if request.user.role == 'doctor':
        return redirect('/appointments/doctor-schedule/')
    return redirect('/appointments/my-appointments/')


@doctor_required
def doctor_appointments_view(request):
    """Manage appointments schedule and pending triage requests for attending doctor."""
    doctor = DoctorService.get_doctor_or_create(request.user.id)
    status_filter = request.GET.get('status', 'ALL')

    appointments = AppointmentService.get_doctor_appointments(doctor["id"], status=status_filter)
    pending_count = len([a for a in appointments if a.get("status") == "Pending"])

    context = {
        'doctor': doctor,
        'appointments': appointments,
        'status_filter': status_filter,
        'pending_count': pending_count,
    }
    return render(request, 'appointments/doctor_appointments.html', context)


@doctor_required
def doctor_appointment_action_view(request, appointment_id):
    """Execute approval, rejection, or completion on an appointment."""
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('doctor_notes', '')
        doctor = DoctorService.get_doctor_or_create(request.user.id)

        try:
            if action == 'approve':
                AppointmentService.approve_appointment(
                    appointment_id=appointment_id,
                    doctor_id=doctor["id"],
                    notes=notes,
                    ip_address=get_client_ip(request),
                )
                messages.success(request, "Appointment approved and patient notified.")
            elif action == 'reject':
                AppointmentService.reject_appointment(
                    appointment_id=appointment_id,
                    doctor_id=doctor["id"],
                    reason=notes,
                    ip_address=get_client_ip(request),
                )
                messages.warning(request, "Appointment declined.")
            elif action == 'complete':
                AppointmentService.complete_appointment(
                    appointment_id=appointment_id,
                    doctor_id=doctor["id"],
                    notes=notes,
                    ip_address=get_client_ip(request),
                )
                messages.success(request, "Appointment marked as completed.")
        except Exception as e:
            messages.error(request, f"Action failed: {str(e)}")

    return redirect('/appointments/doctor-schedule/')


def api_available_slots(request):
    """API endpoint returning available time slots for a doctor on a specific date."""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'slots': []})

    try:
        slots = AppointmentService.get_doctor_available_slots(doctor_id, date_str)
        return JsonResponse({'slots': slots})
    except Exception:
        return JsonResponse({'slots': []})
