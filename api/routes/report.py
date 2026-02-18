"""
PulseGuard AI - PDF Report Route

POST /api/report/generate          → Generate PDF from raw inputs (no DB needed)
GET  /api/report/patient/<id>      → Generate PDF from stored patient + latest visit
"""

from flask import Blueprint, request, jsonify, send_file
import io
from datetime import datetime

from utils.pdf_report import generate_bp_report_pdf
from utils.ml_engine import predict_hypertension, detect_risk_drift
from utils.validators import validate_patient_input, sanitize_input
from utils.db import get_patient, get_visits

report_bp = Blueprint("report", __name__)


# ─── POST /api/report/generate ────────────────────────────────────────────────
@report_bp.route("/generate", methods=["POST"])
def generate_report():
    """
    Generate and download a PDF report from raw inputs (no patient ID needed).
    Great for a quick demo without MongoDB.

    Body (JSON):
    {
      "patient_data": {
        "name": "John Doe",
        "date_of_birth": "1978-05-12",
        "gender": "Male",
        "contact": "+91-9876543210",
        "address": "Hyderabad, India"
      },
      "clinical_inputs": {
        "age": 45, "gender": 1, "bmi": 28.5,
        "systolic_bp": 145, "diastolic_bp": 92,
        "heart_rate": 78, "cholesterol": 220, "glucose": 100,
        "smoking": 0, "alcohol": 1, "physical_activity": 3, "stress_level": 7
      },
      "recommendations": "Reduce salt intake, walk 30 min daily..."  // optional
    }
    """
    data = request.get_json(force=True)

    patient_data    = data.get("patient_data", {})
    clinical_inputs = data.get("clinical_inputs", {})
    recommendations = data.get("recommendations", "")

    # Validate clinical inputs
    valid, error = validate_patient_input(clinical_inputs)
    if not valid:
        return jsonify({"error": error}), 400

    clinical_inputs = sanitize_input(clinical_inputs)

    # Run prediction
    prediction_results = predict_hypertension(clinical_inputs)

    # Auto-generate recommendations if not provided
    if not recommendations:
        recommendations = _default_recommendations(prediction_results["stage_label"])

    # Generate PDF
    pdf_bytes = generate_bp_report_pdf(
        patient_data       = patient_data,
        clinical_inputs    = clinical_inputs,
        prediction_results = prediction_results,
        recommendations    = recommendations,
    )

    filename = f"PulseGuard_Report_{patient_data.get('name', 'Patient').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


# ─── GET /api/report/patient/<patient_id> ─────────────────────────────────────
@report_bp.route("/patient/<patient_id>", methods=["GET"])
def generate_patient_report(patient_id: str):
    """
    Generate PDF report for a stored patient using their latest visit data.
    Requires MongoDB to be running.
    """
    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    visits = get_visits(patient_id)
    if not visits:
        return jsonify({"error": "No visits recorded for this patient yet."}), 404

    # Use latest visit
    latest_visit = visits[-1]

    # Build clinical inputs from stored visit
    clinical_keys = [
        "age", "gender", "bmi", "systolic_bp", "diastolic_bp",
        "heart_rate", "cholesterol", "glucose", "smoking",
        "alcohol", "physical_activity", "stress_level",
    ]
    clinical_inputs = {k: latest_visit.get(k, 0) for k in clinical_keys}

    # Build prediction results from stored visit
    prediction_results = {
        "stage":        latest_visit.get("stage", 0),
        "stage_label":  latest_visit.get("stage_label", "Unknown"),
        "risk_score":   latest_visit.get("risk_score", 0.0),
        "probabilities": latest_visit.get("probabilities", {}),
        "alert_level":  latest_visit.get("alert_level", "STABLE"),
    }

    # Drift detection across all visits
    if len(visits) >= 2:
        risk_scores = [v["risk_score"] for v in visits]
        drift = detect_risk_drift(risk_scores)
        prediction_results["alert_level"] = drift["alert_level"]

    recommendations = _default_recommendations(prediction_results["stage_label"])

    # Generate PDF
    pdf_bytes = generate_bp_report_pdf(
        patient_data       = {**patient, "patient_id": patient_id},
        clinical_inputs    = clinical_inputs,
        prediction_results = prediction_results,
        recommendations    = recommendations,
    )

    filename = f"PulseGuard_{patient.get('name', 'Patient').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


# ─── Helper: Default Recommendations ──────────────────────────────────────────

def _default_recommendations(stage_label: str) -> str:
    recs = {
        "Normal": (
            "Great news! Your blood pressure is in the healthy range.\n\n"
            "• Maintain your current healthy lifestyle\n"
            "• Stay physically active — aim for 150 minutes of exercise per week\n"
            "• Continue eating a balanced diet rich in fruits and vegetables\n"
            "• Get 7-8 hours of quality sleep every night\n"
            "• Manage stress through mindfulness or yoga\n"
            "• Monitor your BP regularly every 6-12 months\n"
        ),
        "Stage 1": (
            "Your blood pressure is mildly elevated. Lifestyle changes can make a big difference.\n\n"
            "• Reduce sodium intake to less than 2,300 mg/day\n"
            "• Follow the DASH diet — fruits, vegetables, whole grains, low-fat dairy\n"
            "• Exercise at least 30 minutes a day, 5 days a week\n"
            "• Limit alcohol consumption\n"
            "• Quit smoking if applicable\n"
            "• Lose weight if BMI is above 25\n"
            "• Monitor BP at home daily\n"
            "• Schedule a follow-up with your doctor within 3 months\n"
        ),
        "Stage 2": (
            "Your blood pressure is significantly elevated. Please take action.\n\n"
            "• Consult your doctor immediately — medication may be required\n"
            "• Strictly reduce salt intake to less than 1,500 mg/day\n"
            "• Avoid all processed and packaged foods\n"
            "• Stop smoking and alcohol completely\n"
            "• Monitor BP twice daily and keep a log\n"
            "• Practice stress management daily (meditation, breathing exercises)\n"
            "• Avoid heavy physical exertion until cleared by your doctor\n"
            "• Follow up with your doctor every 2-4 weeks\n"
        ),
        "Crisis": (
            "WARNING: Your blood pressure is at a critical level.\n\n"
            "SEEK IMMEDIATE MEDICAL ATTENTION.\n\n"
            "• Call emergency services or go to the nearest ER immediately\n"
            "• Do NOT delay or wait for symptoms to worsen\n"
            "• Avoid any physical activity or stress\n"
            "• If prescribed medication, take it as directed immediately\n"
            "• This level of BP can cause stroke, heart attack, or organ damage\n"
        ),
    }
    return recs.get(stage_label, "Please consult your healthcare provider for personalized recommendations.")