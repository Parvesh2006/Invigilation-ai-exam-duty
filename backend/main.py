from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.anomaly_engine import Alert, AnomalyEngine
from backend.database import clear_alerts, fetch_alerts, init_db, insert_alert
from backend.risk_score import score_from_alerts
from ai.intelligence import ExaminationIntelligenceEngine, risk_category


app = FastAPI(title="Invigilation Duty Anomaly Detection")


class DetectionInput(BaseModel):
    phone_detected: bool = False
    invigilator_absent: bool = False
    student_standing: bool = False
    student_head_turning: bool = False
    camera_blocked: bool = False
    unauthorized_person: bool = False


class BoundingBoxPayload(BaseModel):
    x: int = 0
    y: int = 0
    width: int = 1
    height: int = 1


class AIAlertPayload(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    camera_id: str
    tracking_id: str = ""
    confidence: float = 0.0
    risk_score: int = 0
    zone: str = "unknown"
    bounding_box: BoundingBoxPayload = Field(default_factory=BoundingBoxPayload)
    screenshot: str = ""
    description: str = ""


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


engine = AnomalyEngine()
platform_engine = ExaminationIntelligenceEngine()


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
    return {
        "status": "Backend Running",
        "project": "Sentinel AI",
        "positioning": "Examination Intelligence Platform",
    }


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


@app.post("/alert")
def ingest_ai_alert(payload: AIAlertPayload) -> Dict[str, Any]:
    """Receive JSON alerts from the AI engine and update platform intelligence."""

    alert = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    insert_alert(
        alert_type=payload.event_type,
        risk_level=risk_category(payload.risk_score),
        message=payload.description,
        risk_score=payload.risk_score,
        timestamp=payload.timestamp or datetime.now().isoformat(timespec="seconds"),
    )
    snapshot = platform_engine.ingest_alert(alert)
    return {
        "message": "AI alert ingested",
        "event_id": payload.event_id,
        "integrity_score": snapshot["integrity_score"],
        "risk_category": snapshot["risk_category"],
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


@app.get("/platform")
def get_platform_snapshot() -> Dict[str, Any]:
    """Mission Control snapshot for the frontend."""

    return platform_engine.snapshot()


@app.get("/digital-twin")
def get_digital_twin() -> Dict[str, Any]:
    return platform_engine.digital_twin()


@app.get("/ai-health")
def get_ai_health() -> Dict[str, Any]:
    return platform_engine.snapshot()["health"]


@app.get("/session-summary")
def get_session_summary() -> Dict[str, Any]:
    return platform_engine.session_summary()


@app.get("/report")
def get_report() -> FileResponse:
    try:
        from backend.report_generator import generate_pdf_report
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="PDF report dependency missing. Install reportlab to enable reports.",
        ) from exc

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
