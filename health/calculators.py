"""
Health and Physiological Calculations Engine.
Modular, pure-Python algorithms for biometrics, metabolism, cardiovascular indicators,
lifestyle scores, hydration, and composite wellness metrics.
"""

from typing import Any, Dict, Optional, Tuple
from health.clinical_rules import ClinicalStandards


class HealthCalculators:
    """Mathematical and clinical calculation methods."""

    @staticmethod
    def calculate_bmi(height_cm: float, weight_kg: float) -> Dict[str, Any]:
        """
        Calculate Body Mass Index (BMI), WHO weight classification, and healthy weight range.
        Formula: weight (kg) / (height (m) ^ 2)
        """
        if height_cm <= 0 or weight_kg <= 0:
            raise ValueError("Height and weight must be positive numbers.")

        height_m = height_cm / 100.0
        bmi = round(weight_kg / (height_m * height_m), 2)

        # WHO Categorization
        if bmi < 18.5:
            category = "Underweight"
            risk_note = "Increased risk for nutritional deficiency and osteoporosis."
            color = "amber"
        elif bmi <= 24.9:
            category = "Normal Weight"
            risk_note = "Optimal lowest disease risk range."
            color = "green"
        elif bmi <= 29.9:
            category = "Overweight"
            risk_note = "Moderately elevated risk for hypertension and cardiometabolic disorders."
            color = "amber"
        elif bmi <= 34.9:
            category = "Obesity Class I"
            risk_note = "High risk for Type 2 diabetes and cardiovascular disease."
            color = "red"
        elif bmi <= 39.9:
            category = "Obesity Class II"
            risk_note = "Very high cardiovascular and metabolic risk."
            color = "red"
        else:
            category = "Obesity Class III (Severe/Morbid)"
            risk_note = "Extremely high risk; clinical intervention advised."
            color = "red"

        # Healthy weight range (BMI 18.5 - 24.9)
        ideal_min_kg = round(18.5 * (height_m * height_m), 1)
        ideal_max_kg = round(24.9 * (height_m * height_m), 1)

        # Difference to healthy weight
        if weight_kg < ideal_min_kg:
            weight_diff = round(weight_kg - ideal_min_kg, 1)  # negative means gain needed
        elif weight_kg > ideal_max_kg:
            weight_diff = round(weight_kg - ideal_max_kg, 1)  # positive means loss needed
        else:
            weight_diff = 0.0

        return {
            "bmi": bmi,
            "category": category,
            "risk_note": risk_note,
            "badge_color": color,
            "ideal_weight_min_kg": ideal_min_kg,
            "ideal_weight_max_kg": ideal_max_kg,
            "weight_diff_kg": weight_diff,
        }

    @staticmethod
    def calculate_bmr(height_cm: float, weight_kg: float, age: int, gender: str, formula: str = "mifflin") -> Dict[str, Any]:
        """
        Calculate Basal Metabolic Rate (BMR) in calories/day.
        Supports Mifflin-St Jeor (gold standard) and Revised Harris-Benedict formulas.
        """
        is_male = gender.lower() == "male"

        if formula.lower() == "mifflin":
            # Mifflin-St Jeor Equation:
            # Male: (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
            # Female: (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
            s = 5 if is_male else -161
            bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + s
        else:
            # Revised Harris-Benedict Equation:
            # Male: 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
            # Female: 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
            if is_male:
                bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
            else:
                bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

        return {
            "bmr_calories": round(bmr, 0),
            "formula_used": "Mifflin-St Jeor" if formula.lower() == "mifflin" else "Revised Harris-Benedict",
        }

    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> Dict[str, Any]:
        """
        Calculate Total Daily Energy Expenditure (TDEE) and macronutrient distributions.
        """
        multipliers = {
            "sedentary": 1.2,          # Little or no exercise
            "light": 1.375,            # Light exercise 1-3 days/week
            "moderate": 1.55,          # Moderate exercise 3-5 days/week
            "active": 1.725,           # Hard exercise 6-7 days/week
            "very_active": 1.9,        # Very hard exercise / physical job
        }
        mult = multipliers.get(activity_level.lower(), 1.2)
        maintenance_calories = round(bmr * mult, 0)

        # Caloric goals
        fat_loss_calories = round(maintenance_calories - 500, 0)
        muscle_gain_calories = round(maintenance_calories + 300, 0)

        # Recommended Macro Splits for Maintenance (30% Protein, 40% Carbs, 30% Fat)
        protein_g = round((maintenance_calories * 0.30) / 4.0, 0)
        carbs_g = round((maintenance_calories * 0.40) / 4.0, 0)
        fats_g = round((maintenance_calories * 0.30) / 9.0, 0)

        return {
            "tdee_maintenance": maintenance_calories,
            "fat_loss_target": max(1200, fat_loss_calories),
            "muscle_gain_target": muscle_gain_calories,
            "activity_multiplier": mult,
            "macros": {
                "protein_grams": protein_g,
                "carbs_grams": carbs_g,
                "fats_grams": fats_g,
            }
        }

    @staticmethod
    def classify_blood_pressure(systolic: int, diastolic: int) -> Dict[str, Any]:
        """
        Classify blood pressure using AHA/ACC 2017 Clinical Guidelines.
        Calculates Mean Arterial Pressure (MAP) and Pulse Pressure (PP).
        """
        if diastolic >= systolic:
            raise ValueError("Systolic BP must be greater than Diastolic BP.")

        # Mean Arterial Pressure: (2 * Diastolic + Systolic) / 3
        map_value = round((2.0 * diastolic + systolic) / 3.0, 1)

        # Pulse Pressure: Systolic - Diastolic
        pulse_pressure = systolic - diastolic

        if systolic > 180 or diastolic > 120:
            category = "Hypertensive Crisis (Emergency)"
            risk_tier = "CRITICAL"
            badge_color = "red"
            guidance = "Immediate medical evaluation required."
        elif systolic >= 140 or diastolic >= 90:
            category = "Hypertension Stage 2"
            risk_tier = "HIGH"
            badge_color = "red"
            guidance = "Medical consultation and combination medication / lifestyle therapy indicated."
        elif (130 <= systolic <= 139) or (80 <= diastolic <= 89):
            category = "Hypertension Stage 1"
            risk_tier = "MODERATE"
            badge_color = "amber"
            guidance = "Lifestyle intervention, sodium restriction, and regular monitoring recommended."
        elif (120 <= systolic <= 129) and (diastolic < 80):
            category = "Elevated Blood Pressure"
            risk_tier = "MILD"
            badge_color = "amber"
            guidance = "Lifestyle modifications to prevent progression to hypertension."
        elif systolic < 120 and diastolic < 80:
            category = "Normal Blood Pressure"
            risk_tier = "LOW"
            badge_color = "green"
            guidance = "Optimal cardiovascular blood pressure range."
        else:
            category = "Normal / Undefined Range"
            risk_tier = "LOW"
            badge_color = "green"
            guidance = "Maintain healthy dietary and exercise habits."

        return {
            "category": category,
            "risk_tier": risk_tier,
            "badge_color": badge_color,
            "guidance": guidance,
            "mean_arterial_pressure": map_value,
            "pulse_pressure": pulse_pressure,
            "systolic": systolic,
            "diastolic": diastolic,
        }

    @staticmethod
    def classify_heart_rate(resting_hr: int, age: int) -> Dict[str, Any]:
        """
        Classify resting heart rate and compute aerobic exercise training zones.
        """
        # Categorize resting heart rate
        if resting_hr < 60:
            category = "Bradycardia (Low Resting HR)"
            note = "Common in well-trained athletes, but may require check if symptomatic."
        elif resting_hr <= 100:
            category = "Normal Resting Heart Rate"
            note = "Standard healthy resting cardiovascular range."
        else:
            category = "Tachycardia (High Resting HR)"
            note = "Elevated resting heart rate; evaluate stress, caffeine, or arrhythmias."

        # Maximum Heart Rate (Fox Formula: 220 - age)
        max_hr = max(100, 220 - age)

        # Heart Rate Zones
        zones = {
            "warm_up_zone": (round(max_hr * 0.50), round(max_hr * 0.60)),
            "fat_burn_zone": (round(max_hr * 0.60), round(max_hr * 0.70)),
            "aerobic_zone": (round(max_hr * 0.70), round(max_hr * 0.80)),
            "anaerobic_zone": (round(max_hr * 0.80), round(max_hr * 0.90)),
            "vo2_max_zone": (round(max_hr * 0.90), max_hr),
        }

        return {
            "resting_heart_rate": resting_hr,
            "category": category,
            "clinical_note": note,
            "max_heart_rate": max_hr,
            "training_zones": zones,
        }

    @staticmethod
    def calculate_hydration_score(water_intake_liters: float, weight_kg: float) -> Dict[str, Any]:
        """
        Evaluate daily hydration status based on body weight.
        Baseline: 35 ml per kg of body mass.
        """
        recommended_liters = round((weight_kg * ClinicalStandards.WATER_PER_KG_ML) / 1000.0, 2)
        recommended_liters = max(1.5, min(4.5, recommended_liters))

        ratio = water_intake_liters / recommended_liters
        score = min(100, int(ratio * 100)) if ratio <= 1.0 else max(80, int(100 - (ratio - 1.0) * 40))

        if score >= 85:
            status = "Well Hydrated"
        elif score >= 65:
            status = "Mildly Dehydrated"
        else:
            status = "Significantly Dehydrated"

        return {
            "hydration_score": score,
            "current_liters": water_intake_liters,
            "target_liters": recommended_liters,
            "status": status,
            "deficit_liters": max(0.0, round(recommended_liters - water_intake_liters, 2)),
        }

    @staticmethod
    def calculate_sleep_score(sleep_hours: float) -> Dict[str, Any]:
        """
        Evaluate sleep duration quality against clinical sleep medicine recommendations (7-9 hrs).
        """
        if 7.0 <= sleep_hours <= 9.0:
            score = 100
            status = "Optimal Sleep Range"
        elif 6.0 <= sleep_hours < 7.0 or 9.0 < sleep_hours <= 10.0:
            score = 80
            status = "Sub-optimal Duration"
        elif 5.0 <= sleep_hours < 6.0:
            score = 60
            status = "Moderate Sleep Deficit"
        else:
            score = max(20, int(100 - abs(8.0 - sleep_hours) * 18))
            status = "Severe Sleep Deprivation / Excess"

        return {
            "sleep_score": score,
            "sleep_hours": sleep_hours,
            "status": status,
        }

    @staticmethod
    def calculate_lifestyle_score(
        smoking: str,
        alcohol: str,
        exercise_days: int,
        activity_level: str,
        stress: int,
        diet: str
    ) -> Dict[str, Any]:
        """
        Compute multi-factorial lifestyle score (0-100 index).
        """
        score = 100.0

        # Smoking penalty
        smoke_penalties = {
            "never": 0,
            "former": 5,
            "occasional": 15,
            "regular": 25,
            "heavy": 35,
        }
        score -= smoke_penalties.get(smoking.lower(), 10)

        # Alcohol penalty
        alc_penalties = {
            "none": 0,
            "light": 2,
            "moderate": 10,
            "heavy": 25,
        }
        score -= alc_penalties.get(alcohol.lower(), 5)

        # Exercise bonus / penalty
        if exercise_days >= 4:
            pass  # full points
        elif exercise_days >= 2:
            score -= 8
        else:
            score -= 18

        # Stress penalty (1-10)
        score -= max(0, (stress - 3) * 2.5)

        # Diet penalty
        if diet == "high_sodium_fat":
            score -= 15
        elif diet == "balanced" or diet == "vegetarian" or diet == "vegan":
            score -= 0
        else:
            score -= 5

        final_score = max(10, min(100, int(score)))

        if final_score >= 80:
            rating = "Excellent Healthy Habits"
        elif final_score >= 60:
            rating = "Moderate Lifestyle Risk"
        else:
            rating = "High Lifestyle Risk Factors"

        return {
            "lifestyle_score": final_score,
            "rating": rating,
        }

    @staticmethod
    def calculate_composite_health_score(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Holistically synthesize all biometric, cardiovascular, metabolic, and lifestyle parameters
        into a composite clinical health score (0-100) with diagnostic breakdown.
        """
        height_cm = float(metrics.get("height_cm", 175.0))
        weight_kg = float(metrics.get("weight_kg", 72.0))
        age = int(metrics.get("age", 35))
        sys_bp = int(metrics.get("systolic_bp", 120))
        dia_bp = int(metrics.get("diastolic_bp", 80))
        glucose = float(metrics.get("blood_glucose", 95.0))
        cholesterol = float(metrics.get("cholesterol", 185.0))
        resting_hr = int(metrics.get("heart_rate", 72))
        sleep_hours = float(metrics.get("sleep_hours", 7.5))
        water_liters = float(metrics.get("water_intake_liters", 2.5))
        smoking = metrics.get("smoking_status", "never")
        alcohol = metrics.get("alcohol_consumption", "none")
        exercise_days = int(metrics.get("exercise_frequency_days", 3))
        activity_level = metrics.get("physical_activity_level", "moderate")
        stress = int(metrics.get("stress_level", 4))
        diet = metrics.get("diet_type", "balanced")

        bmi_res = HealthCalculators.calculate_bmi(height_cm, weight_kg)
        bp_res = HealthCalculators.classify_blood_pressure(sys_bp, dia_bp)
        hr_res = HealthCalculators.classify_heart_rate(resting_hr, age)
        hydration_res = HealthCalculators.calculate_hydration_score(water_liters, weight_kg)
        sleep_res = HealthCalculators.calculate_sleep_score(sleep_hours)
        lifestyle_res = HealthCalculators.calculate_lifestyle_score(smoking, alcohol, exercise_days, activity_level, stress, diet)

        # Dimension scores (0 - 100)
        # 1. BMI Component (Target 18.5 - 24.9)
        bmi_val = bmi_res["bmi"]
        if 18.5 <= bmi_val <= 24.9:
            bmi_score = 100
        else:
            bmi_score = max(20, int(100 - abs(bmi_val - 22.0) * 5))

        # 2. Blood Pressure Component
        if bp_res["risk_tier"] == "LOW":
            bp_score = 100
        elif bp_res["risk_tier"] == "MILD":
            bp_score = 85
        elif bp_res["risk_tier"] == "MODERATE":
            bp_score = 65
        else:
            bp_score = 35

        # 3. Metabolic / Glucose Component (Fasting 70 - 99 mg/dL)
        if 70.0 <= glucose <= 99.0:
            glucose_score = 100
        elif glucose <= 125.0:
            glucose_score = 70  # pre-diabetes range
        else:
            glucose_score = max(20, int(100 - (glucose - 100) * 0.6))

        # 4. Cholesterol Component (< 200 mg/dL)
        if cholesterol < 200.0:
            chol_score = 100
        elif cholesterol < 240.0:
            chol_score = 75
        else:
            chol_score = max(20, int(100 - (cholesterol - 200) * 0.4))

        # Weighted Synthesis:
        # Cardiovascular (BP + HR): 25%
        # Metabolic (Glucose + Cholesterol): 25%
        # Biometrics (BMI): 20%
        # Lifestyle (Habits, Sleep, Hydration): 30%
        cardio_comp = (bp_score * 0.75) + (100 if 60 <= resting_hr <= 85 else 75) * 0.25
        metabolic_comp = (glucose_score * 0.55) + (chol_score * 0.45)
        biometric_comp = bmi_score
        lifestyle_comp = (
            lifestyle_res["lifestyle_score"] * 0.50 +
            sleep_res["sleep_score"] * 0.30 +
            hydration_res["hydration_score"] * 0.20
        )

        overall_health_score = int(
            (cardio_comp * 0.25) +
            (metabolic_comp * 0.25) +
            (biometric_comp * 0.20) +
            (lifestyle_comp * 0.30)
        )
        overall_health_score = max(10, min(100, overall_health_score))

        return {
            "overall_score": overall_health_score,
            "components": {
                "cardiovascular_score": int(cardio_comp),
                "metabolic_score": int(metabolic_comp),
                "biometric_score": int(biometric_comp),
                "lifestyle_score": int(lifestyle_comp),
            },
            "bmi_details": bmi_res,
            "bp_details": bp_res,
            "hr_details": hr_res,
            "hydration_details": hydration_res,
            "sleep_details": sleep_res,
            "lifestyle_details": lifestyle_res,
        }
