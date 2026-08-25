"""
Doctor & Clinical Practice Forms.
"""

from django import forms


class ClinicalNoteForm(forms.Form):
    subjective = forms.CharField(
        label="Subjective / Patient Symptoms",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Patient complaints, timeline, subjective feedback...'}),
    )
    assessment = forms.CharField(
        label="Clinical Assessment / Diagnosis *",
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Clinical evaluation, diagnosis, risk analysis...'}),
    )
    plan = forms.CharField(
        label="Treatment Plan / Lifestyle Interventions",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Therapy, lifestyle advice, diet adjustments, monitoring...'}),
    )
    prescriptions = forms.CharField(
        label="Prescriptions / Medications",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Metformin 500mg daily, Lisinopril 10mg once daily'}),
    )
    follow_up_date = forms.CharField(
        label="Recommended Follow-up Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )


class PatientSearchForm(forms.Form):
    q = forms.CharField(
        label="Search Patients",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name, email, or username...'}),
    )
    risk_level = forms.ChoiceField(
        label="Risk Level",
        required=False,
        choices=[
            ('ALL', 'All Risk Tiers'),
            ('HIGH', 'High Risk Only'),
            ('MODERATE', 'Moderate Risk'),
            ('LOW', 'Low Risk'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class DoctorProfileForm(forms.Form):
    specialization = forms.CharField(
        label="Specialization",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    department = forms.CharField(
        label="Clinical Department",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    license_number = forms.CharField(
        label="Medical License Number",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    consultation_hours = forms.CharField(
        label="Consultation Hours",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 09:00 - 17:00'}),
    )
    is_available = forms.BooleanField(
        label="Currently Accepting New Patient Consultations",
        required=False,
    )
