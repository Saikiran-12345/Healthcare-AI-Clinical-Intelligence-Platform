"""
Central Multi-Disease ML Prediction Engine.
Extracts clinical features, calculates model probability, classifies risk tier,
identifies biomarker contributors, and records predictions to local JSON storage.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np

from core.audit import AuditAction, AuditLogger
from core.exceptions import PredictionError
from core.storage import db, utc_now_iso
from ml.preprocessing.transformers import ClinicalFeatureTransformer
from ml.training.trainer import DISEASE_FEATURES, ModelTrainer


MEDICAL_DISCLAIMER = (
    "DISCLAIMER: This machine learning health risk assessment is generated locally for educational "
    "and clinical screening purposes only. It is NOT a medical diagnosis. Please consult a qualified "
    "physician or healthcare professional for clinical evaluation and treatment plans."
)


class UnifiedPredictionEngine:
    """Central service orchestrating all machine learning risk evaluations."""

    _models_cache: Dict[str, Any] = {}
    _scalers_cache: Dict[str, ClinicalFeatureTransformer] = {}

    @classmethod
    def get_models_dir(cls) -> Path:
        """Resolve directory containing serialized ML artifacts."""
        base_dir = Path(__file__).resolve().parent.parent
        models_dir = base_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        return models_dir

    @classmethod
    def load_model_and_scaler(cls, disease_key: str) -> Tuple[Any, ClinicalFeatureTransformer]:
        """Load or train serialized model and scaler."""
        models_dir = cls.get_models_dir()
        model_file = models_dir / f"{disease_key}_model.joblib"
        scaler_file = models_dir / f"{disease_key}_scaler.joblib"

        if disease_key in cls._models_cache and disease_key in cls._scalers_cache:
            return cls._models_cache[disease_key], cls._scalers_cache[disease_key]

        # Auto-train if models don't exist
        if not model_file.exists() or not scaler_file.exists():
            ModelTrainer.train_disease_models(disease_key, models_dir)

        try:
            model = joblib.load(model_file)
            scaler = joblib.load(scaler_file)
            cls._models_cache[disease_key] = model
            cls._scalers_cache[disease_key] = scaler
            return model, scaler
        except Exception as e:
            raise PredictionError(f"Failed to load ML model for '{disease_key}': {str(e)}")

    @classmethod
    def predict_risk(
        cls,
        disease_type: str,
        patient_id: Optional[str] = None,
        health_metrics: Dict[str, Any] = None,
        actor_id: Optional[str] = None,
        actor_role: str = "patient",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """
        Execute prediction pipeline for a specific disease domain.
        """
        disease_key = disease_type.lower().replace(" ", "_")
        if disease_key not in DISEASE_FEATURES:
            raise PredictionError(f"Unsupported disease domain: {disease_type}")

        model, scaler = cls.load_model_and_scaler(disease_key)
        feature_names = DISEASE_FEATURES[disease_key]

        # Extract features from input metrics
        features_dict = dict(health_metrics or {})
        # Normalize keys
        if "systolic" in features_dict and "systolic_bp" not in features_dict:
            features_dict["systolic_bp"] = features_dict["systolic"]
        if "diastolic" in features_dict and "diastolic_bp" not in features_dict:
            features_dict["diastolic_bp"] = features_dict["diastolic"]
        if "blood_glucose" in features_dict and "glucose" not in features_dict:
            features_dict["glucose"] = features_dict["blood_glucose"]
        if "exercise_frequency_days" in features_dict and "exercise_frequency" not in features_dict:
            features_dict["exercise_frequency"] = features_dict["exercise_frequency_days"]
        if "water_intake_liters" in features_dict and "water_intake" not in features_dict:
            features_dict["water_intake"] = features_dict["water_intake_liters"]

        # Parse family history array into binary flag
        fam_list = features_dict.get("family_history", [])
        if isinstance(fam_list, list):
            has_fam = any(disease_key.replace("_", " ") in str(item).lower() for item in fam_list)
            features_dict["family_history"] = 1.0 if has_fam else 0.0

        # Extract ordered numeric array
        X_raw = ClinicalFeatureTransformer.extract_features_from_dict(features_dict, feature_names)
        X_scaled = scaler.transform(X_raw)

        # Predict probability
        try:
            proba = model.predict_proba(X_scaled)[0, 1]
        except Exception:
            # Fallback for models without predict_proba
            pred_class = model.predict(X_scaled)[0]
            proba = 0.85 if pred_class == 1 else 0.15

        prob_pct = round(float(proba * 100), 1)

        # Classify risk level
        if prob_pct < 60.0:
            risk_level = "LOW"
            badge_color = "green"
            clinical_summary = "Low baseline statistical likelihood of disease based on current biomarkers."
        elif prob_pct < 70.0:
            risk_level = "MODERATE"
            badge_color = "amber"
            clinical_summary = "Moderately elevated risk factors identified. Proactive lifestyle modifications advised."
        else:
            risk_level = "HIGH"
            badge_color = "red"
            clinical_summary = "Significant clinical risk markers detected. Physician evaluation and follow-up recommended."

        # Contributing risk factors analysis
        contributing_factors = []
        if features_dict.get("glucose", 90) > 110:
            contributing_factors.append("Elevated blood glucose level")
        if features_dict.get("systolic_bp", 120) > 130:
            contributing_factors.append("High systolic blood pressure")
        if features_dict.get("bmi", 22) > 27.0:
            contributing_factors.append("Elevated Body Mass Index (BMI)")
        if features_dict.get("cholesterol", 180) > 200:
            contributing_factors.append("Total cholesterol exceeding recommended range")
        if features_dict.get("smoking") in [1.0, "heavy", "regular"]:
            contributing_factors.append("Tobacco consumption habit")
        if features_dict.get("family_history") == 1.0:
            contributing_factors.append("Hereditary / family medical predisposition")
        if features_dict.get("exercise_frequency", 3) < 2:
            contributing_factors.append("Sedentary physical activity level")

        prediction_record = {
            "patient_id": patient_id or "anonymous",
            "disease_type": disease_type,
            "disease_key": disease_key,
            "probability_pct": prob_pct,
            "risk_level": risk_level,
            "badge_color": badge_color,
            "clinical_summary": clinical_summary,
            "contributing_factors": contributing_factors,
            "algorithm_used": type(model).__name__,
            "inputs": {k: features_dict.get(k) for k in feature_names},
            "disclaimer": MEDICAL_DISCLAIMER,
            "created_at": utc_now_iso(),
        }

        # Save to predictions.json
        saved = db.predictions.insert(prediction_record)

        # Notify if HIGH risk and patient is registered
        if risk_level == "HIGH" and patient_id:
            patient = db.patients.find_by_id(patient_id)
            if patient:
                db.notifications.insert({
                    "user_id": patient.get("user_id", ""),
                    "title": f"High Risk Alert: {disease_type}",
                    "message": f"Your latest AI risk assessment for {disease_type} indicated a HIGH risk level ({prob_pct}%). We recommend booking a consultation.",
                    "category": "Risk Alert",
                    "priority": "HIGH",
                    "read": False,
                    "created_at": utc_now_iso(),
                })

        AuditLogger.log(
            action=AuditAction.PREDICTION_GENERATED,
            actor_id=actor_id or patient_id or "anonymous",
            actor_role=actor_role,
            target_entity="predictions",
            target_id=saved["id"],
            ip_address=ip_address,
            details={"disease": disease_type, "risk": risk_level, "prob": prob_pct},
        )

        return saved
