"""
Patient Management Service Layer.
Coordinates patient profiles, longitudinal health metrics, structured medical histories,
and symptom records across local JSON tables.
"""

from typing import Any, Dict, List, Optional
from core.audit import AuditAction, AuditLogger
from core.exceptions import RecordNotFoundError, ValidationError
from core.storage import db, utc_now_iso
from core.validators import Validator


class PatientService:
    """Service handling all Patient-centric clinical data operations."""

    @staticmethod
    def get_patient_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve patient entity corresponding to a given user ID."""
        return db.patients.find_one(filters={"user_id": user_id})

    @staticmethod
    def get_patient_or_create(user_id: str, user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ensure patient record exists for user."""
        patient = db.patients.find_one(filters={"user_id": user_id})
        if not patient:
            u = user_data or db.users.get_by_id(user_id)
            patient = db.patients.insert({
                "user_id": user_id,
                "username": u.get("username", ""),
                "full_name": f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("username", ""),
                "email": u.get("email", ""),
                "phone": u.get("phone", ""),
                "date_of_birth": "1990-01-01",
                "gender": "other",
                "emergency_contact": "",
                "blood_group": "O+",
                "assigned_doctor_id": None,
                "health_status": "Active",
            })
        return patient

    @staticmethod
    def save_health_profile(patient_id: str, user_id: str, profile_data: Dict[str, Any], ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Validate, calculate baseline indices (BMI), and persist a comprehensive health profile record.
        """
        # Validate individual fields
        age = Validator.validate_age(profile_data.get("age", 30))
        gender = Validator.validate_gender(profile_data.get("gender", "male"))
        height_cm = Validator.validate_height(profile_data.get("height_cm", 170.0))
        weight_kg = Validator.validate_weight(profile_data.get("weight_kg", 70.0))
        sys_bp, dia_bp = Validator.validate_blood_pressure(
            profile_data.get("systolic_bp", 120),
            profile_data.get("diastolic_bp", 80)
        )
        heart_rate = Validator.validate_heart_rate(profile_data.get("heart_rate", 72))
        glucose = Validator.validate_glucose(profile_data.get("blood_glucose", 95.0))
        cholesterol = Validator.validate_cholesterol(profile_data.get("cholesterol", 180.0))
        sleep_hours = Validator.validate_sleep_hours(profile_data.get("sleep_hours", 7.5))
        water_liters = Validator.validate_water_intake(profile_data.get("water_intake_liters", 2.5))
        exercise_days = Validator.validate_exercise_frequency(profile_data.get("exercise_frequency_days", 3))
        stress_level = Validator.validate_stress_level(profile_data.get("stress_level", 4))

        # Calculate BMI locally: weight (kg) / (height (m) ^ 2)
        height_m = height_cm / 100.0
        bmi = round(weight_kg / (height_m * height_m), 2)

        # Categorize BMI
        if bmi < 18.5:
            bmi_category = "Underweight"
        elif bmi < 25.0:
            bmi_category = "Normal Weight"
        elif bmi < 30.0:
            bmi_category = "Overweight"
        elif bmi < 35.0:
            bmi_category = "Obese Class I"
        elif bmi < 40.0:
            bmi_category = "Obese Class II"
        else:
            bmi_category = "Obese Class III (Severe)"

        health_record = {
            "patient_id": patient_id,
            "user_id": user_id,
            "age": age,
            "gender": gender,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "bmi": bmi,
            "bmi_category": bmi_category,
            "systolic_bp": sys_bp,
            "diastolic_bp": dia_bp,
            "heart_rate": heart_rate,
            "blood_glucose": glucose,
            "cholesterol": cholesterol,
            "smoking_status": profile_data.get("smoking_status", "never"),
            "alcohol_consumption": profile_data.get("alcohol_consumption", "none"),
            "physical_activity_level": profile_data.get("physical_activity_level", "moderate"),
            "exercise_frequency_days": exercise_days,
            "sleep_hours": sleep_hours,
            "water_intake_liters": water_liters,
            "stress_level": stress_level,
            "diet_type": profile_data.get("diet_type", "balanced"),
            "family_history": profile_data.get("family_history", []),
            "existing_conditions": profile_data.get("existing_conditions", []),
            "recorded_at": utc_now_iso(),
        }

        saved_profile = db.health_profiles.insert(health_record)

        AuditLogger.log(
            action=AuditAction.HEALTH_ASSESSMENT_SUBMIT,
            actor_id=user_id,
            actor_role="patient",
            target_entity="health_profiles",
            target_id=saved_profile["id"],
            ip_address=ip_address,
            details={"bmi": bmi, "sys_bp": sys_bp, "diastolic_bp": dia_bp, "glucose": glucose},
        )

        return saved_profile

    @staticmethod
    def get_latest_health_profile(patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve most recent health profile for a patient."""
        profiles = db.health_profiles.find_all(
            filters={"patient_id": patient_id},
            sort_by="recorded_at",
            reverse=True,
            limit=1
        )
        return profiles[0] if profiles else None

    @staticmethod
    def get_health_profile_history(patient_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve historical health profile submissions for longitudinal tracking."""
        return db.health_profiles.find_all(
            filters={"patient_id": patient_id},
            sort_by="recorded_at",
            reverse=True,
            limit=limit
        )

    @staticmethod
    def add_medical_history(
        patient_id: str,
        user_id: str,
        condition: str,
        diagnosis_date: str,
        status: str = "Active",
        severity: str = "Moderate",
        notes: str = "",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Add a medical history record."""
        if not condition or not condition.strip():
            raise ValidationError("Medical condition name is required.")

        clean_date = Validator.validate_date_string(diagnosis_date, "Diagnosis Date")

        history_record = {
            "patient_id": patient_id,
            "user_id": user_id,
            "condition": condition.strip(),
            "diagnosis_date": clean_date,
            "status": status,
            "severity": severity,
            "notes": notes.strip(),
            "recorded_at": utc_now_iso(),
        }

        saved = db.medical_history.insert(history_record)

        AuditLogger.log(
            action=AuditAction.MEDICAL_HISTORY_ADD,
            actor_id=user_id,
            actor_role="patient",
            target_entity="medical_history",
            target_id=saved["id"],
            ip_address=ip_address,
            details={"condition": condition, "status": status},
        )

        return saved

    @staticmethod
    def get_medical_history(patient_id: str) -> List[Dict[str, Any]]:
        """Fetch all medical history records for a patient."""
        return db.medical_history.find_all(
            filters={"patient_id": patient_id},
            sort_by="diagnosis_date",
            reverse=True
        )

    @staticmethod
    def delete_medical_history(history_id: str, patient_id: str) -> bool:
        """Delete a medical history entry with ownership validation."""
        history = db.medical_history.find_by_id(history_id)
        if not history or history.get("patient_id") != patient_id:
            raise RecordNotFoundError("medical_history", history_id)
        return db.medical_history.delete(history_id)

    @staticmethod
    def log_symptom_entry(
        patient_id: str,
        user_id: str,
        symptom_name: str,
        category: str = "General",
        severity: int = 3,
        duration_days: int = 1,
        frequency: str = "Daily",
        notes: str = "",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Log a patient symptom report."""
        if not symptom_name or not symptom_name.strip():
            raise ValidationError("Symptom name is required.")

        symptom_record = {
            "patient_id": patient_id,
            "user_id": user_id,
            "symptom_name": symptom_name.strip(),
            "category": category,
            "severity": int(severity),
            "duration_days": int(duration_days),
            "frequency": frequency,
            "notes": notes.strip(),
            "logged_at": utc_now_iso(),
        }

        saved = db.symptoms.insert(symptom_record)

        AuditLogger.log(
            action=AuditAction.SYMPTOMS_LOGGED,
            actor_id=user_id,
            actor_role="patient",
            target_entity="symptoms",
            target_id=saved["id"],
            ip_address=ip_address,
            details={"symptom": symptom_name, "severity": severity},
        )

        return saved

    @staticmethod
    def get_patient_symptoms(patient_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent logged symptoms for a patient."""
        return db.symptoms.find_all(
            filters={"patient_id": patient_id},
            sort_by="logged_at",
            reverse=True,
            limit=limit
        )

    @staticmethod
    def get_patient_dashboard_data(user_id: str) -> Dict[str, Any]:
        """Aggregate comprehensive dashboard data for the patient view."""
        patient = PatientService.get_patient_or_create(user_id)
        patient_id = patient["id"]

        latest_profile = PatientService.get_latest_health_profile(patient_id)
        profile_history = PatientService.get_health_profile_history(patient_id, limit=5)
        medical_histories = PatientService.get_medical_history(patient_id)
        recent_symptoms = PatientService.get_patient_symptoms(patient_id, limit=5)

        # Fetch predictions for this patient
        recent_predictions = db.predictions.find_all(
            filters={"patient_id": patient_id},
            sort_by="created_at",
            reverse=True,
            limit=5
        )

        # Fetch active recommendations
        recommendations = db.recommendations.find_all(
            filters={"patient_id": patient_id},
            sort_by="created_at",
            reverse=True,
            limit=6
        )

        # Fetch upcoming appointments
        appointments = db.appointments.find_all(
            filters={"patient_id": patient_id},
            sort_by="appointment_date",
            reverse=False,
            limit=5
        )

        # Calculate composite health score if profile exists
        health_score = 78  # default baseline
        if latest_profile:
            # Score formula based on BP, BMI, Glucose, Cholesterol, Sleep, Exercise
            score = 100
            bmi = latest_profile.get("bmi", 22.0)
            if bmi < 18.5 or bmi > 25.0:
                score -= min(15, abs(bmi - 22.0) * 2)

            sys_bp = latest_profile.get("systolic_bp", 120)
            if sys_bp > 120:
                score -= min(15, (sys_bp - 120) * 0.5)

            glucose = latest_profile.get("blood_glucose", 90)
            if glucose > 100:
                score -= min(15, (glucose - 100) * 0.4)

            chol = latest_profile.get("cholesterol", 180)
            if chol > 200:
                score -= min(10, (chol - 200) * 0.2)

            stress = latest_profile.get("stress_level", 4)
            score -= (stress * 1.5)

            sleep = latest_profile.get("sleep_hours", 7.5)
            if sleep < 7.0 or sleep > 9.0:
                score -= 8

            health_score = max(10, min(100, int(score)))

        return {
            "patient": patient,
            "latest_profile": latest_profile,
            "profile_history": profile_history,
            "medical_histories": medical_histories,
            "recent_symptoms": recent_symptoms,
            "recent_predictions": recent_predictions,
            "recommendations": recommendations,
            "appointments": appointments,
            "health_score": health_score,
        }
