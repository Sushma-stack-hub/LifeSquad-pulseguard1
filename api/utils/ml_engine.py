"""
PulseGuard AI - ML Inference & Risk Drift Detection Engine
"""

import os
import numpy as np
import joblib
from typing import List, Dict, Optional

# ─── Constants ────────────────────────────────────────────────────────────────
# Frontend sends these 12 fields
FRONTEND_FEATURES = [
    "age", "gender", "bmi", "systolic_bp", "diastolic_bp",
    "heart_rate", "cholesterol", "glucose", "smoking",
    "alcohol", "physical_activity", "stress_level",
]

# Model expects these 13 features (in order)
MODEL_FEATURES = [
    "Gender", "Age", "History", "Patient", "TakeMedication",
    "Severity", "BreathShortness", "VisualChanges", "NoseBleeding",
    "Whendiagnoused", "Systolic", "Diastolic", "ControlledDiet",
]

# Scaler expects these 5 features (in order)
SCALER_FEATURES = ["Age", "Severity", "Whendiagnoused", "Systolic", "Diastolic"]

STAGE_LABELS = {0: "Normal", 1: "Stage 1", 2: "Stage 2", 3: "Crisis"}
STAGE_COLORS = {0: "green", 1: "yellow", 2: "orange", 3: "red"}

MODEL_PATH  = os.path.join(os.path.dirname(__file__), "..", "models", "pulseguard_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "scaler.pkl")

# ─── Singleton Model Loader ────────────────────────────────────────────────────
_model  = None
_scaler = None


def _load_model():
    global _model, _scaler
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "Model not found. Run `python models/train_model.py` first."
            )
        _model  = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
    return _model, _scaler


def _map_frontend_to_model(data: dict) -> dict:
    """
    Map frontend clinical fields to the model's expected feature names.
    
    IMPORTANT: The model was trained on CATEGORICAL / ENCODED features, not raw values.
    Scaler ranges: Age(1-4), Severity(0-2), Whendiagnoused(1-3), Systolic(0-3), Diastolic(0-3)
    We must convert raw clinical values into these encoded ranges.
    """
    raw_age = data.get("age", 45)
    raw_sys = data.get("systolic_bp", 120)
    raw_dia = data.get("diastolic_bp", 80)

    # Encode Age: 1=young(<30), 2=middle(30-49), 3=senior(50-65), 4=elderly(>65)
    if raw_age < 30:
        age_enc = 1
    elif raw_age < 50:
        age_enc = 2
    elif raw_age <= 65:
        age_enc = 3
    else:
        age_enc = 4

    # Encode Systolic BP: 0=Normal(<120), 1=Elevated(120-129), 2=Stage1(130-139), 3=Stage2+(>=140)
    if raw_sys < 120:
        sys_enc = 0
    elif raw_sys < 130:
        sys_enc = 1
    elif raw_sys < 140:
        sys_enc = 2
    else:
        sys_enc = 3

    # Encode Diastolic BP: 0=Normal(<80), 1=Stage1(80-89), 2=Stage2(90-99), 3=Crisis(>=100)
    if raw_dia < 80:
        dia_enc = 0
    elif raw_dia < 90:
        dia_enc = 1
    elif raw_dia < 100:
        dia_enc = 2
    else:
        dia_enc = 3

    # Encode Severity: 0=low, 1=moderate, 2=severe (derived from BP stage)
    bp_max_enc = max(sys_enc, dia_enc)
    if bp_max_enc >= 3:
        severity = 2
    elif bp_max_enc >= 2:
        severity = 1
    else:
        severity = 0

    # Encode Whendiagnoused: 1=recently, 2=some time ago, 3=long time ago (default recently)
    whendiag = 1

    # Encode symptoms from frontend data
    heart_rate = data.get("heart_rate", 72)
    stress = data.get("stress_level", 5)
    smoking = data.get("smoking", 0)
    activity = data.get("physical_activity", 3)

    return {
        "Gender":          data.get("gender", 0),               # 0/1
        "Age":             age_enc,                               # 1-4
        "History":         1 if stress > 6 or smoking > 0 else 0, # 0/1
        "Patient":         0,                                     # 0/1 outpatient
        "TakeMedication":  0,                                     # 0/1
        "Severity":        severity,                              # 0-2
        "BreathShortness": 1 if heart_rate > 90 else 0,          # 0/1
        "VisualChanges":   1 if bp_max_enc >= 3 else 0,          # 0/1
        "NoseBleeding":    0,                                     # 0/1
        "Whendiagnoused":  whendiag,                              # 1-3
        "Systolic":        sys_enc,                               # 0-3
        "Diastolic":       dia_enc,                               # 0-3
        "ControlledDiet":  1 if activity >= 4 else 0,            # 0/1
    }


# ─── Core Prediction ──────────────────────────────────────────────────────────

