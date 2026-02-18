"""
PulseGuard AI - Configuration
"""

import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "pulseguard-secret-key-change-in-prod")
    DEBUG = os.environ.get("DEBUG", True)

    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/pulseguard")

    # JWT
    JWT_EXPIRATION = timedelta(hours=24)

    # OpenAI (for chatbot)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # Model path
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "pulseguard_model.pkl")
    SCALER_PATH = os.path.join(os.path.dirname(__file__), "models", "scaler.pkl")

    # Risk Drift Detection thresholds
    DRIFT_THRESHOLD = 15       # % increase to trigger MODERATE alert
    HIGH_DRIFT_THRESHOLD = 25  # % increase to trigger HIGH alert
    DRIFT_WINDOW = 3           # Number of visits to analyze
