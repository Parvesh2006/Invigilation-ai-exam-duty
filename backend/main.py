from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from anomaly_engine import Alert, AnomalyEngine
from database import clear_alerts, fetch_alerts, init_db, insert_alert
from risk_score import score_from_alerts
from report_generator import generate_pdf_report


app = FastAPI(title="Invigilation Duty Anomaly Detection")


class DetectionInput(BaseModel):
    phone_detected: bool = False
    invigilator_absent: bool = False
    student_standing: bool = False
    student_head_turning: bool = False
    camera_blocked: bool = False
    unauthorized_person: bool = False


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
        )
        for row in rows
    ]


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/")
def home() -> Dict[str, str]:
    return {"status": "Backend Running"}


@app.post("/detect")
def detect_anomaly(payload: DetectionInput) -> Dict[str, Any]:
    detections = payload.dict()
    alerts = engine.analyze(detections)
    timestamp = datetime.now().isoformat(timespec="seconds")

    for alert in alerts:
        insert_alert(
            alert.alert_type,
            alert.risk_level,
            alert.message,
            alert.risk_score,
            timestamp,
        )

    risk_score, level = score_from_alerts(alerts)

    return {
        "message": "Detection processed successfully",
        "total_alerts": len(alerts),
        "risk_score": risk_score,
        "status": level,
        "alerts": [
            {
                "alert_type": alert.alert_type,
                "risk_level": alert.risk_level,
                "message": alert.message,
                "risk_score": alert.risk_score,
                "timestamp": timestamp,
            }
            for alert in alerts
        ],
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
    risk_score, _ = score_from_alerts(_rows_to_alert_objects(alerts))
    report_path = Path(generate_pdf_report(alerts, risk_score))

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