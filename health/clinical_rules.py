"""
Clinical Reference Standards & Physiological Guidelines (AHA, WHO, ACC).
"""

class ClinicalStandards:
    # BMI WHO Categories
    BMI_UNDERWEIGHT = 18.5
    BMI_NORMAL_MAX = 24.9
    BMI_OVERWEIGHT_MAX = 29.9
    BMI_OBESE_1_MAX = 34.9
    BMI_OBESE_2_MAX = 39.9

    # Blood Pressure AHA 2017 Guidelines (mmHg)
    BP_NORMAL_SYS = 120
    BP_NORMAL_DIA = 80
    BP_ELEVATED_SYS = 129
    BP_STAGE1_SYS = 139
    BP_STAGE1_DIA = 89
    BP_CRISIS_SYS = 180
    BP_CRISIS_DIA = 120

    # Glucose Reference Ranges (mg/dL) - Fasting
    GLUCOSE_NORMAL_MIN = 70.0
    GLUCOSE_NORMAL_MAX = 99.0
    GLUCOSE_PREDIABETES_MAX = 125.0

    # Total Cholesterol Ranges (mg/dL)
    CHOLESTEROL_DESIRABLE = 200.0
    CHOLESTEROL_BORDERLINE_MAX = 239.0

    # Resting Heart Rate (bpm)
    HR_BRADYCARDIA_THRESHOLD = 60
    HR_TACHYCARDIA_THRESHOLD = 100

    # Daily Water Intake Base Factor (Liters per kg body weight)
    WATER_PER_KG_ML = 35.0  # 35 ml per kg
