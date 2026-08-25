"""
Health Services Layer coordinating physiological evaluations and patient vital snapshots.
"""

from typing import Any, Dict, Optional
from health.calculators import HealthCalculators


class HealthService:
    """Service facade for health and clinical metrics calculations."""

    @staticmethod
    def evaluate_patient_vitals(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full suite of health calculations on a vital records payload."""
        return HealthCalculators.calculate_composite_health_score(metrics)
