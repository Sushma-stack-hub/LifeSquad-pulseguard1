"""
PulseGuard AI - PDF Report Generator
Generates a professional medical-style Blood Pressure Health Report using ReportLab.

Usage:
    from utils.pdf_report import generate_bp_report_pdf
    pdf_bytes = generate_bp_report_pdf(patient_data, clinical_inputs, prediction_results, recommendations)
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart

# ─── Color Palette (Medical Theme) ────────────────────────────────────────────
BRAND_BLUE      = colors.HexColor("#1A73E8")
BRAND_DARK      = colors.HexColor("#0D2B6B")
LIGHT_BLUE_BG   = colors.HexColor("#EEF4FF")
SECTION_HEADER  = colors.HexColor("#1A73E8")

RISK_COLORS = {
    "Normal":  colors.HexColor("#27AE60"),   # green
    "Stage 1": colors.HexColor("#F39C12"),   # yellow-orange
    "Stage 2": colors.HexColor("#E67E22"),   # orange
    "Crisis":  colors.HexColor("#E74C3C"),   # red
}

# ─── Custom Styles ────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()

    styles = {
        "report_title": ParagraphStyle(
            "report_title",
            parent=base["Title"],
            fontSize=22,
            textColor=BRAND_DARK,
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=2,
            alignment=TA_CENTER,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            parent=base["Heading2"],
            fontSize=12,
            textColor=colors.white,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=6,
            leftIndent=8,
        ),
        "field_label": ParagraphStyle(
            "field_label",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.grey,
            fontName="Helvetica-Bold",
        ),
        "field_value": ParagraphStyle(
            "field_value",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#222222"),
        ),
        "risk_label": ParagraphStyle(
            "risk_label",
            parent=base["Normal"],
            fontSize=28,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "risk_score": ParagraphStyle(
            "risk_score",
            parent=base["Normal"],
            fontSize=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
        ),
        "recommendation_text": ParagraphStyle(
            "recommendation_text",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#333333"),
            leading=16,
            leftIndent=10,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.grey,
            leading=12,
            alignment=TA_CENTER,
        ),
        "normal": base["Normal"],
    }
    return styles


# ─── Helper: Section Header Bar ───────────────────────────────────────────────

def _section_header(title: str, styles: dict):
    """Returns a blue header bar paragraph."""
    # We simulate a colored header using a single-cell table
    header_table = Table(
        [[Paragraph(f"  {title}", styles["section_header"])]],
        colWidths=[6.5 * inch],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SECTION_HEADER),
        ("ROWBACKGROUND", (0, 0), (-1, -1), SECTION_HEADER),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return header_table


# ─── Helper: Two-Column Info Table ────────────────────────────────────────────

def _info_table(rows: list, styles: dict):
    """
    Renders a clean 2-col label/value table.
    rows = [("Label", "Value"), ...]
    """
    table_data = [
        [
            Paragraph(label, styles["field_label"]),
            Paragraph(str(value), styles["field_value"]),
        ]
        for label, value in rows
    ]
    t = Table(table_data, colWidths=[2.0 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE_BG),
        ("ROWBACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D6E8FF")),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ─── Helper: Risk Score Visual Box ────────────────────────────────────────────

def _risk_box(stage_label: str, risk_score: float, styles: dict):
    """Draws a colored box showing the hypertension stage and risk score."""
    risk_color = RISK_COLORS.get(stage_label, colors.grey)

    stage_para = Paragraph(stage_label, styles["risk_label"])
    stage_para.style.textColor = risk_color

    score_para = Paragraph(
        f"Risk Score: <b>{risk_score:.1f}%</b>",
        styles["risk_score"]
    )

    box = Table(
        [[stage_para], [score_para]],
        colWidths=[6.5 * inch],
    )
    box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F9F9F9")),
        ("BOX",           (0, 0), (-1, -1), 2, risk_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    return box


# ─── Helper: Probability Bar Chart ────────────────────────────────────────────

def _probability_chart(probabilities: dict):
    """
    Draws a simple horizontal bar chart of class probabilities.
    probabilities = {"Normal": 5.0, "Stage 1": 15.0, "Stage 2": 58.0, "Crisis": 22.0}
    """
    labels = list(probabilities.keys())
    values = [probabilities[l] for l in labels]
    bar_colors = [RISK_COLORS.get(l, colors.grey) for l in labels]

    drawing = Drawing(400, 130)

    # Draw bars manually (simple, no chart library quirks)
    bar_width = 60
    spacing   = 30
    max_val   = 100
    chart_h   = 90
    x_start   = 40

    for i, (label, val, col) in enumerate(zip(labels, values, bar_colors)):
        x       = x_start + i * (bar_width + spacing)
        bar_h   = int((val / max_val) * chart_h)
        y_base  = 20

        # Bar
        drawing.add(Rect(x, y_base, bar_width, bar_h, fillColor=col, strokeColor=col))

        # Value label above bar
        drawing.add(String(
            x + bar_width / 2, y_base + bar_h + 4,
            f"{val:.1f}%",
            fontSize=8, textAnchor="middle", fillColor=colors.HexColor("#333333")
        ))

        # Category label below bar
        drawing.add(String(
            x + bar_width / 2, y_base - 12,
            label,
            fontSize=8, textAnchor="middle", fillColor=colors.HexColor("#555555")
        ))

    return drawing


# ─── Main PDF Generator Function ──────────────────────────────────────────────

def generate_bp_report_pdf(
    patient_data: dict,
    clinical_inputs: dict,
    prediction_results: dict,
    recommendations: str,
) -> bytes:
    """
    Generate a professional medical-style Blood Pressure Health Report PDF.

    Args:
        patient_data:       Patient profile info (name, dob, gender, contact, etc.)
        clinical_inputs:    Clinical measurements used for prediction
        prediction_results: Output from predict_hypertension() — stage, risk_score, probabilities
        recommendations:    Personalized advice string (from chatbot or rule-based)

    Returns:
        PDF as bytes (ready to send as Flask response)

    Example:
        pdf_bytes = generate_bp_report_pdf(
            patient_data       = {"name": "John Doe", "date_of_birth": "1978-05-12", ...},
            clinical_inputs    = {"age": 45, "systolic_bp": 145, ...},
            prediction_results = {"stage_label": "Stage 2", "risk_score": 68.4, ...},
            recommendations    = "Reduce salt intake, exercise 30 min/day..."
        )
        # Then send as Flask response
    """

    # Build PDF into memory buffer (no file written to disk)
    buffer = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Blood Pressure Health Report",
        author="PulseGuard AI",
    )

    story = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    story.append(Paragraph("🫀 Blood Pressure Health Report", styles["report_title"]))
    story.append(Paragraph("Generated by PulseGuard AI — Intelligent Hypertension Monitoring", styles["subtitle"]))
    story.append(Paragraph(
        f"Report Date: {datetime.now().strftime('%B %d, %Y  |  %I:%M %p')}",
        styles["subtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=12))

    # ── SECTION 1: PATIENT INFORMATION ────────────────────────────────────────
    story.append(_section_header("1. Patient Information", styles))
    story.append(Spacer(1, 6))

    patient_rows = [
        ("Full Name",      patient_data.get("name", "N/A")),
        ("Date of Birth",  patient_data.get("date_of_birth", "N/A")),
        ("Gender",         patient_data.get("gender", "N/A")),
        ("Contact",        patient_data.get("contact", "N/A")),
        ("Address",        patient_data.get("address", "N/A")),
        ("Patient ID",     patient_data.get("patient_id", "N/A")),
    ]
    story.append(_info_table(patient_rows, styles))
    story.append(Spacer(1, 14))

    # ── SECTION 2: CLINICAL INPUTS ────────────────────────────────────────────
    story.append(_section_header("2. Clinical Inputs", styles))
    story.append(Spacer(1, 6))

    clinical_rows = [
        ("Age",                   f"{clinical_inputs.get('age', 'N/A')} years"),
        ("BMI",                   f"{clinical_inputs.get('bmi', 'N/A')}"),
        ("Systolic BP",           f"{clinical_inputs.get('systolic_bp', 'N/A')} mmHg"),
        ("Diastolic BP",          f"{clinical_inputs.get('diastolic_bp', 'N/A')} mmHg"),
        ("Heart Rate",            f"{clinical_inputs.get('heart_rate', 'N/A')} bpm"),
        ("Cholesterol",           f"{clinical_inputs.get('cholesterol', 'N/A')} mg/dL"),
        ("Glucose",               f"{clinical_inputs.get('glucose', 'N/A')} mg/dL"),
        ("Smoking",               "Yes" if clinical_inputs.get("smoking") else "No"),
        ("Alcohol Consumption",   "Yes" if clinical_inputs.get("alcohol") else "No"),
        ("Physical Activity",     f"{clinical_inputs.get('physical_activity', 'N/A')} hrs/week"),
        ("Stress Level",          f"{clinical_inputs.get('stress_level', 'N/A')} / 10"),
    ]
    story.append(_info_table(clinical_rows, styles))
    story.append(Spacer(1, 14))

    # ── SECTION 3: PREDICTION RESULTS ─────────────────────────────────────────
    story.append(_section_header("3. Prediction Results", styles))
    story.append(Spacer(1, 8))

    stage_label = prediction_results.get("stage_label", "Unknown")
    risk_score  = prediction_results.get("risk_score",  0.0)
    alert_level = prediction_results.get("alert_level", "STABLE")

    # Risk box (big colored stage display)
    story.append(KeepTogether([
        _risk_box(stage_label, risk_score, styles),
        Spacer(1, 10),
    ]))

    # Alert level row
    alert_color_map = {"STABLE": "#27AE60", "MODERATE": "#F39C12", "HIGH": "#E74C3C"}
    alert_color     = alert_color_map.get(alert_level, "#888888")
    alert_table     = Table(
        [[Paragraph(
            f'<font color="{alert_color}"><b>Drift Alert Level: {alert_level}</b></font>',
            styles["normal"]
        )]],
        colWidths=[6.5 * inch],
    )
    alert_table.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(alert_table)
    story.append(Spacer(1, 10))

    # Probability breakdown table
    probabilities = prediction_results.get("probabilities", {})
    if probabilities:
        story.append(Paragraph("  Stage Probability Breakdown:", styles["field_label"]))
        story.append(Spacer(1, 6))

        prob_data = [["Stage", "Probability"]] + [
            [stage, f"{prob:.1f}%"] for stage, prob in probabilities.items()
        ]
        prob_table = Table(prob_data, colWidths=[3.25 * inch, 3.25 * inch])
        prob_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  BRAND_BLUE),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("BACKGROUND",    (0, 1), (-1, -1), LIGHT_BLUE_BG),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(prob_table)
        story.append(Spacer(1, 8))

        # Visual bar chart
        story.append(Paragraph("  Visual Risk Distribution:", styles["field_label"]))
        story.append(Spacer(1, 4))
        story.append(_probability_chart(probabilities))

    story.append(Spacer(1, 14))

    # ── SECTION 4: PERSONALIZED RECOMMENDATIONS ───────────────────────────────
    story.append(_section_header("4. Personalized Recommendations", styles))
    story.append(Spacer(1, 8))

    # Split recommendations by newline and render each line
    rec_lines = recommendations.strip().split("\n")
    for line in rec_lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        # Render bullet points nicely
        if line.startswith("•") or line.startswith("-"):
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{line}", styles["recommendation_text"]))
        else:
            story.append(Paragraph(line, styles["recommendation_text"]))
    story.append(Spacer(1, 20))

    # ── FOOTER: MEDICAL DISCLAIMER ────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceAfter=8))
    story.append(Paragraph(
        "<b>Medical Disclaimer</b>",
        ParagraphStyle("disc_header", parent=styles["disclaimer"], fontSize=9,
                       textColor=colors.HexColor("#555555"), fontName="Helvetica-Bold")
    ))
    story.append(Paragraph(
        "This report is generated by PulseGuard AI for informational and educational purposes only. "
        "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
        "Always consult a qualified healthcare provider before making any medical decisions. "
        "In case of a hypertensive crisis or emergency, call emergency services immediately.",
        styles["disclaimer"]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "PulseGuard AI — GenAI Forge 2026 Hackathon Project | For Demo Purposes Only",
        styles["disclaimer"]
    ))

    # ── BUILD PDF ─────────────────────────────────────────────────────────────
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes