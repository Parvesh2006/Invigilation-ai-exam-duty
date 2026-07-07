from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


SEVERITY_TO_SCORE = {
    "Low": 25,
    "Medium": 50,
    "High": 75,
    "Critical": 100,
}


@dataclass(frozen=True)
class Alert:
    alert_type: str
    risk_level: str
    message: str
    risk_score: int


class AnomalyEngine:
    """Convert raw AI detections into structured alerts."""

    RULES = {
        "phone_detected": ("High", "Phone detected during the exam."),
        "invigilator_absent": ("High", "Invigilator is absent from the exam hall."),
        "student_standing": ("Medium", "A student is standing unexpectedly."),
        "student_head_turning": ("Medium", "A student is repeatedly turning their head."),
        "camera_blocked": ("Critical", "The camera view is blocked."),
        "unauthorized_person": ("High", "An unauthorized person was detected in the exam hall."),
    }

    def analyze(self, detections: Dict[str, bool]) -> List[Alert]:
        alerts: List[Alert] = []

        for field_name, (risk_level, message) in self.RULES.items():
            if detections.get(field_name):
                alerts.append(
                    Alert(
                        alert_type=field_name,
                        risk_level=risk_level,
                        message=message,
                        risk_score=SEVERITY_TO_SCORE[risk_level],
                    )
                )

        return alerts

    @staticmethod
    def final_risk_score(alerts: List[Alert]) -> int:
        if not alerts:
            return 0
        return min(max(alert.risk_score for alert in alerts), 100)

