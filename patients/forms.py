"""
Patient Forms for Comprehensive Health Assessments, Medical Records, and Symptoms.
"""

from django import forms


class HealthAssessmentForm(forms.Form):
    # Demographics & Biometrics
    age = forms.IntegerField(
        label="Age (Years)",
        min_value=1,
        max_value=120,
        initial=35,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    gender = forms.ChoiceField(
        label="Gender",
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        initial='male',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    height_cm = forms.FloatField(
        label="Height (cm)",
        min_value=50.0,
        max_value=250.0,
        initial=175.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'id': 'input_height'}),
    )
    weight_kg = forms.FloatField(
        label="Weight (kg)",
        min_value=2.0,
        max_value=350.0,
        initial=72.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'id': 'input_weight'}),
    )

    # Vitals & Labs
    systolic_bp = forms.IntegerField(
        label="Systolic Blood Pressure (mmHg)",
        min_value=60,
        max_value=260,
        initial=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Standard upper blood pressure reading.",
    )
    diastolic_bp = forms.IntegerField(
        label="Diastolic Blood Pressure (mmHg)",
        min_value=40,
        max_value=160,
        initial=80,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Standard lower blood pressure reading.",
    )
    heart_rate = forms.IntegerField(
        label="Resting Heart Rate (bpm)",
        min_value=30,
        max_value=220,
        initial=72,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    blood_glucose = forms.FloatField(
        label="Fasting Blood Glucose (mg/dL)",
        min_value=40.0,
        max_value=500.0,
        initial=95.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        help_text="Normal fasting range: 70-99 mg/dL.",
    )
    cholesterol = forms.FloatField(
        label="Total Serum Cholesterol (mg/dL)",
        min_value=80.0,
        max_value=500.0,
        initial=185.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        help_text="Desirable level: < 200 mg/dL.",
    )

    # Lifestyle Factors
    smoking_status = forms.ChoiceField(
        label="Smoking Status",
        choices=[
            ('never', 'Never Smoked'),
            ('former', 'Former Smoker'),
            ('occasional', 'Occasional Smoker (< 5 cigarettes/day)'),
            ('regular', 'Regular Smoker (10-20 cigarettes/day)'),
            ('heavy', 'Heavy Smoker (> 20 cigarettes/day)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    alcohol_consumption = forms.ChoiceField(
        label="Alcohol Consumption",
        choices=[
            ('none', 'None / Non-Drinker'),
            ('light', 'Light (1-2 drinks/week)'),
            ('moderate', 'Moderate (3-7 drinks/week)'),
            ('heavy', 'Heavy (> 7 drinks/week)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    physical_activity_level = forms.ChoiceField(
        label="Physical Activity Level",
        choices=[
            ('sedentary', 'Sedentary (Little to no activity)'),
            ('light', 'Light (Casual walking 1-2 days/week)'),
            ('moderate', 'Moderate (Exercise 3-4 days/week)'),
            ('active', 'Active (Intense workout 5+ days/week)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    exercise_frequency_days = forms.IntegerField(
        label="Weekly Exercise Frequency (Days)",
        min_value=0,
        max_value=7,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    sleep_hours = forms.FloatField(
        label="Average Sleep Duration (Hours/Night)",
        min_value=1.0,
        max_value=24.0,
        initial=7.5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
    )
    water_intake_liters = forms.FloatField(
        label="Daily Water Intake (Liters)",
        min_value=0.0,
        max_value=15.0,
        initial=2.5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
    )
    stress_level = forms.IntegerField(
        label="Self-Reported Stress Level (1-10)",
        min_value=1,
        max_value=10,
        initial=4,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    diet_type = forms.ChoiceField(
        label="Dietary Pattern",
        choices=[
            ('balanced', 'Balanced Mediterranean / Whole Foods'),
            ('vegetarian', 'Vegetarian / Plant-Based'),
            ('vegan', 'Strict Vegan'),
            ('low_carb', 'Low Carbohydrate / Keto'),
            ('high_sodium_fat', 'High Sodium / Processed Foods'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    # Family Medical History Flags
    fam_diabetes = forms.BooleanField(label="Family History of Diabetes", required=False)
    fam_heart_disease = forms.BooleanField(label="Family History of Heart Disease", required=False)
    fam_hypertension = forms.BooleanField(label="Family History of Hypertension", required=False)
    fam_kidney_disease = forms.BooleanField(label="Family History of Kidney Disease", required=False)

    def clean(self):
        cleaned_data = super().clean()
        sys_bp = cleaned_data.get("systolic_bp")
        dia_bp = cleaned_data.get("diastolic_bp")

        if sys_bp and dia_bp and dia_bp >= sys_bp:
            self.add_error("diastolic_bp", "Diastolic blood pressure must be lower than systolic blood pressure.")

        return cleaned_data


class MedicalHistoryForm(forms.Form):
    condition = forms.CharField(
        label="Medical Condition / Diagnosis",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Type 2 Diabetes, Asthma, Migraine'}),
    )
    diagnosis_date = forms.CharField(
        label="Date of Diagnosis",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    status = forms.ChoiceField(
        label="Current Status",
        choices=[
            ('Active', 'Active Condition'),
            ('In Treatment', 'Under Active Treatment'),
            ('Managed', 'Well Managed'),
            ('Resolved', 'Resolved / In Remission'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    severity = forms.ChoiceField(
        label="Severity",
        choices=[
            ('Mild', 'Mild (Minimal daily impact)'),
            ('Moderate', 'Moderate (Periodic symptoms)'),
            ('Severe', 'Severe (Requires ongoing monitoring)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    notes = forms.CharField(
        label="Clinical Notes / Prescriptions",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Current medications, dosage, attending physician notes...'}),
    )


class SymptomEntryForm(forms.Form):
    symptom_name = forms.CharField(
        label="Symptom Name",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Shortness of breath, Chest tightness, Fatigue'}),
    )
    category = forms.ChoiceField(
        label="Category",
        choices=[
            ('General', 'General / Systemic'),
            ('Cardiovascular', 'Cardiovascular / Heart'),
            ('Respiratory', 'Respiratory / Lungs'),
            ('Metabolic', 'Metabolic / Endocrine'),
            ('Renal', 'Renal / Urinary'),
            ('Neurological', 'Neurological / Headaches'),
            ('Gastrointestinal', 'Gastrointestinal'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    severity = forms.ChoiceField(
        label="Severity (1: Mild to 5: Extreme)",
        choices=[(1, '1 - Very Mild'), (2, '2 - Mild'), (3, '3 - Moderate'), (4, '4 - Severe'), (5, '5 - Very Severe / Critical')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    duration_days = forms.IntegerField(
        label="Duration (Days Present)",
        min_value=1,
        max_value=365,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    frequency = forms.ChoiceField(
        label="Frequency",
        choices=[
            ('Daily', 'Constant / Daily'),
            ('Frequent', 'Frequent (Multiple times a day)'),
            ('Intermittent', 'Intermittent (Comes and goes)'),
            ('Occasional', 'Occasional (1-2 times a week)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    notes = forms.CharField(
        label="Observations & Triggers",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Triggers, time of day, relief factors...'}),
    )
