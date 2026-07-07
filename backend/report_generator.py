from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from backend.evidence_manager import EVIDENCE_DIR


def _final_status_from_score(score: int) -> str:
    if score >= 100:
        return "Critical"
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    if score > 0:
        return "Low"
    return "No Alerts"


def generate_pdf_report(alerts: List[Dict], risk_score: int) -> str:
    """Generate a PDF report and return the file path."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = EVIDENCE_DIR / f"invigilation_report_{timestamp}.pdf"

    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    y = height - 50
    pdf.setTitle("Invigilation Duty Anomaly Detection Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "Invigilation Duty Anomaly Detection Report")

    y -= 35
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 20
    pdf.drawString(50, y, f"Total alerts: {len(alerts)}")
    y -= 20
    pdf.drawString(50, y, f"Risk score: {risk_score}")
    y -= 20
    pdf.drawString(50, y, f"Final status: {_final_status_from_score(risk_score)}")

    y -= 35
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Alert List")
    y -= 22
    pdf.setFont("Helvetica", 10)

    if not alerts:
        pdf.drawString(50, y, "No alerts detected.")
    else:
        for alert in alerts:
            line = (
                f"[{alert['timestamp']}] {alert['alert_type']} | "
                f"{alert['risk_level']} | Score: {alert['risk_score']} | {alert['message']}"
            )
            if y < 70:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y, line[:120])
            y -= 18

    pdf.save()
    return str(output_path)
