"""Read-only JSON endpoints for patient-facing integrations."""

from typing import Any, Dict

from django.http import JsonResponse

from accounts.decorators import patient_required
from patients.services import PatientService


def _profile_summary(profile: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Return the stable, non-sensitive profile fields used by client apps."""
    if not profile:
        return None
    fields = (
        "bmi", "bmi_category", "systolic_bp", "diastolic_bp",
        "heart_rate", "blood_glucose", "cholesterol", "recorded_at",
    )
    return {field: profile.get(field) for field in fields}


@patient_required
def patient_summary_api(request):
    """Return a compact dashboard payload for mobile and external clients."""
    data = PatientService.get_patient_dashboard_data(request.user.id)
    appointments = [
        {
            "id": appointment.get("id"),
            "doctor_name": appointment.get("doctor_name"),
            "date": appointment.get("appointment_date"),
            "time": appointment.get("appointment_time"),
            "status": appointment.get("status"),
            "priority": appointment.get("priority"),
        }
        for appointment in data["appointments"]
    ]

    return JsonResponse({
        "patient": {
            "id": data["patient"].get("id"),
            "full_name": data["patient"].get("full_name"),
            "health_status": data["patient"].get("health_status"),
        },
        "health_score": data["health_score"],
        "latest_profile": _profile_summary(data["latest_profile"]),
        "appointments": appointments,
        "recent_predictions": data["recent_predictions"],
        "recommendations": data["recommendations"],
    })