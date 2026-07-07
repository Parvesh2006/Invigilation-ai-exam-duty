from __future__ import annotations

from typing import List, Tuple

from anomaly_engine import Alert


def score_from_alerts(alerts: List[Alert]) -> Tuple[int, str]:
    """Return the final risk score and overall status."""
    if not alerts:
        return 0, "Safe"

    score = min(max(alert.risk_score for alert in alerts), 100)

    if score <= 30:
        status = "Safe"
    elif score <= 60:
        status = "Moderate Risk"
    elif score <= 80:
        status = "High Risk"
    else:
        status = "Critical Risk"

    return score, status
