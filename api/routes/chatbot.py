"""
PulseGuard AI - AI Chatbot Routes
POST /api/chatbot/explain   → Explain a risk report in simple language
POST /api/chatbot/ask       → General health Q&A
POST /api/chatbot/advice/<patient_id> → Personalized advice based on history
"""

from flask import Blueprint, request, jsonify
import os

chatbot_bp = Blueprint("chatbot", __name__)

# ─── Try to load OpenAI / LangChain ───────────────────────────────────────────
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

SYSTEM_PROMPT = """
You are PulseGuard AI's health assistant — a friendly, empathetic, and knowledgeable
medical companion specializing in hypertension and cardiovascular health.

Your role:
- Explain complex medical risk reports in simple, patient-friendly language
- Provide evidence-based lifestyle recommendations
- Encourage patients to follow up with their doctor for clinical decisions
- Always be supportive, never alarming unless the patient is in a real emergency

IMPORTANT: Keep your responses concise but informative.
- Target length: Approximately 4 lines (60-80 words).
- Use clear, complete sentences.
- Do not offer unsolicited medical advice.
"""


def get_llm():
    if not LANGCHAIN_AVAILABLE:
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    
    return ChatGroq(
        temperature=0.5,
        model_name="llama-3.3-70b-versatile",
        groq_api_key=api_key
    )


def fallback_response(topic: str, stage: str = None, risk_score: float = None) -> str:
    """Rule-based fallback when OpenAI is not configured."""
    if stage == "Crisis" or (risk_score and risk_score > 80):
        return (
            "🚨 Your blood pressure is in a critical range. Please seek immediate "
            "medical attention. Avoid strenuous activity and contact your doctor or "
            "go to the nearest emergency room right away."
        )
    elif stage in ("Stage 2",) or (risk_score and risk_score > 60):
        return (
            "⚠️ Your blood pressure is elevated (Stage 2 Hypertension). "
            "Please schedule an appointment with your doctor soon. In the meantime:\n"
            "• Reduce salt intake to less than 5g/day\n"
            "• Avoid alcohol and smoking\n"
            "• Take a 30-minute walk daily\n"
            "• Monitor your BP every day\n"
            "• Manage stress with deep breathing or meditation"
        )
    elif stage == "Stage 1" or (risk_score and risk_score > 30):
        return (
            "Your blood pressure is slightly elevated (Stage 1 Hypertension). "
            "The good news is that lifestyle changes can make a big difference:\n"
            "• Eat more fruits, vegetables, and whole grains (DASH diet)\n"
            "• Reduce sodium and processed food\n"
            "• Exercise at least 150 minutes/week\n"
            "• Maintain a healthy weight\n"
            "• Limit alcohol and quit smoking\n\n"
            "Regular monitoring is important. Follow up with your doctor."
        )
    else:
        return (
            "Great news! Your blood pressure is in the normal range. "
            "Keep up the healthy habits:\n"
            "• Stay physically active\n"
            "• Maintain a balanced diet\n"
            "• Get 7-8 hours of sleep\n"
            "• Manage stress effectively\n\n"
            "Continue monitoring your blood pressure regularly."
        )


# ─── POST /api/chatbot/explain ────────────────────────────────────────────────
@chatbot_bp.route("/explain", methods=["POST"])
def explain_report():
    """
    Explain a risk report in patient-friendly language.

    Body:
    {
      "stage": "Stage 2",
      "risk_score": 72.5,
      "alert_level": "HIGH",
      "patient_name": "John"
    }
    """
    data        = request.get_json(force=True)
    stage       = data.get("stage", "Unknown")
    risk_score  = data.get("risk_score", 0)
    alert_level = data.get("alert_level", "STABLE")
    name        = data.get("patient_name", "Patient")

    llm = get_llm()
    if llm:
        prompt = (
            f"Patient name: {name}\n"
            f"Hypertension Stage: {stage}\n"
            f"Risk Score: {risk_score:.1f}%\n"
            f"Alert Level: {alert_level}\n\n"
            f"Please explain this result in simple, kind language and provide "
            f"3-5 actionable lifestyle recommendations. Keep it under 200 words."
        )
        try:
            response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
            reply    = response.content
        except Exception as e:
            reply = fallback_response(stage, stage, risk_score)
    else:
        reply = fallback_response(stage, stage, risk_score)

    return jsonify({"success": True, "response": reply}), 200


