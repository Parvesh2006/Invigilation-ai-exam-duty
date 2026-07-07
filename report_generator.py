from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from evidence_manager import EVIDENCE_DIR


REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_pdf_report(alerts: List[Dict], risk_score: int, status: str) -> Path:
    """Generate a PDF report and return the file path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = REPORTS_DIR / f"invigilation_report_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Invigilation Duty Anomaly Detection", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Paragraph(f"Total alerts: {len(alerts)}", styles["Normal"]))
    story.append(Paragraph(f"Final risk score: {risk_score}", styles["Normal"]))
    story.append(Paragraph(f"Final status: {status}", styles["Normal"]))
    story.append(Spacer(1, 12))

    table_data = [["Alert Type", "Risk Level", "Message", "Timestamp"]]
    for alert in alerts:
        table_data.append(
            [
                alert["alert_type"],
                alert["risk_level"],
                alert["message"],
                alert["timestamp"],
            ]
        )

    if len(table_data) == 1:
        table_data.append(["No alerts detected", "-", "-", "-"])

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3c88")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 11),
            ]
        )
    )

    story.append(table)
    doc.build(story)
    return output_path

