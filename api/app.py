"""
PulseGuard AI - Main Flask Application
Intelligent Blood Pressure Prediction & Monitoring System
"""

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

from routes.predict import predict_bp
from routes.patients import patients_bp
from routes.chatbot import chatbot_bp
from routes.auth import auth_bp
from routes.report import report_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(predict_bp, url_prefix="/api/predict")
    app.register_blueprint(patients_bp, url_prefix="/api/patients")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(report_bp, url_prefix="/api/report")

    @app.route("/")
    def health_check():
        return {"status": "PulseGuard AI Backend Running", "version": "1.0.0"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5001)