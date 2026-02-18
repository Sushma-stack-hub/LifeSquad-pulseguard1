# PulseGuard AI — Backend

> Intelligent Blood Pressure Prediction & Monitoring System  
> Flask · Scikit-learn · MongoDB · LangChain/OpenAI

---

## Project Structure

```
pulseguard_backend/
├── app.py                    # Flask app factory & entry point
├── config.py                 # Configuration & env variables
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── models/
│   └── train_model.py        # Model training script (run once)
│
├── routes/
│   ├── predict.py            # /api/predict — ML inference & drift
│   ├── patients.py           # /api/patients — CRUD + visit history
│   ├── chatbot.py            # /api/chatbot — AI explanations
│   └── auth.py               # /api/auth — JWT authentication
│
└── utils/
    ├── ml_engine.py          # predict_hypertension() + detect_risk_drift()
    ├── db.py                 # MongoDB helpers
    └── validators.py         # Input validation
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the model (required once)
```bash
python models/train_model.py
```
This trains Logistic Regression on 1,825 synthetic patient records and saves:
- `models/pulseguard_model.pkl`
- `models/scaler.pkl`

### 3. Set environment variables
```bash
cp .env.example .env
# Edit .env with your MongoDB URI and OpenAI key
```

### 4. Run the server
```bash
python app.py
# Server starts at http://localhost:5000
```

### Docker (recommended)
```bash
docker-compose up --build
```

---

## API Reference

### Base URL: `http://localhost:5000/api`

---

### 🔐 Auth

#### Register
```
POST /auth/register
Body: { "name", "email", "password", "role": "doctor"|"admin" }
Response: { "token", "user_id", "role" }
```

#### Login
```
POST /auth/login
Body: { "email", "password" }
Response: { "token", "user" }
```

#### Get current user
```
GET /auth/me
Header: Authorization: Bearer <token>
```

---

### 👤 Patients

#### Create patient
```
POST /patients/
Body: { "name", "date_of_birth", "gender", "contact", "address" }
```

#### List patients
```
GET /patients/?limit=100
```

#### Get patient
```
GET /patients/<patient_id>
```

#### Update patient
```
PUT /patients/<patient_id>
Body: { fields to update }
```

#### Delete patient
```
DELETE /patients/<patient_id>
```

#### Visit history
```
GET /patients/<patient_id>/visits
```

#### Patient alerts
```
GET /patients/<patient_id>/alerts?unread=true
```

#### All alerts (doctor dashboard)
```
GET /patients/alerts/all?unread=true
```

#### Acknowledge alert
```
POST /patients/alerts/<alert_id>/acknowledge
```

---

### 🤖 ML Prediction

#### Quick prediction (no storage)
```
POST /predict/
Body:
{
  "age": 45, "gender": 1, "bmi": 28.5,
  "systolic_bp": 145, "diastolic_bp": 92,
  "heart_rate": 78, "cholesterol": 220, "glucose": 100,
  "smoking": 0, "alcohol": 1, "physical_activity": 3,
  "stress_level": 7
}
Response:
{
  "prediction": {
    "stage": 2,
    "stage_label": "Stage 2",
    "risk_score": 68.4,
    "probabilities": { "Normal": 5.0, "Stage 1": 15.0, "Stage 2": 58.0, "Crisis": 10.4 },
    "color": "orange"
  }
}
```

#### Predict + store visit + drift detection
```
POST /predict/visit
Body: { "patient_id": "abc123", ...same clinical fields... }
Response:
{
  "visit_id": "...",
  "prediction": { ...stage, risk_score... },
  "drift": {
    "alert_level": "HIGH",
    "drift_value": 48.0,
    "slope": 24.0,
    "trend": "INCREASING",
    "message": "⚠️ HIGH ALERT: ..."
  },
  "alert_id": "..."  // null if STABLE
}
```

#### Risk history + drift timeline
```
GET /predict/risk/<patient_id>
Response:
{
  "total_visits": 3,
  "drift_analysis": { "alert_level", "drift_value", "slope", "trend", "message" },
  "timeline": [
    { "visit_number": 1, "stage": "Stage 1", "risk_score": 30, "alert": "Stable" },
    { "visit_number": 2, "stage": "Stage 1", "risk_score": 55, "alert": "Drifting" },
    { "visit_number": 3, "stage": "Stage 2", "risk_score": 78, "alert": "⚠ HIGH ALERT" }
  ]
}
```

---

### 💬 Chatbot

#### Explain a report
```
POST /chatbot/explain
Body: { "stage": "Stage 2", "risk_score": 72.5, "alert_level": "HIGH", "patient_name": "John" }
```

#### Ask a health question
```
POST /chatbot/ask
Body: { "question": "What foods lower blood pressure?" }
```

#### Personalized advice
```
POST /chatbot/advice/<patient_id>
```

---

## Risk Drift Detection Logic

| Condition | Alert Level |
|-----------|-------------|
| Risk increase ≥ 25% AND positive slope | 🔴 HIGH |
| Risk increase ≥ 15% AND positive slope | 🟡 MODERATE |
| Otherwise | 🟢 STABLE |

Drift is computed over the last **3 visits** using linear regression on risk scores.

---

## Hypertension Stages

| Stage | Systolic | Diastolic | Risk Score |
|-------|----------|-----------|------------|
| Normal | < 120 | < 80 | 0–25% |
| Stage 1 | 130–139 | 80–89 | 25–50% |
| Stage 2 | ≥ 140 | ≥ 90 | 50–75% |
| Crisis | > 180 | > 120 | > 75% |

---

## Notes for Hackathon Demo

- The chatbot falls back to rule-based responses if `OPENAI_API_KEY` is not set
- MongoDB is optional during dev — set `MONGO_URI` to a local or Atlas instance
- Run `python models/train_model.py` first, always, before starting the server
- Model achieves ~95% accuracy using Logistic Regression (overfitted models rejected)
