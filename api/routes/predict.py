"""
PulseGuard AI - Prediction Routes
POST /api/predict/         → Single prediction
POST /api/predict/visit    → Predict + store visit + drift check
GET  /api/predict/risk/<patient_id> → Full risk history + drift
"""

from flask import Blueprint, request, jsonify
from utils.ml_engine import predict_hypertension, detect_risk_drift, build_risk_summary
from utils.validators import validate_patient_input, sanitize_input
from utils.db import add_visit, get_visits, get_patient, save_alert
from config import Config

predict_bp = Blueprint("predict", __name__)


# ─── POST /api/predict/ ───────────────────────────────────────────────────────
@predict_bp.route("/", methods=["POST"])
def predict():
    """
    Quick one-time prediction. Does NOT store to DB.

    Body (JSON):
    {
      "age": 45, "gender": 1, "bmi": 28.5,
      "systolic_bp": 145, "diastolic_bp": 92,
      "heart_rate": 78, "cholesterol": 220, "glucose": 100,
      "smoking": 0, "alcohol": 1, "physical_activity": 3,
      "stress_level": 7
    }
    """
    data = request.get_json(force=True)

    valid, error = validate_patient_input(data)
    if not valid:
        return jsonify({"error": error}), 400

    data   = sanitize_input(data)
    result = predict_hypertension(data)

    return jsonify({
        "success":    True,
        "prediction": result,
    }), 200


# ─── POST /api/predict/visit ──────────────────────────────────────────────────
@predict_bp.route("/visit", methods=["POST"])
def predict_and_store_visit():
    """
    Predict, store visit, and run drift detection.

    Body (JSON):
    {
      "patient_id": "abc123",
      "age": 45, ... (clinical features)
    }
    """
    data = request.get_json(force=True)

    patient_id = data.pop("patient_id", None)
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400

    valid, error = validate_patient_input(data)
    if not valid:
        return jsonify({"error": error}), 400

    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data   = sanitize_input(data)
    result = predict_hypertension(data)

    # Store visit
    visit_record = {**data, **result}
    visit_id = add_visit(patient_id, visit_record)

    # Drift detection
    all_visits  = get_visits(patient_id)
    risk_scores = [v["risk_score"] for v in all_visits]
    drift       = detect_risk_drift(
        risk_scores,
        drift_threshold  = Config.DRIFT_THRESHOLD,
        high_threshold   = Config.HIGH_DRIFT_THRESHOLD,
        window           = Config.DRIFT_WINDOW,
    )

    # Auto-save alert if needed
    alert_id = None
    if drift["alert_level"] in ("MODERATE", "HIGH"):
        alert_id = save_alert(patient_id, {
            "alert_level": drift["alert_level"],
            "message":     drift["message"],
            "risk_score":  result["risk_score"],
            "stage":       result["stage_label"],
            "visit_id":    visit_id,
        })

    return jsonify({
        "success":    True,
        "visit_id":   visit_id,
        "prediction": result,
        "drift":      drift,
        "alert_id":   alert_id,
    }), 201


# ─── GET /api/predict/risk/<patient_id> ───────────────────────────────────────
@predict_bp.route("/risk/<patient_id>", methods=["GET"])
def get_risk_history(patient_id: str):
    """
    Return full risk trajectory and drift summary for a patient.
    """
    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    visits = get_visits(patient_id)
    if not visits:
        return jsonify({"message": "No visits recorded yet.", "timeline": []}), 200

    summary = build_risk_summary(visits)

    return jsonify({
        "success":      True,
        "patient_id":   patient_id,
        "patient_name": patient.get("name", "N/A"),
        "total_visits": len(visits),
        **summary,
    }), 200
