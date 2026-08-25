"""
Appointment Management Service Layer.
Coordinates patient consultations, conflict-free time slot scheduling,
status workflows (Pending/Approved/Rejected/Completed), and notifications.
"""

from typing import Any, Dict, List, Optional
from core.audit import AuditAction, AuditLogger
from core.exceptions import AppointmentConflictError, RecordNotFoundError, ValidationError
from core.storage import db, utc_now_iso
from core.validators import Validator


AVAILABLE_TIME_SLOTS = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
]


class AppointmentService:
    """Service handling clinical booking, conflict detection, and status transitions."""

    @staticmethod
    def check_doctor_slot_available(
        doctor_id: str,
        date_str: str,
        time_str: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """Verify whether a doctor is free at a specific date and time slot."""
        clean_date = Validator.validate_date_string(date_str, "Appointment Date")
        clean_time = Validator.validate_time_string(time_str, "Appointment Time")

        existing = db.appointments.find_all(
            filters={
                "doctor_id": doctor_id,
                "appointment_date": clean_date,
                "appointment_time": clean_time,
            }
        )

        for appt in existing:
            if exclude_id and appt.get("id") == exclude_id:
                continue
            # Non-cancelled/non-rejected bookings represent conflicts
            if appt.get("status") in ["Pending", "Approved"]:
                return False

        return True

    @staticmethod
    def get_doctor_available_slots(doctor_id: str, date_str: str) -> List[str]:
        """Return list of free time slots for a given doctor on a specific date."""
        clean_date = Validator.validate_date_string(date_str, "Appointment Date")
        booked = db.appointments.find_all(
            filters={"doctor_id": doctor_id, "appointment_date": clean_date}
        )
        booked_times = {
            a.get("appointment_time") for a in booked
            if a.get("status") in ["Pending", "Approved"]
        }

        return [slot for slot in AVAILABLE_TIME_SLOTS if slot not in booked_times]

    @staticmethod
    def book_appointment(
        patient_id: str,
        doctor_id: str,
        date_str: str,
        time_str: str,
        reason: str,
        priority: str = "Standard",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Request a new clinical consultation appointment."""
        clean_date = Validator.validate_future_date_string(date_str, "Appointment Date")
        clean_time = Validator.validate_time_string(time_str, "Appointment Time")

        if not reason or not reason.strip():
            raise ValidationError("Reason for consultation is required.")

        patient = db.patients.get_by_id(patient_id)
        doctor = db.doctors.get_by_id(doctor_id)

        # Check for double booking conflict
        if not AppointmentService.check_doctor_slot_available(doctor_id, clean_date, clean_time):
            raise AppointmentConflictError(
                f"Dr. {doctor.get('full_name')} is already booked on {clean_date} at {clean_time}."
            )

        appointment_record = {
            "patient_id": patient_id,
            "patient_name": patient.get("full_name", ""),
            "patient_email": patient.get("email", ""),
            "doctor_id": doctor_id,
            "doctor_name": doctor.get("full_name", ""),
            "doctor_specialization": doctor.get("specialization", ""),
            "appointment_date": clean_date,
            "appointment_time": clean_time,
            "reason": reason.strip(),
            "priority": priority,
            "status": "Pending",
            "doctor_notes": "",
            "created_at": utc_now_iso(),
        }

        saved_appointment = db.appointments.insert(appointment_record)

        # Create doctor notification
        db.notifications.insert({
            "user_id": doctor.get("user_id", ""),
            "title": "New Appointment Request",
            "message": f"Patient {patient.get('full_name')} requested an appointment for {clean_date} at {clean_time}.",
            "category": "Appointment",
            "priority": "HIGH" if priority == "Urgent" else "NORMAL",
            "read": False,
            "created_at": utc_now_iso(),
        })

        AuditLogger.log(
            action=AuditAction.APPOINTMENT_REQUESTED,
            actor_id=patient_id,
            actor_name=patient.get("full_name", ""),
            actor_role="patient",
            target_entity="appointments",
            target_id=saved_appointment["id"],
            ip_address=ip_address,
            details={"doctor": doctor.get("full_name"), "date": clean_date, "time": clean_time},
        )

        return saved_appointment

    @staticmethod
    def approve_appointment(
        appointment_id: str,
        doctor_id: str,
        notes: str = "",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Approve a pending appointment request."""
        appointment = db.appointments.get_by_id(appointment_id)
        if appointment.get("doctor_id") != doctor_id:
            raise ValidationError("You are not authorized to manage this appointment.")

        updates = {
            "status": "Approved",
            "doctor_notes": notes.strip() or "Appointment approved by attending physician.",
        }
        updated = db.appointments.update(appointment_id, updates)

        # Notify patient
        patient = db.patients.get_by_id(appointment["patient_id"])
        db.notifications.insert({
            "user_id": patient.get("user_id", ""),
            "title": "Appointment Confirmed",
            "message": f"Your appointment with {appointment['doctor_name']} on {appointment['appointment_date']} at {appointment['appointment_time']} has been approved.",
            "category": "Appointment",
            "priority": "HIGH",
            "read": False,
            "created_at": utc_now_iso(),
        })

        AuditLogger.log(
            action=AuditAction.APPOINTMENT_APPROVED,
            actor_id=doctor_id,
            actor_role="doctor",
            target_entity="appointments",
            target_id=appointment_id,
            ip_address=ip_address,
        )

        return updated

    @staticmethod
    def reject_appointment(
        appointment_id: str,
        doctor_id: str,
        reason: str = "",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Decline/Reject an appointment request."""
        appointment = db.appointments.get_by_id(appointment_id)
        if appointment.get("doctor_id") != doctor_id:
            raise ValidationError("You are not authorized to manage this appointment.")

        updates = {
            "status": "Rejected",
            "doctor_notes": reason.strip() or "Unavailable at requested time. Please reschedule.",
        }
        updated = db.appointments.update(appointment_id, updates)

        patient = db.patients.get_by_id(appointment["patient_id"])
        db.notifications.insert({
            "user_id": patient.get("user_id", ""),
            "title": "Appointment Declined",
            "message": f"Your appointment request for {appointment['appointment_date']} was declined: {updates['doctor_notes']}",
            "category": "Appointment",
            "priority": "HIGH",
            "read": False,
            "created_at": utc_now_iso(),
        })

        AuditLogger.log(
            action=AuditAction.APPOINTMENT_REJECTED,
            actor_id=doctor_id,
            actor_role="doctor",
            target_entity="appointments",
            target_id=appointment_id,
            ip_address=ip_address,
            details={"reason": reason},
        )

        return updated

    @staticmethod
    def cancel_appointment(
        appointment_id: str,
        user_id: str,
        role: str,
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Cancel an appointment by either patient or doctor."""
        appointment = db.appointments.get_by_id(appointment_id)

        updates = {"status": "Cancelled"}
        updated = db.appointments.update(appointment_id, updates)

        AuditLogger.log(
            action=AuditAction.APPOINTMENT_CANCELLED,
            actor_id=user_id,
            actor_role=role,
            target_entity="appointments",
            target_id=appointment_id,
            ip_address=ip_address,
        )

        return updated

    @staticmethod
    def complete_appointment(
        appointment_id: str,
        doctor_id: str,
        notes: str = "",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Mark an approved appointment as completed with final clinical summary."""
        appointment = db.appointments.get_by_id(appointment_id)
        if appointment.get("doctor_id") != doctor_id:
            raise ValidationError("You are not authorized to complete this appointment.")

        updates = {
            "status": "Completed",
            "doctor_notes": notes.strip() or appointment.get("doctor_notes", ""),
        }
        updated = db.appointments.update(appointment_id, updates)

        AuditLogger.log(
            action=AuditAction.APPOINTMENT_COMPLETED,
            actor_id=doctor_id,
            actor_role="doctor",
            target_entity="appointments",
            target_id=appointment_id,
            ip_address=ip_address,
        )

        return updated

    @staticmethod
    def get_patient_appointments(patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve all consultations for a patient sorted chronologically."""
        return db.appointments.find_all(
            filters={"patient_id": patient_id},
            sort_by="appointment_date",
            reverse=True
        )

    @staticmethod
    def get_doctor_appointments(doctor_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve appointments for a doctor with optional status filter."""
        filters = {"doctor_id": doctor_id}
        if status and status != "ALL":
            filters["status"] = status
        return db.appointments.find_all(
            filters=filters,
            sort_by="appointment_date",
            reverse=False
        )
