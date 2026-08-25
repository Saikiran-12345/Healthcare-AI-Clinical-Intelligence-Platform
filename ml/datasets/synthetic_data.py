"""
Synthetic Clinical Dataset Generator.
Generates deterministic, clinically calibrated synthetic datasets modeled after real-world
epidemiological distributions for Diabetes, Heart Disease, Hypertension, and Kidney Disease.
"""

from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd


class ClinicalDatasetGenerator:
    """Generates synthetic tabular datasets for machine learning model training."""

    @staticmethod
    def generate_diabetes_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
        """
        Generate Diabetes dataset based on Framingham & Pima clinical distributions.
        Features: age, bmi, glucose, systolic_bp, diastolic_bp, exercise_frequency, family_history, smoking, cholesterol
        """
        np.random.seed(random_state)

        age = np.random.normal(48, 14, n_samples).clip(18, 85)
        bmi = np.random.normal(28.5, 5.5, n_samples).clip(16.0, 50.0)
        glucose = np.random.normal(110, 32, n_samples).clip(60, 300)
        systolic_bp = np.random.normal(128, 18, n_samples).clip(85, 200)
        diastolic_bp = (systolic_bp * 0.65 + np.random.normal(0, 5, n_samples)).clip(50, 120)
        exercise_days = np.random.choice([0, 1, 2, 3, 4, 5, 6, 7], size=n_samples, p=[0.25, 0.15, 0.20, 0.15, 0.10, 0.08, 0.04, 0.03])
        family_history = np.random.choice([0, 1], size=n_samples, p=[0.65, 0.35])
        smoking = np.random.choice([0, 0.5, 1.0], size=n_samples, p=[0.60, 0.20, 0.20])
        cholesterol = np.random.normal(195, 38, n_samples).clip(110, 350)

        # Log-odds risk formulation
        logit = (
                        -0.5 +
            0.045 * age +
            0.12 * (bmi - 22.0) +
            0.04 * (glucose - 90.0) +
            0.015 * (systolic_bp - 120.0) +
            0.85 * family_history -
            0.20 * exercise_days +
            0.35 * smoking +
            0.008 * (cholesterol - 180.0)
        )
        prob = 1.0 / (1.0 + np.exp(-logit))
        target = (np.random.rand(n_samples) < prob).astype(int)

        df = pd.DataFrame({
            'age': np.round(age, 0),
            'bmi': np.round(bmi, 1),
            'glucose': np.round(glucose, 1),
            'systolic_bp': np.round(systolic_bp, 0),
            'diastolic_bp': np.round(diastolic_bp, 0),
            'exercise_frequency': exercise_days,
            'family_history': family_history,
            'smoking': smoking,
            'cholesterol': np.round(cholesterol, 1),
            'target': target,
        })
        return df

    @staticmethod
    def generate_heart_disease_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
        """
        Generate Heart Disease dataset based on Cleveland/Framingham cardiovascular patterns.
        Features: age, gender, systolic_bp, cholesterol, heart_rate, smoking, exercise_frequency, stress_level, family_history
        """
        np.random.seed(random_state)

        age = np.random.normal(54, 12, n_samples).clip(20, 85)
        gender = np.random.choice([0, 1], size=n_samples, p=[0.48, 0.52])  # 1 = male
        systolic_bp = np.random.normal(132, 19, n_samples).clip(90, 210)
        cholesterol = np.random.normal(210, 42, n_samples).clip(120, 400)
        heart_rate = np.random.normal(74, 12, n_samples).clip(45, 120)
        smoking = np.random.choice([0, 0.5, 1.0], size=n_samples, p=[0.55, 0.20, 0.25])
        exercise_days = np.random.choice([0, 1, 2, 3, 4, 5, 6, 7], size=n_samples, p=[0.25, 0.15, 0.20, 0.15, 0.10, 0.08, 0.04, 0.03])
        stress_level = np.random.choice(range(1, 11), size=n_samples)
        family_history = np.random.choice([0, 1], size=n_samples, p=[0.70, 0.30])

        logit = (
            -4.5 +
            0.05 * age +
            0.55 * gender +
            0.03 * (systolic_bp - 120.0) +
            0.015 * (cholesterol - 180.0) +
            0.02 * (heart_rate - 70.0) +
            0.80 * smoking -
            0.22 * exercise_days +
            0.15 * (stress_level - 3) +
            1.10 * family_history
        )
        prob = 1.0 / (1.0 + np.exp(-logit))
        target = (np.random.rand(n_samples) < prob).astype(int)

        df = pd.DataFrame({
            'age': np.round(age, 0),
            'gender': gender,
            'systolic_bp': np.round(systolic_bp, 0),
            'cholesterol': np.round(cholesterol, 1),
            'heart_rate': np.round(heart_rate, 0),
            'smoking': smoking,
            'exercise_frequency': exercise_days,
            'stress_level': stress_level,
            'family_history': family_history,
            'target': target,
        })
        return df

    @staticmethod
    def generate_hypertension_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
        """
        Generate Hypertension dataset.
        Features: age, bmi, systolic_bp, diastolic_bp, physical_activity, sodium_diet, smoking, alcohol, family_history
        """
        np.random.seed(random_state)

        age = np.random.normal(50, 15, n_samples).clip(18, 85)
        bmi = np.random.normal(27.8, 5.2, n_samples).clip(16.0, 48.0)
        systolic_bp = np.random.normal(130, 20, n_samples).clip(85, 220)
        diastolic_bp = (systolic_bp * 0.64 + np.random.normal(0, 6, n_samples)).clip(50, 130)
        physical_activity = np.random.choice([0, 0.33, 0.66, 1.0], size=n_samples, p=[0.25, 0.30, 0.30, 0.15])
        sodium_diet = np.random.choice([0, 1], size=n_samples, p=[0.45, 0.55])
        smoking = np.random.choice([0, 0.5, 1.0], size=n_samples, p=[0.60, 0.20, 0.20])
        alcohol = np.random.choice([0, 0.33, 0.66, 1.0], size=n_samples, p=[0.50, 0.25, 0.15, 0.10])
        family_history = np.random.choice([0, 1], size=n_samples, p=[0.60, 0.40])

        logit = (
            -3.8 +
            0.04 * age +
            0.10 * (bmi - 22.0) +
            0.06 * (systolic_bp - 120.0) +
            0.05 * (diastolic_bp - 80.0) -
            0.60 * physical_activity +
            0.50 * sodium_diet +
            0.45 * smoking +
            0.40 * alcohol +
            0.90 * family_history
        )
        prob = 1.0 / (1.0 + np.exp(-logit))
        target = (np.random.rand(n_samples) < prob).astype(int)

        df = pd.DataFrame({
            'age': np.round(age, 0),
            'bmi': np.round(bmi, 1),
            'systolic_bp': np.round(systolic_bp, 0),
            'diastolic_bp': np.round(diastolic_bp, 0),
            'physical_activity': physical_activity,
            'sodium_diet': sodium_diet,
            'smoking': smoking,
            'alcohol': alcohol,
            'family_history': family_history,
            'target': target,
        })
        return df

    @staticmethod
    def generate_kidney_disease_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
        """
        Generate Chronic Kidney Disease (CKD) dataset.
        Features: age, systolic_bp, glucose, cholesterol, water_intake, smoking, hypertension_flag, diabetes_flag, family_history
        """
        np.random.seed(random_state)

        age = np.random.normal(56, 13, n_samples).clip(20, 85)
        systolic_bp = np.random.normal(134, 21, n_samples).clip(90, 210)
        glucose = np.random.normal(115, 35, n_samples).clip(60, 320)
        cholesterol = np.random.normal(205, 40, n_samples).clip(110, 360)
        water_intake = np.random.normal(2.2, 0.8, n_samples).clip(0.5, 5.0)
        smoking = np.random.choice([0, 0.5, 1.0], size=n_samples, p=[0.60, 0.20, 0.20])
        hypertension_flag = (systolic_bp > 140).astype(int)
        diabetes_flag = (glucose > 125).astype(int)
        family_history = np.random.choice([0, 1], size=n_samples, p=[0.75, 0.25])

        logit = (
            -1.5 +
            0.045 * age +
            0.02 * (systolic_bp - 120.0) +
            0.025 * (glucose - 95.0) +
            0.01 * (cholesterol - 180.0) -
            0.55 * (water_intake - 1.5) +
            0.50 * smoking +
            1.20 * hypertension_flag +
            1.40 * diabetes_flag +
            0.85 * family_history
        )
        prob = 1.0 / (1.0 + np.exp(-logit))
        target = (np.random.rand(n_samples) < prob).astype(int)

        df = pd.DataFrame({
            'age': np.round(age, 0),
            'systolic_bp': np.round(systolic_bp, 0),
            'glucose': np.round(glucose, 1),
            'cholesterol': np.round(cholesterol, 1),
            'water_intake': np.round(water_intake, 1),
            'smoking': smoking,
            'hypertension_flag': hypertension_flag,
            'diabetes_flag': diabetes_flag,
            'family_history': family_history,
            'target': target,
        })
        return df

    @staticmethod
    def save_datasets_to_disk(target_dir: Path) -> None:
        """Export all generated benchmark datasets to CSV files."""
        target_dir.mkdir(parents=True, exist_ok=True)
        ClinicalDatasetGenerator.generate_diabetes_dataset().to_csv(target_dir / "diabetes.csv", index=False)
        ClinicalDatasetGenerator.generate_heart_disease_dataset().to_csv(target_dir / "heart_disease.csv", index=False)
        ClinicalDatasetGenerator.generate_hypertension_dataset().to_csv(target_dir / "hypertension.csv", index=False)
        ClinicalDatasetGenerator.generate_kidney_disease_dataset().to_csv(target_dir / "kidney_disease.csv", index=False)
