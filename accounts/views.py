"""
Authentication and User Profile Views for JSON Architecture.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from accounts.decorators import login_required_json
from accounts.forms import (
    LoginForm,
    PasswordChangeForm,
    PatientRegistrationForm,
    ProfileUpdateForm,
)
from accounts.services import AuthService
from core.exceptions import AuthenticationError, ValidationError
from core.storage import db


def get_client_ip(request) -> str:
    """Extract client IP address from HTTP headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def login_view(request):
    """Handle user authentication and session establishment."""
    # Seed default accounts on first access if none exist
    AuthService.seed_initial_accounts()

    if getattr(request, 'user', None) and request.user.is_authenticated:
        if request.user.role == 'patient':
            return redirect('/patients/dashboard/')
        elif request.user.role == 'doctor':
            return redirect('/doctors/dashboard/')
        elif request.user.role == 'admin':
            return redirect('/admin-panel/dashboard/')
        return redirect('/')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ident = form.cleaned_data['username_or_email']
        pwd = form.cleaned_data['password']
        ip = get_client_ip(request)

        try:
            user_record = AuthService.authenticate(ident, pwd, ip_address=ip)
            # Store authenticated user id in session
            request.session['user_id'] = user_record['id']
            request.session['user_role'] = user_record['role']
            request.session.modified = True

            messages.success(request, f"Welcome back, {user_record.get('first_name') or user_record['username']}!")

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if user_record['role'] == 'patient':
                return redirect('/patients/dashboard/')
            elif user_record['role'] == 'doctor':
                return redirect('/doctors/dashboard/')
            elif user_record['role'] == 'admin':
                return redirect('/admin-panel/dashboard/')
            return redirect('/')

        except AuthenticationError as e:
            messages.error(request, e.message)

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Handle new patient self-registration."""
    if getattr(request, 'user', None) and request.user.is_authenticated:
        return redirect('/')

    form = PatientRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        ip = get_client_ip(request)

        try:
            user_record = AuthService.register_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                role='patient',
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data.get('phone', ''),
                date_of_birth=data.get('date_of_birth', ''),
                gender=data.get('gender', 'other'),
                ip_address=ip,
            )

            # Auto login after registration
            request.session['user_id'] = user_record['id']
            request.session['user_role'] = user_record['role']
            request.session.modified = True

            messages.success(request, "Registration successful! Welcome to the HealthAI Platform.")
            return redirect('/patients/dashboard/')

        except (ValidationError, Exception) as e:
            messages.error(request, str(e))

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """Terminate user session."""
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        from core.audit import AuditAction, AuditLogger
        AuditLogger.log(
            action=AuditAction.LOGOUT,
            actor_id=user.id,
            actor_name=user.username,
            actor_role=user.role,
            ip_address=get_client_ip(request),
            status="SUCCESS",
        )

    request.session.flush()
    messages.info(request, "You have been securely signed out.")
    return redirect('/accounts/login/')


@login_required_json
def profile_view(request):
    """View and update account information."""
    user_record = db.users.get_by_id(request.user.id)
    patient_record = db.patients.find_one(filters={"user_id": request.user.id}) if request.user.role == 'patient' else None
    doctor_record = db.doctors.find_one(filters={"user_id": request.user.id}) if request.user.role == 'doctor' else None

    initial_data = {
        'first_name': user_record.get('first_name', ''),
        'last_name': user_record.get('last_name', ''),
        'phone': user_record.get('phone', ''),
    }

    if patient_record:
        initial_data.update({
            'date_of_birth': patient_record.get('date_of_birth', ''),
            'gender': patient_record.get('gender', 'male'),
            'blood_group': patient_record.get('blood_group', 'O+'),
            'emergency_contact': patient_record.get('emergency_contact', ''),
        })

    form = ProfileUpdateForm(request.POST or None, initial=initial_data)

    if request.method == 'POST' and form.is_valid():
        try:
            AuthService.update_profile(
                user_id=request.user.id,
                profile_data=form.cleaned_data,
                ip_address=get_client_ip(request),
            )
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('/accounts/profile/')
        except ValidationError as e:
            messages.error(request, e.message)

    context = {
        'form': form,
        'user_record': user_record,
        'patient_record': patient_record,
        'doctor_record': doctor_record,
    }
    return render(request, 'accounts/profile.html', context)


@login_required_json
def change_password_view(request):
    """Allow user to update password."""
    form = PasswordChangeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        old_pwd = form.cleaned_data['old_password']
        new_pwd = form.cleaned_data['new_password']
        try:
            AuthService.change_password(
                user_id=request.user.id,
                old_password=old_pwd,
                new_password=new_pwd,
                ip_address=get_client_ip(request),
            )
            messages.success(request, "Password updated successfully.")
            return redirect('/accounts/profile/')
        except ValidationError as e:
            messages.error(request, e.message)

    return render(request, 'accounts/change_password.html', {'form': form})
