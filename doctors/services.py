"""
Doctor Management and Clinical Triage Service.
Provides patient roster aggregation, clinical note recording, longitudinal charts,
and high-risk patient surveillance without database dependencies.
"""

from typing import Any, Dict, List, Optional
from core.audit import AuditAction, AuditLogger
from core.exceptions import RecordNotFoundError, ValidationError
from core.storage import db, utc_now_iso
from core.validators import Validator


class DoctorService:
    """Service handling clinical operations, patient triage, and doctor workflows."""

    @staticmethod
    def get_doctor_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve doctor record by user account ID."""
        return db.doctors.find_one(filters={"user_id": user_id})

    @staticmethod
    def get_doctor_or_create(user_id: str) -> Dict[str, Any]:
        """Ensure doctor record exists for user."""
        doc = db.doctors.find_one(filters={"user_id": user_id})
        if not doc:
            u = db.users.get_by_id(user_id)
            doc = db.doctors.insert({
                "user_id": user_id,
                "username": u.get("username", ""),
                "full_name": f"Dr. {u.get('first_name', '')} {u.get('last_name', '')}".strip() or f"Dr. {u.get('username', '')}",
                "email": u.get("email", ""),
                "phone": u.get("phone", ""),
                "specialization": "General Medicine",
                "license_number": f"MED-{u.get('username', 'DOC').upper()}-2026",
                "department": "Primary Care",
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "consultation_hours": "09:00 - 17:00",
                "rating": 4.9,
                "is_available": True,
            })
        return doc

    @staticmethod
    def get_all_doctors(active_only: bool = True) -> List[Dict[str, Any]]:
        """Fetch list of all doctors for appointment scheduling and referrals."""
        filters = {"is_available": True} if active_only else None
        return db.doctors.find_all(filters=filters, sort_by="full_name")

    @staticmethod
    def get_patient_roster(
        search_query: Optional[str] = None,
        risk_filter: Optional[str] = None,
        doctor_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query patient roster enriched with latest vitals, BMI, and highest ML risk level.
        """
        all_patients = db.patients.find_all(sort_by="full_name")
        roster = []

        q = search_query.strip().lower() if search_query else None
        target_risk = risk_filter.strip().upper() if risk_filter and risk_filter != "ALL" else None

        for p in all_patients:
            # Filter by search term
            if q:
                match_name = q in p.get("full_name", "").lower()
                match_user = q in p.get("username", "").lower()
                match_email = q in p.get("email", "").lower()
                if not (match_name or match_user or match_email):
                    continue

            # Filter by assigned doctor if provided
            if doctor_id and p.get("assigned_doctor_id") != doctor_id:
                pass  # allow doctors to view all patients in clinical directory

            # Fetch latest health profile
            latest_profiles = db.health_profiles.find_all(
                filters={"patient_id": p["id"]},
                sort_by="recorded_at",
                reverse=True,
                limit=1
            )
            latest_profile = latest_profiles[0] if latest_profiles else None

            # Fetch highest risk prediction
            predictions = db.predictions.find_all(
                filters={"patient_id": p["id"]},
                sort_by="created_at",
                reverse=True,
                limit=5
            )

            highest_risk = "LOW"
            if any(pred.get("risk_level") == "HIGH" for pred in predictions):
                highest_risk = "HIGH"
            elif any(pred.get("risk_level") == "MODERATE" for pred in predictions):
                highest_risk = "MODERATE"

            # Apply risk filter
            if target_risk and highest_risk != target_risk:
                continue

            roster.append({
                "patient": p,
                "latest_profile": latest_profile,
                "highest_risk": highest_risk,
                "predictions_count": len(predictions),
            })

        return roster

    @staticmethod
    def get_patient_clinical_chart(patient_id: str) -> Dict[str, Any]:
        """
        Compile complete longitudinal clinical chart for a patient:
        demographics, vitals trajectory, medical conditions, symptoms, ML predictions, and notes.
        """
        patient = db.patients.get_by_id(patient_id)
        user_record = db.users.find_by_id(patient.get("user_id", ""))

        profiles = db.health_profiles.find_all(
            filters={"patient_id": patient_id},
            sort_by="recorded_at",
            reverse=True,
            limit=20
        )
        latest_profile = profiles[0] if profiles else None

        medical_histories = db.medical_history.find_all(
            filters={"patient_id": patient_id},
            sort_by="diagnosis_date",
            reverse=True
        )

        symptoms = db.symptoms.find_all(
            filters={"patient_id": patient_id},
            sort_by="logged_at",
            reverse=True,
            limit=15
        )

        predictions = db.predictions.find_all(
            filters={"patient_id": patient_id},
            sort_by="created_at",
            reverse=True,
            limit=15
        )

        clinical_notes = db.get_table("clinical_notes").find_all(
            filters={"patient_id": patient_id},
            sort_by="created_at",
            reverse=True
        )

        appointments = db.appointments.find_all(
            filters={"patient_id": patient_id},
            sort_by="appointment_date",
            reverse=True,
            limit=10
        )

        return {
            "patient": patient,
            "user_record": user_record,
            "profiles": profiles,
            "latest_profile": latest_profile,
            "medical_histories": medical_histories,
            "symptoms": symptoms,
            "predictions": predictions,
            "clinical_notes": clinical_notes,
            "appointments": appointments,
        }

    @staticmethod
    def add_clinical_note(
        doctor_id: str,
        doctor_name: str,
        patient_id: str,
        subjective: str,
        assessment: str,
        plan: str,
        prescriptions: str = "",
        follow_up_date: Optional[str] = None,
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Record structured SOAP clinical observation note."""
        if not assessment or not assessment.strip():
            raise ValidationError("Clinical Assessment is required.")

        patient = db.patients.get_by_id(patient_id)

        clean_follow_up = None
        if follow_up_date and follow_up_date.strip():
            clean_follow_up = Validator.validate_date_string(follow_up_date, "Follow-up Date")

        note_record = {
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "patient_id": patient_id,
            "patient_name": patient.get("full_name", ""),
            "subjective": subjective.strip(),
            "assessment": assessment.strip(),
            "plan": plan.strip(),
            "prescriptions": prescriptions.strip(),
            "follow_up_date": clean_follow_up,
            "created_at": utc_now_iso(),
        }

        saved_note = db.get_table("clinical_notes").insert(note_record)

        AuditLogger.log(
            action=AuditAction.DOCTOR_NOTE_ADDED,
            actor_id=doctor_id,
            actor_name=doctor_name,
            actor_role="doctor",
            target_entity="patients",
            target_id=patient_id,
            ip_address=ip_address,
            details={"assessment": assessment[:100]},
        )

        return saved_note

    @staticmethod
    def get_high_risk_patients() -> List[Dict[str, Any]]:
        """Identify all patients with active HIGH risk disease estimations for immediate triage."""
        all_high_predictions = db.predictions.find_all(
            filters={"risk_level": "HIGH"},
            sort_by="created_at",
            reverse=True
        )

        high_risk_map = {}
        for pred in all_high_predictions:
            pid = pred.get("patient_id")
            if pid and pid not in high_risk_map:
                patient = db.patients.find_by_id(pid)
                if patient:
                    latest_profile = db.health_profiles.find_all(
                        filters={"patient_id": pid},
                        sort_by="recorded_at",
                        reverse=True,
                        limit=1
                    )
                    high_risk_map[pid] = {
                        "patient": patient,
                        "flagged_prediction": pred,
                        "latest_profile": latest_profile[0] if latest_profile else None,
                        "all_high_diseases": [pred.get("disease_type")],
                    }
            elif pid and pid in high_risk_map:
                dtype = pred.get("disease_type")
                if dtype not in high_risk_map[pid]["all_high_diseases"]:
                    high_risk_map[pid]["all_high_diseases"].append(dtype)

        return list(high_risk_map.values())

    @staticmethod
    def get_doctor_dashboard_stats(user_id: str) -> Dict[str, Any]:
        """Aggregate high-level overview statistics for doctor dashboard."""
        doctor = DoctorService.get_doctor_or_create(user_id)
        doctor_id = doctor["id"]

        total_patients = db.patients.count()
        high_risk_cases = DoctorService.get_high_risk_patients()

        # Doctor appointments
        pending_appointments = db.appointments.count(filters={"doctor_id": doctor_id, "status": "Pending"})
        upcoming_appointments = db.appointments.find_all(
            filters={"doctor_id": doctor_id, "status": "Approved"},
            sort_by="appointment_date",
            limit=5
        )

        # Recent predictions across system
        recent_predictions = db.predictions.find_all(sort_by="created_at", reverse=True, limit=8)

        # Risk distribution calculation
        all_predictions = db.predictions.find_all()
        risk_dist = {"LOW": 0, "MODERATE": 0, "HIGH": 0}
        for p in all_predictions:
            lvl = p.get("risk_level", "LOW")
            if lvl in risk_dist:
                risk_dist[lvl] += 1

        return {
            "doctor": doctor,
            "total_patients": total_patients,
            "high_risk_count": len(high_risk_cases),
            "high_risk_cases": high_risk_cases[:5],
            "pending_appointments_count": pending_appointments,
            "upcoming_appointments": upcoming_appointments,
            "recent_predictions": recent_predictions,
            "risk_distribution": risk_dist,
        }