# ─── POST /api/chatbot/ask ────────────────────────────────────────────────────
@chatbot_bp.route("/ask", methods=["POST"])
def ask():
    """
    General health Q&A.

    Body: { "question": "What foods lower blood pressure?" }
    """
    data     = request.get_json(force=True)
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    llm = get_llm()
    if llm:
        try:
            response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)])
            reply    = response.content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            reply = "I'm sorry, I'm having trouble connecting right now. Please consult your doctor for medical questions."
    else:
        # Simple keyword-based fallback
        q = question.lower()
        if "food" in q or "diet" in q or "eat" in q:
            reply = (
                "Foods that help lower blood pressure include:\n"
                "• Leafy greens (spinach, kale)\n"
                "• Berries (blueberries, strawberries)\n"
                "• Bananas (high in potassium)\n"
                "• Beets\n"
                "• Oatmeal\n"
                "• Garlic\n"
                "• Fish rich in omega-3 (salmon, mackerel)\n\n"
                "Reduce: salt, processed foods, red meat, alcohol."
            )
        elif "exercise" in q or "workout" in q or "activity" in q:
            reply = (
                "Exercise recommendations for hypertension:\n"
                "• 150 minutes of moderate aerobic activity per week\n"
                "• Brisk walking, swimming, cycling, or yoga are excellent choices\n"
                "• Avoid heavy weightlifting without doctor approval\n"
                "• Aim for 30 minutes, 5 days a week"
            )
        elif "stress" in q:
            reply = (
                "Stress management techniques:\n"
                "• Deep breathing exercises (4-7-8 method)\n"
                "• Meditation or mindfulness — even 10 min/day helps\n"
                "• Regular sleep schedule (7-8 hours)\n"
                "• Yoga or tai chi\n"
                "• Limit news and social media intake"
            )
        else:
            reply = (
                "I'm PulseGuard AI. I can help you understand your blood pressure "
                "results and offer lifestyle guidance. For specific medical advice, "
                "please consult your doctor. You can ask me about:\n"
                "• Your risk report\n"
                "• Diet and nutrition for BP management\n"
                "• Exercise recommendations\n"
                "• Stress management tips"
            )

    return jsonify({"success": True, "response": reply}), 200


# ─── POST /api/chatbot/advice/<patient_id> ────────────────────────────────────
@chatbot_bp.route("/advice/<patient_id>", methods=["POST"])
def personalized_advice(patient_id: str):
    """
    Generate personalized advice based on patient's visit history.
    """
    from utils.db import get_patient, get_visits

    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    visits = get_visits(patient_id)
    if not visits:
        return jsonify({"message": "No visits recorded yet. No advice to generate."}), 200

    latest  = visits[-1]
    stage   = latest.get("stage_label", "Unknown")
    risk    = latest.get("risk_score", 0)
    smoking = latest.get("smoking", 0)
    alcohol = latest.get("alcohol", 0)
    bmi     = latest.get("bmi", 0)
    stress  = latest.get("stress_level", 5)

    llm = get_llm()
    if llm:
        prompt = (
            f"Patient: {patient.get('name', 'Patient')}\n"
            f"Latest Stage: {stage}, Risk Score: {risk:.1f}%\n"
            f"BMI: {bmi:.1f}, Smoking: {'Yes' if smoking else 'No'}, "
            f"Alcohol: {'Yes' if alcohol else 'No'}, Stress Level: {stress}/10\n"
            f"Number of visits: {len(visits)}\n\n"
            "Give personalized, specific, and actionable health recommendations "
            "based on this patient's profile. Be encouraging. Keep it under 250 words."
        )
        try:
            response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
            advice   = response.content
        except Exception as e:
            advice = fallback_response(stage, stage, risk)
    else:
        advice = fallback_response(stage, stage, risk)

    return jsonify({"success": True, "patient_id": patient_id, "advice": advice}), 200
