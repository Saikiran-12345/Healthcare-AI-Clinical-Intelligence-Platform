"""
Authentication and Profile Form Classes.
"""

from django import forms
from core.validators import Validator, ValidationError


class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Username or Email",
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username or email', 'autofocus': True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}),
    )


class PatientRegistrationForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. jsmith'}),
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. john@example.com'}),
    )
    first_name = forms.CharField(
        label="First Name",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John'}),
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doe'}),
    )
    phone = forms.CharField(
        label="Phone Number",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555 123 4567'}),
    )
    date_of_birth = forms.CharField(
        label="Date of Birth",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    gender = forms.ChoiceField(
        label="Gender",
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Minimum 8 characters with letters & numbers'}),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter your password'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password:
            try:
                Validator.validate_password(password)
            except ValidationError as exc:
                self.add_error("password", str(exc))

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data


class ProfileUpdateForm(forms.Form):
    first_name = forms.CharField(
        label="First Name",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    phone = forms.CharField(
        label="Phone Number",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    date_of_birth = forms.CharField(
        label="Date of Birth",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    gender = forms.ChoiceField(
        label="Gender",
        required=False,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    blood_group = forms.ChoiceField(
        label="Blood Group",
        required=False,
        choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    emergency_contact = forms.CharField(
        label="Emergency Contact",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name & phone of contact'}),
    )


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Min 8 chars, letters & numbers'}),
    )
    confirm_new_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm = cleaned_data.get("confirm_new_password")
        if new_password:
            try:
                Validator.validate_password(new_password)
            except ValidationError as exc:
                self.add_error("new_password", str(exc))

        if new_password and confirm and new_password != confirm:
            self.add_error("confirm_new_password", "New passwords do not match.")
        return cleaned_data
