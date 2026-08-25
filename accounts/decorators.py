"""
Role-Based Access Control (RBAC) Decorators for JSON Authentication.
Enforces authentication and role permissions without Django DB auth.
"""

from functools import wraps
from typing import Callable, List, Union
from django.contrib import messages
from django.shortcuts import redirect


def login_required_json(view_func: Callable) -> Callable:
    """Decorator ensuring that user is authenticated in current session."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            messages.warning(request, "Please sign in to access this page.")
            return redirect(f"/accounts/login/?next={request.path}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(allowed_roles: Union[str, List[str]]) -> Callable:
    """Decorator ensuring that authenticated user has one of the required roles."""
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                messages.warning(request, "Please sign in to continue.")
                return redirect(f"/accounts/login/?next={request.path}")

            if request.user.role not in allowed_roles:
                messages.error(request, "You do not have permission to access this clinical area.")
                # Redirect to appropriate home for user's actual role
                if request.user.role == 'patient':
                    return redirect('/patients/dashboard/')
                elif request.user.role == 'doctor':
                    return redirect('/doctors/dashboard/')
                elif request.user.role == 'admin':
                    return redirect('/admin-panel/dashboard/')
                return redirect('/')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def patient_required(view_func: Callable) -> Callable:
    """Convenience decorator restricting access to Patients only."""
    return role_required(['patient'])(view_func)


def doctor_required(view_func: Callable) -> Callable:
    """Convenience decorator restricting access to Doctors only."""
    return role_required(['doctor'])(view_func)


def admin_required(view_func: Callable) -> Callable:
    """Convenience decorator restricting access to System Administrators only."""
    return role_required(['admin'])(view_func)


def doctor_or_admin_required(view_func: Callable) -> Callable:
    """Convenience decorator allowing either Doctors or Administrators."""
    return role_required(['doctor', 'admin'])(view_func)
