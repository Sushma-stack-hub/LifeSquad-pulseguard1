"""
PulseGuard AI - Authentication Routes (JWT-based)
POST /api/auth/register  → Register doctor/admin
POST /api/auth/login     → Login
GET  /api/auth/me        → Get current user
"""

from flask import Blueprint, request, jsonify, current_app
from utils.db import get_db
from datetime import datetime, timedelta
import hashlib
import hmac
import jwt
import os

auth_bp = Blueprint("auth", __name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "pulseguard-secret-key-change-in-prod")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role":    role,
        "exp":     datetime.utcnow() + timedelta(hours=24),
        "iat":     datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ─── POST /api/auth/register ──────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new doctor or admin user.

    Body:
    {
      "name": "Dr. Priya Sharma",
      "email": "priya@hospital.com",
      "password": "SecurePass123",
      "role": "doctor"   // "doctor" | "admin"
    }
    """
    data = request.get_json(force=True)

    required = ["name", "email", "password", "role"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if data["role"] not in ("doctor", "admin"):
        return jsonify({"error": "role must be 'doctor' or 'admin'"}), 400

    db = get_db()
    if db.users.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 409

    user = {
        "name":       data["name"],
        "email":      data["email"].lower(),
        "password":   hash_password(data["password"]),
        "role":       data["role"],
        "created_at": datetime.utcnow().isoformat(),
    }
    result  = db.users.insert_one(user)
    user_id = str(result.inserted_id)
    token   = generate_token(user_id, data["role"])

    return jsonify({
        "success":  True,
        "user_id":  user_id,
        "token":    token,
        "role":     data["role"],
    }), 201


# ─── POST /api/auth/login ─────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Body: { "email": "...", "password": "..." }
    """
    data = request.get_json(force=True)
    email    = data.get("email", "").lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    db   = get_db()
    user = db.users.find_one({"email": email})

    if not user or user["password"] != hash_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    user_id = str(user["_id"])
    token   = generate_token(user_id, user["role"])

    return jsonify({
        "success": True,
        "token":   token,
        "user":    {
            "id":    user_id,
            "name":  user["name"],
            "email": user["email"],
            "role":  user["role"],
        },
    }), 200


# ─── GET /api/auth/me ─────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
def me():
    """
    Return current user from Bearer token.
    Header: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token   = auth_header.split(" ", 1)[1]
    payload = verify_token(token)

    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401

    from bson import ObjectId
    db   = get_db()
    user = db.users.find_one({"_id": ObjectId(payload["user_id"])})

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "success": True,
        "user": {
            "id":    str(user["_id"]),
            "name":  user["name"],
            "email": user["email"],
            "role":  user["role"],
        }
    }), 200
