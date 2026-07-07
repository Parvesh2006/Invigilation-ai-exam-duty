"""Examination intelligence layer built on top of AI alerts.

This module turns low-level anomaly events into product-level outputs:
digital twin, integrity score, supervisor recommendations, timeline, health,
and session summaries. It intentionally uses only realistic signals from YOLO,
tracking, zones, timing, and the rule engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from ai.config import BoundingBox, SETTINGS


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def risk_category(score: int) -> str:
    """Convert risk into judge-friendly severity language."""

    if score >= 85:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 45:
        return "Medium"
    if score >= 20:
        return "Low"
    return "Safe"


@dataclass(slots=True)
class AlertSignal:
    """Backend/AI alert shape consumed by the intelligence engine."""

    event_id: str
    event_type: str
    timestamp: str
    camera_id: str
    tracking_id: str
    confidence: float
    risk_score: int
    zone: str
    bounding_box: dict[str, int]
    screenshot: str
    description: str

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> AlertSignal:
        bbox = payload.get("bounding_box") or {}
        return cls(
            event_id=str(payload.get("event_id", "")),
            event_type=str(payload.get("event_type", "UNKNOWN")),
            timestamp=str(payload.get("timestamp") or _now_iso()),
            camera_id=str(payload.get("camera_id", "unknown")),
            tracking_id=str(payload.get("tracking_id", "")),
            confidence=float(payload.get("confidence", 0.0)),
            risk_score=int(payload.get("risk_score", 0)),
            zone=str(payload.get("zone", "unknown")),
            bounding_box={
                "x": int(bbox.get("x", 0)),
                "y": int(bbox.get("y", 0)),
                "width": int(bbox.get("width", 1)),
                "height": int(bbox.get("height", 1)),
            },
            screenshot=str(payload.get("screenshot", "")),
            description=str(payload.get("description", "")),
        )


@dataclass(slots=True)
class SupervisorRecommendation:
    """Explainable recommendation generated from a real rule event."""

    title: str
    recommendation: str
    reason: str
    confidence: float
    priority: str
    zone: str


@dataclass(slots=True)
class IntelligenceSnapshot:
    """Full Mission Control state exposed to backend/frontend."""

    integrity_score: int
    risk_category: str
    trend: str
    active_alerts: list[dict[str, Any]]
    highlighted_alert: dict[str, Any] | None
    timeline: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    digital_twin: dict[str, Any]
    health: dict[str, Any]
    evidence_center: list[dict[str, Any]]
    session: dict[str, Any]


class ExaminationIntelligenceEngine:
    """Maintains exam-level intelligence state for Mission Control views."""

    def __init__(self) -> None:
        self.started_at = datetime.now(UTC)
        self.integrity_score = 100.0
        self._last_integrity_score = 100.0
        self._alerts: list[AlertSignal] = []
        self._active_alerts: dict[str, AlertSignal] = {}
        self._timeline: list[dict[str, Any]] = []
        self._recommendations: list[SupervisorRecommendation] = []
        self._latest_tracks: list[dict[str, Any]] = []
        self._latest_zones: list[dict[str, Any]] = [
            zone.model_dump(mode="json") for zone in SETTINGS.zones
        ]
        self._health: dict[str, Any] = {
            "camera": "Unknown",
            "yolo": "Unknown",
            "tracking": "Unknown",
            "backend": "Unknown",
            "fps": 0.0,
            "last_update": _now_iso(),
        }

    def ingest_alert(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Add a new alert and update risk, timeline, and recommendations."""

        alert = AlertSignal.from_mapping(payload)
        self._alerts.append(alert)
        self._active_alerts[alert.event_id or f"{alert.event_type}:{len(self._alerts)}"] = alert
        self._update_integrity(alert)
        self._timeline.insert(0, self._timeline_entry(alert))
        self._recommendations.insert(0, self._recommendation_for(alert))
        self._timeline = self._timeline[:100]
        self._recommendations = self._recommendations[:20]
        return self.snapshot()

    def update_scene(
        self,
        *,
        tracks: list[Any],
        zones: list[Any],
        fps: float,
        camera_connected: bool,
        yolo_running: bool,
        backend_connected: bool,
    ) -> None:
        """Update live digital-twin and system-health state."""

        self._latest_tracks = [self._track_to_mapping(track) for track in tracks]
        self._latest_zones = [
            zone.model_dump(mode="json") if hasattr(zone, "model_dump") else dict(zone)
            for zone in zones
        ]
        self._health = {
            "camera": "Connected" if camera_connected else "Disconnected",
            "yolo": "Running" if yolo_running else "Stopped",
            "tracking": "Stable" if tracks is not None else "Unknown",
            "backend": "Connected" if backend_connected else "Offline",
            "fps": round(float(fps), 2),
            "last_update": _now_iso(),
        }
        self._recover_integrity()

    def resolve_alert(self, event_id: str) -> None:
        """Mark an alert resolved for timeline/session accounting."""

        alert = self._active_alerts.pop(event_id, None)
        if alert is None:
            return
        self._timeline.insert(
            0,
            {
                "timestamp": _now_iso(),
                "title": f"{alert.event_type} resolved",
                "status": "Resolved",
                "zone": alert.zone,
                "risk_score": alert.risk_score,
            },
        )

    def snapshot(self) -> dict[str, Any]:
        """Return the current Mission Control state."""

        active_alerts = [self._explain_alert(alert) for alert in self._active_alerts.values()]
        highlighted = max(active_alerts, key=lambda item: item["risk_score"], default=None)
        snapshot = IntelligenceSnapshot(
            integrity_score=round(self.integrity_score),
            risk_category=risk_category(100 - round(self.integrity_score)),
            trend=self._trend(),
            active_alerts=active_alerts,
            highlighted_alert=highlighted,
            timeline=self._timeline,
            recommendations=[asdict(item) for item in self._recommendations[:5]],
            digital_twin=self.digital_twin(),
            health=self._health,
            evidence_center=self.evidence_center(),
            session=self.session_summary(),
        )
        return asdict(snapshot)

    def digital_twin(self) -> dict[str, Any]:
        """Return a simplified live classroom map."""

        invigilators = [
            track for track in self._latest_tracks if track.get("zone") == "invigilator"
        ]
        students = [
            track for track in self._latest_tracks if track.get("zone") != "invigilator"
        ]
        return {
            "frame": {
                "width": SETTINGS.camera.frame_width,
                "height": SETTINGS.camera.frame_height,
            },
            "zones": self._latest_zones,
            "students": students,
            "invigilators": invigilators,
            "door": [zone for zone in self._latest_zones if zone.get("zone_type") == "door"],
            "restricted_areas": [
                zone for zone in self._latest_zones if zone.get("zone_type") == "restricted"
            ],
            "active_alerts": [
                {
                    "event_type": alert.event_type,
                    "tracking_id": alert.tracking_id,
                    "zone": alert.zone,
                    "bounding_box": alert.bounding_box,
                    "risk_score": alert.risk_score,
                }
                for alert in self._active_alerts.values()
            ],
            "patrol": self.patrol_coverage(),
        }

    def patrol_coverage(self) -> dict[str, Any]:
        """Estimate invigilator zone coverage from observed track zones."""

        observed_zones = {track.get("zone") for track in self._latest_tracks if track.get("zone")}
        expected = {"student", "invigilator", "door", "restricted"}
        visited = sorted(observed_zones & expected)
        blind = sorted(expected - observed_zones)
        coverage = int((len(visited) / len(expected)) * 100) if expected else 0
        recommendation = "Coverage acceptable."
        if blind:
            recommendation = f"Increase monitoring in {', '.join(blind)} zone(s)."
        return {
            "coverage_percentage": coverage,
            "visited_zones": visited,
            "blind_zones": blind,
            "recommendation": recommendation,
        }

    def evidence_center(self) -> list[dict[str, Any]]:
        """Return compact evidence cards."""

        return [
            {
                "event_id": alert.event_id,
                "event_type": alert.event_type,
                "timestamp": alert.timestamp,
                "tracking_id": alert.tracking_id,
                "zone": alert.zone,
                "confidence": alert.confidence,
                "risk_score": alert.risk_score,
                "screenshot": alert.screenshot,
                "bounding_box": alert.bounding_box,
            }
            for alert in reversed(self._alerts[-50:])
        ]

    def session_summary(self) -> dict[str, Any]:
        """Return JSON-ready session summary."""

        duration = datetime.now(UTC) - self.started_at
        counts: dict[str, int] = {}
        zone_risk: dict[str, int] = {}
        for alert in self._alerts:
            counts[alert.event_type] = counts.get(alert.event_type, 0) + 1
            zone_risk[alert.zone] = zone_risk.get(alert.zone, 0) + alert.risk_score

        top_risk_zones = [
            {"zone": zone, "risk_score": score}
            for zone, score in sorted(zone_risk.items(), key=lambda item: item[1], reverse=True)[:5]
        ]
        return {
            "exam_duration_seconds": int(duration.total_seconds()),
            "students_detected": len([track for track in self._latest_tracks if track.get("zone") != "invigilator"]),
            "invigilator_patrol_coverage": self.patrol_coverage(),
            "integrity_score": round(self.integrity_score),
            "risk_category": risk_category(100 - round(self.integrity_score)),
            "total_alerts": len(self._alerts),
            "critical_alerts": sum(1 for alert in self._alerts if alert.risk_score >= 85),
            "high_alerts": sum(1 for alert in self._alerts if 70 <= alert.risk_score < 85),
            "medium_alerts": sum(1 for alert in self._alerts if 45 <= alert.risk_score < 70),
            "low_alerts": sum(1 for alert in self._alerts if 20 <= alert.risk_score < 45),
            "event_counts": counts,
            "top_risk_zones": top_risk_zones,
            "ai_recommendations": [asdict(item) for item in self._recommendations[:5]],
            "human_summary": self.human_summary(counts, top_risk_zones),
        }

    def human_summary(self, counts: dict[str, int], top_risk_zones: list[dict[str, Any]]) -> str:
        if not self._alerts:
            return "Exam session remained stable. No AI alerts were generated."
        top_zone = top_risk_zones[0]["zone"] if top_risk_zones else "unknown"
        most_common = max(counts.items(), key=lambda item: item[1])[0]
        return (
            f"Session integrity is {round(self.integrity_score)}/100. "
            f"Most frequent event: {most_common}. Highest risk zone: {top_zone}. "
            "Review evidence and follow AI supervisor recommendations."
        )

    def _update_integrity(self, alert: AlertSignal) -> None:
        self._last_integrity_score = self.integrity_score
        simultaneous = max(0, len(self._active_alerts) - 1)
        penalty = min(35.0, alert.risk_score * 0.18 + simultaneous * 2.0)
        self.integrity_score = max(0.0, self.integrity_score - penalty)

    def _recover_integrity(self) -> None:
        if self._active_alerts:
            return
        self._last_integrity_score = self.integrity_score
        self.integrity_score = min(100.0, self.integrity_score + 0.05)

    def _trend(self) -> str:
        if self.integrity_score > self._last_integrity_score:
            return "Recovering"
        if self.integrity_score < self._last_integrity_score:
            return "Degrading"
        return "Stable"

    def _timeline_entry(self, alert: AlertSignal) -> dict[str, Any]:
        return {
            "timestamp": alert.timestamp,
            "title": alert.event_type,
            "status": "Created",
            "zone": alert.zone,
            "tracking_id": alert.tracking_id,
            "risk_score": alert.risk_score,
            "confidence": alert.confidence,
            "evidence": alert.screenshot,
        }

    def _recommendation_for(self, alert: AlertSignal) -> SupervisorRecommendation:
        recommendation_map = {
            "PHONE_USAGE": "Invigilator should inspect the student and verify unauthorized device usage.",
            "MULTIPLE_PHONE_USAGE": "Pause nearby activity and inspect the affected cluster immediately.",
            "STUDENT_GROUPING": "Invigilator should move toward the grouped students and separate them.",
            "CROWD_FORMATION": "Inspect the cluster and restore seating discipline.",
            "SUSPICIOUS_PROXIMITY": "Ask nearby students to maintain exam spacing.",
            "UNAUTHORIZED_ENTRY": "Verify identity and entry authorization at the door zone.",
            "EXCESSIVE_DOOR_ACTIVITY": "Reduce door movement and check whether repeated exits are valid.",
            "RESTRICTED_ZONE_ACCESS": "Move the student away from the restricted or invigilator-only zone.",
            "EMPTY_INVIGILATOR_ZONE": "Assign invigilator coverage to the unattended patrol zone.",
            "INVIGILATOR_LEFT_ROOM": "Ensure an invigilator returns or assign backup supervision.",
            "CAMERA_BLOCKED": "Check the camera view immediately.",
            "LONG_INACTIVITY": "Verify whether the tracked person requires attention.",
        }
        return SupervisorRecommendation(
            title=alert.event_type,
            recommendation=recommendation_map.get(alert.event_type, "Review evidence and inspect the zone."),
            reason=alert.description,
            confidence=alert.confidence,
            priority=risk_category(alert.risk_score),
            zone=alert.zone,
        )

    def _explain_alert(self, alert: AlertSignal) -> dict[str, Any]:
        return {
            "event_id": alert.event_id,
            "event_type": alert.event_type,
            "status": "Active",
            "what": alert.description,
            "where": alert.zone,
            "who": alert.tracking_id or "camera",
            "when": alert.timestamp,
            "why": self._recommendation_for(alert).reason,
            "evidence": alert.screenshot,
            "confidence": alert.confidence,
            "risk_score": alert.risk_score,
            "risk_category": risk_category(alert.risk_score),
            "bounding_box": alert.bounding_box,
        }

    def _track_to_mapping(self, track: Any) -> dict[str, Any]:
        bbox = getattr(track, "bbox", BoundingBox(x=0, y=0, width=1, height=1))
        center = getattr(track, "center", (0.0, 0.0))
        return {
            "tracking_id": getattr(track, "tracking_id", ""),
            "zone": getattr(track, "zone", "unknown"),
            "confidence": round(float(getattr(track, "confidence", 0.0)), 4),
            "center": {"x": round(center[0], 2), "y": round(center[1], 2)},
            "bounding_box": bbox.model_dump() if hasattr(bbox, "model_dump") else bbox,
            "average_speed": round(float(getattr(track, "average_speed", 0.0)), 2),
            "is_active": bool(getattr(track, "active", True)),
        }
