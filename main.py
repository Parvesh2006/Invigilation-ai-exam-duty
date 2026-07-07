from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from anomaly_engine import Alert, AnomalyEngine
from database import clear_alerts, fetch_alerts, init_db, insert_alert
from report_generator import generate_pdf_report
from risk_score import score_from_alerts


class DetectionInput(BaseModel):
    phone_detected: bool = False
    invigilator_absent: bool = False
    student_standing: bool = False
    student_head_turning: bool = False
    camera_blocked: bool = False
    unauthorized_person: bool = False
    multiple_students_talking: bool = False
    paper_exchange: bool = False
    student_sleeping: bool = False
    crowd_movement: bool = False


app = FastAPI(title="Invigilation Duty Anomaly Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = AnomalyEngine()


def _rows_to_alert_objects(rows: List[Dict[str, Any]]) -> List[Alert]:
    return [
        Alert(
            alert_type=row["alert_type"],
            risk_level=row["risk_level"],
            message=row["message"],
            risk_score=int(row["risk_score"]),
            timestamp=row["timestamp"],
        )
        for row in rows
    ]


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "status": "Backend Running",
        "project": "Invigilation Duty Anomaly Detection",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy", "project": "Invigilation Duty Anomaly Detection"}


@app.post("/detect")
def detect(payload: DetectionInput) -> Dict[str, Any]:
    detections = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    alerts = engine.analyze(detections)
    timestamp = datetime.now().isoformat(timespec="seconds")

    stored_alerts = []
    for alert in alerts:
        alert_id = insert_alert(
            alert_type=alert.alert_type,
            risk_level=alert.risk_level,
            message=alert.message,
            risk_score=alert.risk_score,
            timestamp=timestamp,
        )
        stored_alerts.append(
            {
                "id": alert_id,
                "alert_type": alert.alert_type,
                "risk_level": alert.risk_level,
                "message": alert.message,
                "risk_score": alert.risk_score,
                "timestamp": timestamp,
            }
        )

    final_score, final_status = score_from_alerts(alerts)

    return {
        "message": "Detection processed successfully",
        "total_alerts": len(alerts),
        "risk_score": final_score,
        "status": final_status,
        "alerts": stored_alerts,
    }


@app.get("/alerts")
def get_alerts() -> Dict[str, Any]:
    alerts = fetch_alerts()
    return {"total_alerts": len(alerts), "alerts": alerts}


@app.get("/risk-score")
def get_risk_score() -> Dict[str, Any]:
    alerts = fetch_alerts()
    risk_score, status = score_from_alerts(_rows_to_alert_objects(alerts))
    return {
        "risk_score": risk_score,
        "status": status,
        "total_alerts": len(alerts),
    }


@app.get("/report")
def get_report() -> FileResponse:
    alerts = fetch_alerts()
    risk_score, status = score_from_alerts(_rows_to_alert_objects(alerts))
    report_path = generate_pdf_report(alerts, risk_score, status)

    if not report_path.exists():
        raise HTTPException(status_code=500, detail="Report could not be generated")

    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=report_path.name,
    )


@app.delete("/alerts")
def delete_alerts() -> Dict[str, Any]:
    deleted_rows = clear_alerts()
    return {
        "message": "All alerts deleted successfully",
        "deleted_rows": deleted_rows,
    }

