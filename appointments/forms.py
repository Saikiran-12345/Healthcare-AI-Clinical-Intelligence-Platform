"""
Forms for Patient Appointment Requests and Doctor Consultation Scheduling.
"""

from django import forms
from appointments.services import AVAILABLE_TIME_SLOTS
from core.storage import db


class AppointmentBookingForm(forms.Form):
    doctor_id = forms.ChoiceField(
        label="Select Attending Physician",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'select_doctor'}),
    )
    appointment_date = forms.CharField(
        label="Consultation Date",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'input_appt_date'}),
    )
    appointment_time = forms.ChoiceField(
        label="Available Time Slot",
        choices=[(slot, slot) for slot in AVAILABLE_TIME_SLOTS],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'select_time_slot'}),
    )
    priority = forms.ChoiceField(
        label="Consultation Priority",
        choices=[
            ('Standard', 'Standard Routine Consultation'),
            ('Follow-up', 'Follow-up on Previous Assessment / Lab'),
            ('Urgent', 'Urgent / Acute Symptom Review'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    reason = forms.CharField(
        label="Reason for Visit / Chief Complaint *",
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Describe your symptoms, questions, or medical concerns...'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate active doctors
        doctors = db.doctors.find_all(filters={"is_available": True})
        choices = [(d["id"], f"{d['full_name']} ({d.get('specialization', 'General')})") for d in doctors]
        if not choices:
            choices = [('', 'No doctors currently available')]
        self.fields['doctor_id'].choices = choices


class AppointmentActionForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Decline / Reject'), ('complete', 'Mark Completed')],
        widget=forms.HiddenInput(),
    )
    doctor_notes = forms.CharField(
        label="Doctor Response / Instructions",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Optional instructions or reason...'}),
    )
