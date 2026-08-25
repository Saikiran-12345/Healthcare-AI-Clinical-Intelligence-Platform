"""
Core views for landing page, health calculators hub, and error pages.
"""

from django.shortcuts import render
from core.storage import db


def home_view(request):
    """Render application landing page with system statistics summary."""
    context = {
        'total_patients': db.patients.count(),
        'total_doctors': db.doctors.count(),
        'total_predictions': db.predictions.count(),
    }
    return render(request, 'home.html', context)