def predict_hypertension(patient_data: dict) -> dict:
    """
    Predict hypertension stage and return risk probability score.

    Args:
        patient_data: dict with frontend clinical keys

    Returns:
        {
          "stage": int,
          "stage_label": str,
          "risk_score": float,   # 0.0 – 100.0
          "probabilities": dict,
          "color": str
        }
    """
    model, scaler = _load_model()

    # Map frontend data to model features
    mapped = _map_frontend_to_model(patient_data)

    # Scale only the 5 features the scaler expects
    scaler_vector = np.array([[mapped[f] for f in SCALER_FEATURES]], dtype=float)
    scaled_values = scaler.transform(scaler_vector)[0]

    # Build the full 13-feature vector, substituting scaled values
    scaled_map = dict(zip(SCALER_FEATURES, scaled_values))
    full_vector = []
    for f in MODEL_FEATURES:
        if f in scaled_map:
            full_vector.append(scaled_map[f])
        else:
            full_vector.append(float(mapped[f]))

    feature_array = np.array([full_vector], dtype=float)

    stage = int(model.predict(feature_array)[0])
    proba = model.predict_proba(feature_array)[0]

    # Risk score = probability of being in Stage 2 or Crisis
    risk_score = float((proba[2] + proba[3]) * 100)

    return {
        "stage":        stage,
        "stage_label":  STAGE_LABELS[stage],
        "risk_score":   round(risk_score, 2),
        "probabilities": {
            STAGE_LABELS[i]: round(float(p) * 100, 2) for i, p in enumerate(proba)
        },
        "color": STAGE_COLORS[stage],
    }


# ─── Risk Drift Detection Engine ──────────────────────────────────────────────

def detect_risk_drift(
    visit_scores: List[float],
    drift_threshold: float = 15.0,
    high_threshold: float = 25.0,
    window: int = 3,
) -> dict:
    """
    Analyze a patient's risk score trajectory across the last `window` visits.

    Args:
        visit_scores:     List of risk scores (0-100) in chronological order
        drift_threshold:  % change to trigger MODERATE alert
        high_threshold:   % change to trigger HIGH alert
        window:           Number of recent visits to analyze

    Returns:
        {
          "alert_level": "STABLE" | "MODERATE" | "HIGH",
          "drift_value": float,
          "slope": float,
          "trend": "INCREASING" | "DECREASING" | "STABLE",
          "message": str,
          "analyzed_scores": list
        }
    """
    if len(visit_scores) < 2:
        return {
            "alert_level":    "STABLE",
            "drift_value":    0.0,
            "slope":          0.0,
            "trend":          "STABLE",
            "message":        "Insufficient visit data for drift analysis.",
            "analyzed_scores": visit_scores,
        }

    recent = visit_scores[-window:]

    # Compute slope via linear regression over recent visits
    x      = np.arange(len(recent), dtype=float)
    slope  = float(np.polyfit(x, recent, 1)[0])

    # Drift = absolute change from first to last in window
    drift_value = float(recent[-1] - recent[0])

    # Determine trend
    if slope > 0.5:
        trend = "INCREASING"
    elif slope < -0.5:
        trend = "DECREASING"
    else:
        trend = "STABLE"

    # Alert logic: drift AND positive slope required for alert
    if drift_value >= high_threshold and slope > 0:
        alert_level = "HIGH"
        message = (
            f"⚠️ HIGH ALERT: Patient risk has increased by {drift_value:.1f}% "
            f"over the last {len(recent)} visits (slope={slope:.1f}). "
            "Immediate clinical intervention recommended."
        )
    elif drift_value >= drift_threshold and slope > 0:
        alert_level = "MODERATE"
        message = (
            f"⚠️ MODERATE ALERT: Risk drift of {drift_value:.1f}% detected "
            f"(slope={slope:.1f}). Schedule follow-up within 2 weeks."
        )
    else:
        alert_level = "STABLE"
        message = f"Patient risk is stable (drift={drift_value:.1f}%, slope={slope:.1f})."

    return {
        "alert_level":    alert_level,
        "drift_value":    round(drift_value, 2),
        "slope":          round(slope, 2),
        "trend":          trend,
        "message":        message,
        "analyzed_scores": [round(s, 2) for s in recent],
    }


# ─── Helper: Build Patient Risk History Summary ────────────────────────────────

def build_risk_summary(visits: List[Dict]) -> dict:
    """
    Given a list of visit dicts (each with 'risk_score', 'stage_label', 'visit_date'),
    return drift analysis plus a formatted timeline.
    """
    scores  = [v["risk_score"] for v in visits]
    drift   = detect_risk_drift(scores)

    timeline = [
        {
            "visit_number": i + 1,
            "visit_date":   v.get("visit_date", "N/A"),
            "stage":        v.get("stage_label", "Unknown"),
            "risk_score":   v.get("risk_score", 0),
            "alert":        "⚠ HIGH ALERT"
                            if v["risk_score"] >= 70 else (
                            "Drifting"
                            if v["risk_score"] >= 50 else "Stable"),
        }
        for i, v in enumerate(visits)
    ]

    return {"drift_analysis": drift, "timeline": timeline}
