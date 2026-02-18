"""
PulseGuard AI - MongoDB Database Helper
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/pulseguard")

_client = None
_db     = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db     = _client["pulseguard"]
    return _db


def serialize(doc) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def serialize_list(docs) -> list:
    return [serialize(d) for d in docs]


# ─── Patient CRUD ─────────────────────────────────────────────────────────────

def create_patient(data: dict) -> str:
    db  = get_db()
    data["created_at"] = datetime.utcnow().isoformat()
    data["visits"]     = []
    result = db.patients.insert_one(data)
    return str(result.inserted_id)


def get_patient(patient_id: str) -> dict:
    db  = get_db()
    doc = db.patients.find_one({"_id": ObjectId(patient_id)})
    return serialize(doc)


def get_all_patients(limit: int = 100) -> list:
    db   = get_db()
    docs = db.patients.find().limit(limit).sort("created_at", -1)
    return serialize_list(list(docs))


def update_patient(patient_id: str, data: dict) -> bool:
    db     = get_db()
    result = db.patients.update_one(
        {"_id": ObjectId(patient_id)},
        {"$set": {**data, "updated_at": datetime.utcnow().isoformat()}}
    )
    return result.modified_count > 0


def delete_patient(patient_id: str) -> bool:
    db     = get_db()
    result = db.patients.delete_one({"_id": ObjectId(patient_id)})
    return result.deleted_count > 0


# ─── Visit CRUD ───────────────────────────────────────────────────────────────

def add_visit(patient_id: str, visit_data: dict) -> str:
    db = get_db()
    visit_data["visit_date"] = datetime.utcnow().isoformat()
    visit_data["visit_id"]   = str(ObjectId())

    db.patients.update_one(
        {"_id": ObjectId(patient_id)},
        {"$push": {"visits": visit_data}}
    )
    return visit_data["visit_id"]


def get_visits(patient_id: str) -> list:
    patient = get_patient(patient_id)
    if not patient:
        return []
    return patient.get("visits", [])


# ─── Alert Storage ────────────────────────────────────────────────────────────

def save_alert(patient_id: str, alert_data: dict) -> str:
    db = get_db()
    alert_data["patient_id"]  = patient_id
    alert_data["created_at"]  = datetime.utcnow().isoformat()
    alert_data["acknowledged"] = False
    result = db.alerts.insert_one(alert_data)
    return str(result.inserted_id)


def get_alerts(patient_id: str = None, unacknowledged_only: bool = False) -> list:
    db    = get_db()
    query = {}
    if patient_id:
        query["patient_id"] = patient_id
    if unacknowledged_only:
        query["acknowledged"] = False
    docs = db.alerts.find(query).sort("created_at", -1)
    return serialize_list(list(docs))


def acknowledge_alert(alert_id: str) -> bool:
    db     = get_db()
    result = db.alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"acknowledged": True, "acknowledged_at": datetime.utcnow().isoformat()}}
    )
    return result.modified_count > 0
