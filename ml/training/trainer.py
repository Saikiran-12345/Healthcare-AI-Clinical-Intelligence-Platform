"""
ML Training Pipeline Orchestrator.
Trains and compares 5 classification algorithms (LR, DT, RF, GB, KNN) across
4 disease domains (Diabetes, Heart Disease, Hypertension, Kidney Disease) and serializes champion models.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

from ml.datasets.synthetic_data import ClinicalDatasetGenerator
from ml.evaluation.metrics import ModelEvaluator
from ml.preprocessing.transformers import ClinicalFeatureTransformer


DISEASE_FEATURES = {
    "diabetes": [
        "age", "bmi", "glucose", "systolic_bp", "diastolic_bp",
        "exercise_frequency", "family_history", "smoking", "cholesterol"
    ],
    "heart_disease": [
        "age", "gender", "systolic_bp", "cholesterol", "heart_rate",
        "smoking", "exercise_frequency", "stress_level", "family_history"
    ],
    "hypertension": [
        "age", "bmi", "systolic_bp", "diastolic_bp", "physical_activity",
        "sodium_diet", "smoking", "alcohol", "family_history"
    ],
    "kidney_disease": [
        "age", "systolic_bp", "glucose", "cholesterol", "water_intake",
        "smoking", "hypertension_flag", "diabetes_flag", "family_history"
    ],
}


class ModelTrainer:
    """Orchestrates training, cross-validation, evaluation, and model serialization."""

    @staticmethod
    def get_candidate_models() -> Dict[str, Any]:
        """Return fresh instances of the 5 classification algorithms with tuned hyperparameters."""
        return {
            "Logistic Regression": LogisticRegression(max_iter=2000, class_weight='balanced', C=2.0, random_state=42),
            "Decision Tree": DecisionTreeClassifier(max_depth=8, class_weight='balanced', random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=None, class_weight='balanced', random_state=42),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42),
            "KNN": KNeighborsClassifier(n_neighbors=5, weights='distance')
        }

    @staticmethod
    def train_disease_models(disease_type: str, models_dir: Path) -> Dict[str, Any]:
        """
        Train and compare candidate algorithms on a disease dataset.
        Serializes the best-performing model to disk.
        """
        models_dir.mkdir(parents=True, exist_ok=True)
        disease_key = disease_type.lower().replace(" ", "_")

        # 1. Generate or load dataset
        if disease_key == "diabetes":
            df = ClinicalDatasetGenerator.generate_diabetes_dataset()
        elif disease_key == "heart_disease":
            df = ClinicalDatasetGenerator.generate_heart_disease_dataset()
        elif disease_key == "hypertension":
            df = ClinicalDatasetGenerator.generate_hypertension_dataset()
        elif disease_key == "kidney_disease":
            df = ClinicalDatasetGenerator.generate_kidney_disease_dataset()
        else:
            raise ValueError(f"Unknown disease type: {disease_type}")

        features = DISEASE_FEATURES[disease_key]
        X = df[features].values
        y = df['target'].values

        # 2. Train-Test Split (80% Train, 20% Test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        # 3. Fit feature scaler
        transformer = ClinicalFeatureTransformer(features)
        X_train_scaled = transformer.fit_transform(X_train)
        X_test_scaled = transformer.transform(X_test)

        # 4. Train & Evaluate each candidate algorithm
        candidates = ModelTrainer.get_candidate_models()
        comparison_results = {}
        best_model_name = None
        best_f1_score = -1.0
        best_model_instance = None

        for name, model in candidates.items():
            model.fit(X_train_scaled, y_train)
            metrics = ModelEvaluator.evaluate_model(model, X_test_scaled, y_test)
            cv_metrics = ModelEvaluator.evaluate_cross_validation(model, X_train_scaled, y_train, cv=5)
            metrics["cross_validation"] = cv_metrics

            comparison_results[name] = metrics

            # Select champion model prioritizing F1 score and ROC-AUC
            score_metric = metrics["f1_score"] + (metrics["roc_auc"] * 0.5)
            if score_metric > best_f1_score:
                best_f1_score = score_metric
                best_model_name = name
                best_model_instance = model

        # 5. Serialize Champion Model and Scaler
        model_file = models_dir / f"{disease_key}_model.joblib"
        scaler_file = models_dir / f"{disease_key}_scaler.joblib"
        metadata_file = models_dir / f"{disease_key}_metadata.json"

        joblib.dump(best_model_instance, model_file)
        joblib.dump(transformer, scaler_file)

        # Extract feature importances if available
        feature_importance = {}
        if hasattr(best_model_instance, 'feature_importances_'):
            importances = best_model_instance.feature_importances_
            feature_importance = {
                feat: round(float(imp), 4)
                for feat, imp in zip(features, importances)
            }
        elif hasattr(best_model_instance, 'coef_'):
            coefs = np.abs(best_model_instance.coef_[0])
            feature_importance = {
                feat: round(float(c), 4)
                for feat, c in zip(features, coefs)
            }

        report = {
            "disease_type": disease_type,
            "disease_key": disease_key,
            "best_algorithm": best_model_name,
            "features_used": features,
            "feature_importance": feature_importance,
            "metrics": comparison_results[best_model_name],
            "all_model_comparisons": comparison_results,
            "model_path": str(model_file),
            "scaler_path": str(scaler_file),
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    @staticmethod
    def train_all_models(models_dir: Path) -> Dict[str, Any]:
        """Train and evaluate models for all 4 disease domains."""
        summary = {}
        for disease in ["diabetes", "heart_disease", "hypertension", "kidney_disease"]:
            summary[disease] = ModelTrainer.train_disease_models(disease, models_dir)
        return summary
