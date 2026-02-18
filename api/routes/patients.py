"""
PulseGuard AI - Patient Management Routes
POST   /api/patients/           → Create patient
GET    /api/patients/           → List all patients
GET    /api/patients/<id>       → Get patient by ID
PUT    /api/patients/<id>       → Update patient
DELETE /api/patients/<id>       → Delete patient
GET    /api/patients/<id>/visits → Get visit history
GET    /api/patients/<id>/alerts → Get alerts
POST   /api/patients/alerts/<id>/acknowledge → Acknowledge alert
"""

from flask import Blueprint, request, jsonify
from utils.db import (
    create_patient, get_patient, get_all_patients,
    update_patient, delete_patient, get_visits,
    get_alerts, acknowledge_alert,
)
from utils.validators import validate_patient_profile

patients_bp = Blueprint("patients", __name__)


# ─── POST /api/patients/ ──────────────────────────────────────────────────────
@patients_bp.route("/", methods=["POST"])
def create():
    """
    Create a new patient profile.

    Body (JSON):
    {
      "name": "John Doe",
      "date_of_birth": "1978-05-12",
      "gender": "Male",
      "contact": "+91-9876543210",
      "address": "Hyderabad, India",
      "doctor_id": "doc_001"   (optional)
    }
    """
    data = request.get_json(force=True)

    valid, error = validate_patient_profile(data)
    if not valid:
        return jsonify({"error": error}), 400

    patient_id = create_patient(data)
    return jsonify({"success": True, "patient_id": patient_id}), 201


# ─── GET /api/patients/ ───────────────────────────────────────────────────────
@patients_bp.route("/", methods=["GET"])
def list_patients():
    limit    = int(request.args.get("limit", 100))
    patients = get_all_patients(limit=limit)
    return jsonify({"success": True, "count": len(patients), "patients": patients}), 200


# ─── GET /api/patients/<id> ───────────────────────────────────────────────────
@patients_bp.route("/<patient_id>", methods=["GET"])
def get(patient_id):
    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    return jsonify({"success": True, "patient": patient}), 200


# ─── PUT /api/patients/<id> ───────────────────────────────────────────────────
@patients_bp.route("/<patient_id>", methods=["PUT"])
def update(patient_id):
    data    = request.get_json(force=True)
    updated = update_patient(patient_id, data)
    if not updated:
        return jsonify({"error": "Patient not found or nothing to update"}), 404
    return jsonify({"success": True}), 200


# ─── DELETE /api/patients/<id> ────────────────────────────────────────────────
@patients_bp.route("/<patient_id>", methods=["DELETE"])
def delete(patient_id):
    deleted = delete_patient(patient_id)
    if not deleted:
        return jsonify({"error": "Patient not found"}), 404
    return jsonify({"success": True}), 200


# ─── GET /api/patients/<id>/visits ───────────────────────────────────────────
@patients_bp.route("/<patient_id>/visits", methods=["GET"])
def visit_history(patient_id):
    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    visits = get_visits(patient_id)
    return jsonify({
        "success":      True,
        "patient_id":   patient_id,
        "total_visits": len(visits),
        "visits":       visits,
    }), 200


# ─── GET /api/patients/<id>/alerts ───────────────────────────────────────────
@patients_bp.route("/<patient_id>/alerts", methods=["GET"])
def patient_alerts(patient_id):
    unread_only = request.args.get("unread", "false").lower() == "true"
    alerts      = get_alerts(patient_id=patient_id, unacknowledged_only=unread_only)
    return jsonify({"success": True, "alerts": alerts}), 200


# ─── GET /api/patients/alerts/all ─────────────────────────────────────────────
@patients_bp.route("/alerts/all", methods=["GET"])
def all_alerts():
    """Get all alerts across all patients (doctor dashboard)."""
    unread_only = request.args.get("unread", "false").lower() == "true"
    alerts      = get_alerts(unacknowledged_only=unread_only)
    return jsonify({"success": True, "count": len(alerts), "alerts": alerts}), 200


# ─── POST /api/patients/alerts/<alert_id>/acknowledge ─────────────────────────
@patients_bp.route("/alerts/<alert_id>/acknowledge", methods=["POST"])
def ack_alert(alert_id):
    success = acknowledge_alert(alert_id)
    if not success:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify({"success": True}), 200
