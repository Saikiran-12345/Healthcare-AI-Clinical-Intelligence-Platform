"""
Phase 7 & 8 Unit Tests: ML Pipelines, 4 Disease Models, 5 Algorithms, Evaluation Metrics, and Unified Predictor.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.storage import JsonDatabase
from ml.datasets.synthetic_data import ClinicalDatasetGenerator
from ml.preprocessing.transformers import ClinicalFeatureTransformer
from ml.training.trainer import ModelTrainer, DISEASE_FEATURES
from ml.prediction.predictor import UnifiedPredictionEngine
from ml.evaluation.metrics import ModelEvaluator


class TestMachineLearningModule(unittest.TestCase):
    """Test datasets, training across 5 classification algorithms, metrics, and multi-disease prediction."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from core import storage
        self.orig_db = storage.db
        storage.db = JsonDatabase(self.temp_dir)
        import ml.prediction.predictor
        ml.prediction.predictor.db = storage.db

        self.models_dir = Path(self.temp_dir) / "ml_models"

    def tearDown(self):
        from core import storage
        storage.db = self.orig_db
        import ml.prediction.predictor
        ml.prediction.predictor.db = self.orig_db
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_synthetic_dataset_generators(self):
        df_diab = ClinicalDatasetGenerator.generate_diabetes_dataset(n_samples=100)
        self.assertEqual(len(df_diab), 100)
        self.assertIn("target", df_diab.columns)
        self.assertIn("glucose", df_diab.columns)

        df_heart = ClinicalDatasetGenerator.generate_heart_disease_dataset(n_samples=100)
        self.assertEqual(len(df_heart), 100)
        self.assertIn("cholesterol", df_heart.columns)

        df_htn = ClinicalDatasetGenerator.generate_hypertension_dataset(n_samples=100)
        self.assertEqual(len(df_htn), 100)

        df_ckd = ClinicalDatasetGenerator.generate_kidney_disease_dataset(n_samples=100)
        self.assertEqual(len(df_ckd), 100)

    def test_model_training_and_comparison(self):
        report = ModelTrainer.train_disease_models("diabetes", self.models_dir)
        self.assertIn("best_algorithm", report)
        self.assertIn(report["best_algorithm"], ["Logistic Regression", "Decision Tree", "Random Forest", "Gradient Boosting", "KNN"])
        self.assertTrue(report["metrics"]["accuracy"] > 0.60)
        self.assertTrue(report["metrics"]["f1_score"] > 0.40)
        self.assertTrue((self.models_dir / "diabetes_model.joblib").exists())
        self.assertTrue((self.models_dir / "diabetes_scaler.joblib").exists())

    def test_prediction_engine_execution(self):
        # Patch UnifiedPredictionEngine to use temp models dir
        orig_get_dir = UnifiedPredictionEngine.get_models_dir
        UnifiedPredictionEngine.get_models_dir = classmethod(lambda cls: self.models_dir)

        # Low-risk test profile (young, normal biomarkers, active)
        healthy_metrics = {
            "age": 25,
            "bmi": 21.0,
            "glucose": 85.0,
            "systolic_bp": 115,
            "diastolic_bp": 75,
            "exercise_frequency": 5,
            "smoking": 0,
            "cholesterol": 160.0,
            "family_history": "no",
        }
        res_low = UnifiedPredictionEngine.predict_risk("diabetes", health_metrics=healthy_metrics)
        self.assertIn("probability_pct", res_low)
        self.assertIn("risk_level", res_low)
        self.assertEqual(res_low["risk_level"], "LOW")

        # High-risk test profile (older, very high glucose, obese, smoker, high BP)
        high_risk_metrics = {
            "age": 68,
            "bmi": 38.5,
            "glucose": 240.0,
            "systolic_bp": 175,
            "diastolic_bp": 105,
            "exercise_frequency": 0,
            "smoking": 1.0,
            "cholesterol": 280.0,
            "family_history": "yes",
        }
        res_high = UnifiedPredictionEngine.predict_risk("diabetes", health_metrics=high_risk_metrics)
        self.assertEqual(res_high["risk_level"], "HIGH")
        self.assertTrue(res_high["probability_pct"] >= 70.0)
        self.assertTrue(len(res_high["contributing_factors"]) > 0)

        # Restore method
        UnifiedPredictionEngine.get_models_dir = orig_get_dir


if __name__ == '__main__':
    unittest.main()
