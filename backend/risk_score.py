from __future__ import annotations

from typing import List, Tuple

from anomaly_engine import Alert, SEVERITY_TO_SCORE


def score_from_alerts(alerts: List[Alert]) -> Tuple[int, str]:
    """Return the final score and a human-readable overall level."""
    if not alerts:
        return 0, "Safe"

    score = min(max(alert.risk_score for alert in alerts), 100)

    if score <= 30:
        level = "Safe"
    elif score <= 60:
        level = "Moderate Risk"
    elif score <= 80:
        level = "High Risk"
    else:
        level = "Critical Risk"

    return score, level
