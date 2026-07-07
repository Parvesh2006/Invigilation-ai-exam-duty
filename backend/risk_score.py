from __future__ import annotations

from typing import List, Tuple

from backend.anomaly_engine import Alert, SEVERITY_TO_SCORE


def score_from_alerts(alerts: List[Alert]) -> Tuple[int, str]:
    """Return the final score and a human-readable overall level."""
    if not alerts:
        return 0, "No Alerts"

    score = min(max(alert.risk_score for alert in alerts), 100)

    if score >= SEVERITY_TO_SCORE["Critical"]:
        level = "Critical"
    elif score >= SEVERITY_TO_SCORE["High"]:
        level = "High"
    elif score >= SEVERITY_TO_SCORE["Medium"]:
        level = "Medium"
    else:
        level = "Low"

    return score, level

