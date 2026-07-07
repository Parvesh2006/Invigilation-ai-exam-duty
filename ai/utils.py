"""Shared data models and geometry helpers for Sentinel AI."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from ai.config import BoundingBox, EventType


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for JSON alerts."""

    return datetime.now(UTC).isoformat()


def evidence_timestamp() -> str:
    """Return a compact timestamp suitable for screenshot filenames."""

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def new_event_id() -> str:
    """Create a stable unique identifier for an alert event."""

    return str(uuid.uuid4())


@dataclass(slots=True)
class Detection:
    """Object detector output normalized for the rest of the pipeline."""

    class_name: str
    confidence: float
    bbox: BoundingBox
    tracking_id: int | None = None

    @property
    def center(self) -> tuple[float, float]:
        return bbox_center(self.bbox)


@dataclass(slots=True)
class TrackedObject:
    """State for a tracked object across video frames."""

    tracking_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    first_seen: float
    last_seen: float
    last_moved_at: float
    missed_frames: int = 0
    active: bool = True
    zone: str = "unknown"
    trajectory: list[tuple[float, float]] = field(default_factory=list)
    movement_history: list[float] = field(default_factory=list)

    @property
    def center(self) -> tuple[float, float]:
        return bbox_center(self.bbox)

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.last_seen - self.first_seen)

    @property
    def movement_distance(self) -> float:
        return sum(self.movement_history)

    @property
    def average_speed(self) -> float:
        duration = self.duration_seconds
        return 0.0 if duration <= 0 else self.movement_distance / duration


@dataclass(slots=True)
class MotionResult:
    """Motion analyzer output for the current frame."""

    has_motion: bool
    intensity: float
    direction: str
    moving_area: int
    brightness: float
    dark_pixel_ratio: float
    camera_blocked: bool


@dataclass(slots=True)
class Anomaly:
    """Rule-engine anomaly before evidence and backend routing are attached."""

    event_type: EventType
    tracking_id: str
    confidence: float
    bounding_box: BoundingBox
    description: str
    zone: str = "unknown"
    event_key: str = ""
    status: str = "started"
    timestamp: float = 0.0


class AlertBoundingBox(BaseModel):
    """Exact bounding_box object required by the backend alert schema."""

    model_config = ConfigDict(frozen=True)

    x: int
    y: int
    width: int
    height: int


class AlertEvent(BaseModel):
    """Exact JSON alert schema required by the project brief."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: str
    timestamp: str
    camera_id: str
    tracking_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_score: int = Field(ge=0, le=100)
    zone: str
    bounding_box: AlertBoundingBox
    screenshot: str
    description: str

    @classmethod
    def from_anomaly(
        cls,
        anomaly: Anomaly,
        *,
        camera_id: str,
        risk_score: int,
        screenshot: str,
    ) -> AlertEvent:
        return cls(
            event_id=new_event_id(),
            event_type=anomaly.event_type.value,
            timestamp=utc_timestamp(),
            camera_id=camera_id,
            tracking_id=anomaly.tracking_id,
            confidence=round(float(anomaly.confidence), 4),
            risk_score=risk_score,
            zone=anomaly.zone,
            bounding_box=AlertBoundingBox(**anomaly.bounding_box.model_dump()),
            screenshot=screenshot,
            description=anomaly.description,
        )


def bbox_from_xyxy(x1: float, y1: float, x2: float, y2: float) -> BoundingBox:
    """Convert detector xyxy coordinates into the shared BoundingBox model."""

    left = max(0, int(round(min(x1, x2))))
    top = max(0, int(round(min(y1, y2))))
    right = max(left + 1, int(round(max(x1, x2))))
    bottom = max(top + 1, int(round(max(y1, y2))))
    return BoundingBox(x=left, y=top, width=right - left, height=bottom - top)


def bbox_center(box: BoundingBox) -> tuple[float, float]:
    return (box.x + box.width / 2.0, box.y + box.height / 2.0)


def bbox_area(box: BoundingBox) -> int:
    return box.width * box.height


def bbox_intersection(a: BoundingBox, b: BoundingBox) -> int:
    x1 = max(a.x, b.x)
    y1 = max(a.y, b.y)
    x2 = min(a.x2, b.x2)
    y2 = min(a.y2, b.y2)
    if x2 <= x1 or y2 <= y1:
        return 0
    return (x2 - x1) * (y2 - y1)


def bbox_iou(a: BoundingBox, b: BoundingBox) -> float:
    intersection = bbox_intersection(a, b)
    union = bbox_area(a) + bbox_area(b) - intersection
    return 0.0 if union <= 0 else intersection / union


def overlap_ratio(inner: BoundingBox, outer: BoundingBox) -> float:
    """Return how much of the first box overlaps the second box."""

    area = bbox_area(inner)
    return 0.0 if area <= 0 else bbox_intersection(inner, outer) / area


def point_in_bbox(point: tuple[float, float], box: BoundingBox) -> bool:
    x, y = point
    return box.x <= x <= box.x2 and box.y <= y <= box.y2


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def union_bbox(boxes: Iterable[BoundingBox]) -> BoundingBox:
    """Return the smallest BoundingBox enclosing all provided boxes."""

    collected = tuple(boxes)
    if not collected:
        return BoundingBox(x=0, y=0, width=1, height=1)
    x1 = min(box.x for box in collected)
    y1 = min(box.y for box in collected)
    x2 = max(box.x2 for box in collected)
    y2 = max(box.y2 for box in collected)
    return BoundingBox(x=x1, y=y1, width=max(1, x2 - x1), height=max(1, y2 - y1))


def clamp_bbox(box: BoundingBox, frame_width: int, frame_height: int) -> BoundingBox:
    """Clamp a box to the frame dimensions."""

    x1 = max(0, min(box.x, frame_width - 1))
    y1 = max(0, min(box.y, frame_height - 1))
    x2 = max(x1 + 1, min(box.x2, frame_width))
    y2 = max(y1 + 1, min(box.y2, frame_height))
    return BoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1)

