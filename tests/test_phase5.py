"""
Phase 5 Unit Tests: Physiological Calculators, Hemodynamics, BMR/TDEE, and Composite Health Scoring.
"""

import os
import unittest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from health.calculators import HealthCalculators


class TestHealthCalculators(unittest.TestCase):
    """Test all physiological and clinical mathematical calculators."""

    def test_bmi_calculator(self):
        # 175 cm, 70 kg -> 70 / (1.75^2) = 22.86 (Normal Weight)
        res = HealthCalculators.calculate_bmi(175.0, 70.0)
        self.assertEqual(res["bmi"], 22.86)
        self.assertEqual(res["category"], "Normal Weight")
        self.assertEqual(res["badge_color"], "green")
        self.assertEqual(res["ideal_weight_min_kg"], 56.7)
        self.assertEqual(res["ideal_weight_max_kg"], 76.3)
        self.assertEqual(res["weight_diff_kg"], 0.0)

        # Obese case: 170 cm, 105 kg -> 105 / (1.7^2) = 36.33 (Obesity Class II)
        res_obese = HealthCalculators.calculate_bmi(170.0, 105.0)
        self.assertEqual(res_obese["bmi"], 36.33)
        self.assertEqual(res_obese["category"], "Obesity Class II")

    def test_bmr_and_tdee_calculator(self):
        # Male, 75kg, 180cm, 30 yrs
        # Mifflin: (10 * 75) + (6.25 * 180) - (5 * 30) + 5 = 750 + 1125 - 150 + 5 = 1730 kcal
        res = HealthCalculators.calculate_bmr(180.0, 75.0, 30, "male", formula="mifflin")
        self.assertEqual(res["bmr_calories"], 1730.0)

        # TDEE Moderate (1.55 * 1730 = 2681.5 -> 2682)
        tdee_res = HealthCalculators.calculate_tdee(res["bmr_calories"], "moderate")
        self.assertEqual(tdee_res["tdee_maintenance"], 2682.0)
        self.assertEqual(tdee_res["fat_loss_target"], 2182.0)
        self.assertTrue(tdee_res["macros"]["protein_grams"] > 0)

    def test_blood_pressure_classifier_and_map(self):
        # Normal BP
        normal_bp = HealthCalculators.classify_blood_pressure(115, 75)
        self.assertEqual(normal_bp["category"], "Normal Blood Pressure")
        self.assertEqual(normal_bp["risk_tier"], "LOW")
        # MAP = (2 * 75 + 115) / 3 = 265 / 3 = 88.3
        self.assertEqual(normal_bp["mean_arterial_pressure"], 88.3)
        self.assertEqual(normal_bp["pulse_pressure"], 40)

        # Stage 1 HTN
        s1_bp = HealthCalculators.classify_blood_pressure(135, 85)
        self.assertEqual(s1_bp["category"], "Hypertension Stage 1")

        # Stage 2 HTN
        s2_bp = HealthCalculators.classify_blood_pressure(145, 95)
        self.assertEqual(s2_bp["category"], "Hypertension Stage 2")

        # Crisis
        crisis = HealthCalculators.classify_blood_pressure(190, 125)
        self.assertEqual(crisis["category"], "Hypertensive Crisis (Emergency)")
        self.assertEqual(crisis["risk_tier"], "CRITICAL")

    def test_heart_rate_zones(self):
        hr_res = HealthCalculators.classify_heart_rate(70, 30)
        self.assertEqual(hr_res["category"], "Normal Resting Heart Rate")
        self.assertEqual(hr_res["max_heart_rate"], 190)  # 220 - 30
        self.assertEqual(hr_res["training_zones"]["aerobic_zone"], (133, 152))

    def test_hydration_and_sleep_scoring(self):
        hyd = HealthCalculators.calculate_hydration_score(2.5, 70.0)
        self.assertTrue(0 <= hyd["hydration_score"] <= 100)
        self.assertIn("target_liters", hyd)

        sleep = HealthCalculators.calculate_sleep_score(8.0)
        self.assertEqual(sleep["sleep_score"], 100)

    def test_composite_health_score(self):
        metrics = {
            "height_cm": 175.0,
            "weight_kg": 72.0,
            "age": 32,
            "systolic_bp": 118,
            "diastolic_bp": 78,
            "blood_glucose": 92.0,
            "cholesterol": 175.0,
            "heart_rate": 68,
            "sleep_hours": 8.0,
            "water_intake_liters": 2.5,
            "smoking_status": "never",
            "alcohol_consumption": "none",
            "exercise_frequency_days": 4,
            "physical_activity_level": "moderate",
            "stress_level": 3,
            "diet_type": "balanced",
        }
        res = HealthCalculators.calculate_composite_health_score(metrics)
        self.assertTrue(80 <= res["overall_score"] <= 100)
        self.assertIn("cardiovascular_score", res["components"])
        self.assertIn("metabolic_score", res["components"])
        self.assertIn("lifestyle_score", res["components"])


if __name__ == '__main__':
    unittest.main()
