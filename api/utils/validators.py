"""
PulseGuard AI - Input Validation Helpers
"""

from typing import Tuple, Optional

REQUIRED_FEATURES = [
    "age", "gender", "bmi", "systolic_bp", "diastolic_bp",
    "heart_rate", "cholesterol", "glucose", "smoking",
    "alcohol", "physical_activity", "stress_level",
]

FEATURE_RANGES = {
    "age":               (1,   120),
    "gender":            (0,   1),
    "bmi":               (10,  70),
    "systolic_bp":       (60,  250),
    "diastolic_bp":      (40,  150),
    "heart_rate":        (30,  220),
    "cholesterol":       (100, 400),
    "glucose":           (40,  500),
    "smoking":           (0,   1),
    "alcohol":           (0,   1),
    "physical_activity": (0,   40),
    "stress_level":      (1,   10),
}


def validate_patient_input(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate patient clinical data for prediction.

    Returns:
        (True, None) if valid
        (False, error_message) if invalid
    """
    # Check all required fields present
    missing = [f for f in REQUIRED_FEATURES if f not in data]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    # Check types and ranges
    for field, (lo, hi) in FEATURE_RANGES.items():
        val = data.get(field)
        try:
            val = float(val)
        except (TypeError, ValueError):
            return False, f"Field '{field}' must be a number."

        if not (lo <= val <= hi):
            return False, f"Field '{field}' must be between {lo} and {hi}. Got {val}."

    return True, None


def validate_patient_profile(data: dict) -> Tuple[bool, Optional[str]]:
    """Validate basic patient profile fields."""
    required = ["name", "date_of_birth", "contact"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return False, f"Missing profile fields: {', '.join(missing)}"
    return True, None


def sanitize_input(data: dict) -> dict:
    """Cast all feature values to float."""
    return {
        k: (float(v) if k in REQUIRED_FEATURES else v)
        for k, v in data.items()
    }
