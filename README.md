# PulseGuard AI

**Intelligent Blood Pressure Prediction & Monitoring System**

PulseGuard AI is a comprehensive health monitoring application designed to predict hypertension risks, track patient vitals, and provide AI-driven health insights. It combines machine learning for risk prediction with a generative AI chatbot for personalized patient support.

![PulseGuard AI](https://via.placeholder.com/800x400?text=PulseGuard+AI+Dashboard)

---

## 🚀 Key Features

-   **ML Risk Prediction**: Predicts hypertension stages (Normal, Stage 1, Stage 2, Crisis) using a trained Logistic Regression model.
-   **Drift Detection**: Monitors patient risk scores over time to detect worsening trends (Risk Drift).
-   **AI Chatbot**: A Groq-powered health assistant (Llama-3.3-70b) that answers queries and explains medical reports.
-   **Doctor & Patient Portals**: distinct dashboards for patients to view history and doctors to manage alerts.
-   **PDF Reports**: Generate downloadable health reports.

---

## 📂 Project Structure

```
pulseguard/
├── frontend/             # HTML/CSS/JS User Interface
│   ├── index.html        # Main application entry point
│   ├── app.js            # Frontend logic
│   └── chatbot.js        # Chatbot widget logic
│
└── pulseguard_backend/   # Flask API & ML Engine
    ├── app.py            # API Entry point
    ├── models/           # ML Model training scripts & .pkl files
    ├── routes/           # API Endpoints (predict, chatbot, auth)
    └── utils/            # Helper functions
```

---

## 🛠️ Setup & Installation

### Prerequisites

-   Python 3.9+
-   MongoDB (Local or Atlas)
-   Groq API Key (for Chatbot)

### 1. Backend Setup

Navigate to the backend directory:

```bash
cd pulseguard_backend
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Train the ML Model** (Run this once first):

```bash
python models/train_model.py
```

**Configure Environment**:
Create a `.env` file in `pulseguard_backend/`:

```ini
MONGO_URI=mongodb://localhost:27017/pulseguard
OPENAI_API_KEY=your_groq_api_key_here  # Use Groq API Key here
SECRET_KEY=your_secret_key
```

**Start the Server**:

```bash
python app.py
```
*Backend runs on `http://127.0.0.1:5001`*

### 2. Frontend Setup

The frontend is built with vanilla HTML/JS and requires a simple HTTP server to avoid CORS issues.

Open a new terminal, navigate to `frontend/`:

```bash
cd frontend
python3 -m http.server 8080
```

*Access the app at `http://localhost:8080`*

---

## 🤖 Usage Guide

1.  **Login**:
    *   **Patient**: Use `jane` / `1234`
    *   **Doctor**: Use `sharma` / `doc123`
2.  **Predict**: Go to "Analyse My Risk" and enter clinical data.
3.  **Chat**: Click the bot icon to ask about your blood pressure or general health.
4.  **Dashboard**: Doctors can view "High Risk" patient alerts and drift analysis.

---

## 🔗 Stack

-   **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
-   **Backend**: Flask (Python)
-   **Database**: MongoDB
-   **AI/ML**: Scikit-Learn (Logistic Regression), LangChain, Groq (Llama-3)

---

## 📜 License

This project is open-source.
