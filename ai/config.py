"""Centralized configuration for the Sentinel AI engine.

The rest of the AI modules should import settings from this file instead of
hard-coding camera, model, zone, threshold, or backend parameters.
"""

from __future__ import annotations

import json
import os
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
LOGS_DIR = PROJECT_ROOT / "logs"


class EventType(StrEnum):
    """Supported anomaly event types.

    Keep these values aligned with the fixed alert JSON contract.
    """

    PHONE_USAGE = "PHONE_USAGE"
    INVIGILATOR_LEFT_ROOM = "INVIGILATOR_LEFT_ROOM"
    LONG_INACTIVITY = "LONG_INACTIVITY"
    UNAUTHORIZED_ENTRY = "UNAUTHORIZED_ENTRY"
    STUDENT_GROUPING = "STUDENT_GROUPING"
    CAMERA_BLOCKED = "CAMERA_BLOCKED"


class ZoneType(StrEnum):
    """Known logical zones in the examination hall."""

    DOOR = "door"
    INVIGILATOR = "invigilator"
    STUDENT = "student"
    RESTRICTED = "restricted"


class BoundingBox(BaseModel):
    """Pixel-space rectangle used for zones and detections."""

    model_config = ConfigDict(frozen=True)

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)

    @property
    def x2(self) -> int:
        """Right edge coordinate."""

        return self.x + self.width

    @property
    def y2(self) -> int:
        """Bottom edge coordinate."""

        return self.y + self.height


class ZoneConfig(BaseModel):
    """Named configurable area in the camera frame."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    zone_type: ZoneType
    box: BoundingBox
    enabled: bool = True
    description: str = ""


class CameraConfig(BaseModel):
    """Camera capture and processing cadence settings."""

    model_config = ConfigDict(frozen=True)

    camera_id: str = Field(default="exam_hall_camera_01", min_length=1)
    device_index: int = Field(default=0, ge=0)
    target_fps: int = Field(default=30, ge=1, le=60)
    frame_width: int = Field(default=1280, ge=320)
    frame_height: int = Field(default=720, ge=240)
    reconnect_delay_seconds: float = Field(default=2.0, ge=0.1)
    read_timeout_seconds: float = Field(default=5.0, ge=0.5)
    mirror_frame: bool = False


class ModelConfig(BaseModel):
    """YOLO model and class filtering settings."""

    model_config = ConfigDict(frozen=True)

    primary_model: str = "yolo11n.pt"
    fallback_model: str = "yolov8n.pt"
    model_dir: Path = MODELS_DIR
    confidence_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    device: str = "auto"
    image_size: int = Field(default=640, ge=320)
    classes: tuple[str, ...] = ("person", "cell phone", "backpack", "book", "chair")
    class_confidence_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "person": 0.55,
            "cell phone": 0.65,
            "backpack": 0.60,
            "book": 0.60,
            "chair": 0.55,
        }
    )
    tracker_config: str = "bytetrack.yaml"

    @field_validator("model_dir", mode="before")
    @classmethod
    def _coerce_model_dir(cls, value: str | Path) -> Path:
        return Path(value)


class MotionConfig(BaseModel):
    """OpenCV motion and inactivity thresholds."""

    model_config = ConfigDict(frozen=True)

    motion_threshold: float = Field(default=18.0, ge=0.0)
    min_motion_area: int = Field(default=700, ge=1)
    inactivity_seconds: float = Field(default=30.0, ge=1.0)
    inactivity_motion_threshold: float = Field(default=4.0, ge=0.0)
    background_history: int = Field(default=120, ge=1)
    direction_window: int = Field(default=8, ge=2)


class AnomalyConfig(BaseModel):
    """Rule-engine thresholds for the supported anomalies."""

    model_config = ConfigDict(frozen=True)

    phone_person_overlap_ratio: float = Field(default=0.12, ge=0.0, le=1.0)
    phone_alert_min_confidence: float = Field(default=0.65, ge=0.0, le=1.0)
    person_alert_min_confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    door_entry_requires_center_inside: bool = True
    door_entry_max_track_age_seconds: float = Field(default=3.0, ge=0.0)
    invigilator_left_seconds: float = Field(default=20.0, ge=1.0)
    grouping_distance_pixels: float = Field(default=140.0, ge=1.0)
    grouping_min_people: int = Field(default=3, ge=2)
    camera_blocked_brightness_threshold: float = Field(default=25.0, ge=0.0, le=255.0)
    camera_blocked_dark_pixel_ratio: float = Field(default=0.92, ge=0.0, le=1.0)
    duplicate_alert_cooldown_seconds: float = Field(default=10.0, ge=0.0)


class EvidenceConfig(BaseModel):
    """Screenshot and evidence storage settings."""

    model_config = ConfigDict(frozen=True)

    screenshot_dir: Path = SCREENSHOTS_DIR
    image_format: str = Field(default="jpg", pattern="^(jpg|jpeg|png)$")
    jpeg_quality: int = Field(default=90, ge=1, le=100)
    draw_annotations: bool = True
    max_retained_screenshots: int = Field(default=500, ge=1)

    @field_validator("screenshot_dir", mode="before")
    @classmethod
    def _coerce_screenshot_dir(cls, value: str | Path) -> Path:
        return Path(value)


class AlertConfig(BaseModel):
    """Backend alert routing and retry settings."""

    model_config = ConfigDict(frozen=True)

    backend_url: str = "http://localhost:8000/api/alerts"
    request_timeout_seconds: float = Field(default=2.0, ge=0.1)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=0.5, ge=0.0)
    send_alerts: bool = True
    queue_max_size: int = Field(default=128, ge=1)


class LoggingConfig(BaseModel):
    """Logging output configuration."""

    model_config = ConfigDict(frozen=True)

    log_dir: Path = LOGS_DIR
    level: str = "INFO"
    file_name: str = "sentinel_ai.log"
    rotation: str = "10 MB"
    retention: str = "7 days"

    @field_validator("log_dir", mode="before")
    @classmethod
    def _coerce_log_dir(cls, value: str | Path) -> Path:
        return Path(value)


class AppConfig(BaseModel):
    """Top-level immutable application configuration."""

    model_config = ConfigDict(frozen=True)

    camera: CameraConfig = Field(default_factory=CameraConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    motion: MotionConfig = Field(default_factory=MotionConfig)
    anomalies: AnomalyConfig = Field(default_factory=AnomalyConfig)
    evidence: EvidenceConfig = Field(default_factory=EvidenceConfig)
    alert: AlertConfig = Field(default_factory=AlertConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    zones: tuple[ZoneConfig, ...] = Field(default_factory=tuple)
    risk_scores: dict[EventType, int] = Field(default_factory=dict)

    DEFAULT_RISK_SCORES: ClassVar[dict[EventType, int]] = {
        EventType.PHONE_USAGE: 40,
        EventType.INVIGILATOR_LEFT_ROOM: 80,
        EventType.LONG_INACTIVITY: 50,
        EventType.UNAUTHORIZED_ENTRY: 90,
        EventType.STUDENT_GROUPING: 60,
        EventType.CAMERA_BLOCKED: 100,
    }

    @model_validator(mode="after")
    def _populate_defaults(self) -> AppConfig:
        zones = self.zones or default_zones(
            self.camera.frame_width,
            self.camera.frame_height,
        )
        risk_scores = self.risk_scores or self.DEFAULT_RISK_SCORES
        missing_events = set(EventType) - set(risk_scores)
        if missing_events:
            missing = ", ".join(sorted(event.value for event in missing_events))
            raise ValueError(f"Missing risk score for: {missing}")

        normalized_scores = {event: int(score) for event, score in risk_scores.items()}
        for event, score in normalized_scores.items():
            if not 0 <= score <= 100:
                raise ValueError(f"Risk score for {event.value} must be between 0 and 100")

        object.__setattr__(self, "zones", zones)
        object.__setattr__(self, "risk_scores", normalized_scores)
        return self

    @property
    def active_zones(self) -> tuple[ZoneConfig, ...]:
        """Enabled zones only."""

        return tuple(zone for zone in self.zones if zone.enabled)

    def zone_by_type(self, zone_type: ZoneType) -> tuple[ZoneConfig, ...]:
        """Return all enabled zones matching the requested type."""

        return tuple(zone for zone in self.active_zones if zone.zone_type == zone_type)

    def risk_score_for(self, event_type: EventType | str) -> int:
        """Resolve a risk score for a supported event type."""

        return self.risk_scores[EventType(event_type)]

    def ensure_directories(self) -> None:
        """Create directories required by model, screenshot, and logging modules."""

        for directory in (
            self.model.model_dir,
            self.evidence.screenshot_dir,
            self.logging.log_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def default_zones(frame_width: int = 1280, frame_height: int = 720) -> tuple[ZoneConfig, ...]:
    """Build sensible default zones scaled to the configured frame size."""

    door_width = max(120, int(frame_width * 0.16))
    invigilator_width = max(180, int(frame_width * 0.22))
    restricted_height = max(90, int(frame_height * 0.14))

    return (
        ZoneConfig(
            name="main_door",
            zone_type=ZoneType.DOOR,
            box=BoundingBox(
                x=0,
                y=0,
                width=door_width,
                height=frame_height,
            ),
            description="Entry and exit area near the examination hall door.",
        ),
        ZoneConfig(
            name="invigilator_desk",
            zone_type=ZoneType.INVIGILATOR,
            box=BoundingBox(
                x=max(0, frame_width - invigilator_width),
                y=0,
                width=invigilator_width,
                height=frame_height,
            ),
            description="Expected invigilator supervision area.",
        ),
        ZoneConfig(
            name="student_area",
            zone_type=ZoneType.STUDENT,
            box=BoundingBox(
                x=door_width,
                y=restricted_height,
                width=max(1, frame_width - door_width - invigilator_width),
                height=max(1, frame_height - restricted_height),
            ),
            description="Primary student seating area.",
        ),
        ZoneConfig(
            name="front_restricted_area",
            zone_type=ZoneType.RESTRICTED,
            box=BoundingBox(
                x=door_width,
                y=0,
                width=max(1, frame_width - door_width),
                height=restricted_height,
            ),
            description="Restricted front area where unsupervised entry should alert.",
        ),
    )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return default if value is None else Path(value)


def _parse_json_env(name: str, default: Any) -> Any:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return json.loads(value)


def _load_zones_from_env() -> tuple[ZoneConfig, ...]:
    raw_zones = _parse_json_env("SENTINEL_ZONES_JSON", [])
    return tuple(ZoneConfig.model_validate(zone) for zone in raw_zones)


def _load_risk_scores_from_env() -> dict[EventType, int]:
    raw_scores = _parse_json_env("SENTINEL_RISK_SCORES_JSON", {})
    return {EventType(event_type): int(score) for event_type, score in raw_scores.items()}


def _load_class_confidences_from_env() -> dict[str, float]:
    raw_scores = _parse_json_env("SENTINEL_CLASS_CONFIDENCE_JSON", {})
    return {str(class_name): float(score) for class_name, score in raw_scores.items()}


def _load_detection_classes_from_env() -> tuple[str, ...]:
    value = os.getenv("SENTINEL_DETECTION_CLASSES")
    if value is None or value.strip() == "":
        return ModelConfig().classes
    return tuple(class_name.strip() for class_name in value.split(",") if class_name.strip())


def load_config() -> AppConfig:
    """Load configuration from environment variables with validated defaults.

    All environment variables are optional. Complex values can be supplied as
    JSON through SENTINEL_ZONES_JSON and SENTINEL_RISK_SCORES_JSON.
    """

    config = AppConfig(
        camera=CameraConfig(
            camera_id=os.getenv("SENTINEL_CAMERA_ID", "exam_hall_camera_01"),
            device_index=_env_int("SENTINEL_CAMERA_DEVICE_INDEX", 0),
            target_fps=_env_int("SENTINEL_TARGET_FPS", 30),
            frame_width=_env_int("SENTINEL_FRAME_WIDTH", 1280),
            frame_height=_env_int("SENTINEL_FRAME_HEIGHT", 720),
            reconnect_delay_seconds=_env_float("SENTINEL_CAMERA_RECONNECT_DELAY", 2.0),
            read_timeout_seconds=_env_float("SENTINEL_CAMERA_READ_TIMEOUT", 5.0),
            mirror_frame=_env_bool("SENTINEL_MIRROR_FRAME", False),
        ),
        model=ModelConfig(
            primary_model=os.getenv("SENTINEL_YOLO_MODEL", "yolo11n.pt"),
            fallback_model=os.getenv("SENTINEL_YOLO_FALLBACK_MODEL", "yolov8n.pt"),
            model_dir=_env_path("SENTINEL_MODEL_DIR", MODELS_DIR),
            confidence_threshold=_env_float("SENTINEL_CONFIDENCE_THRESHOLD", 0.55),
            iou_threshold=_env_float("SENTINEL_IOU_THRESHOLD", 0.50),
            device=os.getenv("SENTINEL_MODEL_DEVICE", "auto"),
            image_size=_env_int("SENTINEL_IMAGE_SIZE", 640),
            classes=_load_detection_classes_from_env(),
            class_confidence_thresholds=_load_class_confidences_from_env()
            or ModelConfig().class_confidence_thresholds,
            tracker_config=os.getenv("SENTINEL_TRACKER_CONFIG", "bytetrack.yaml"),
        ),
        motion=MotionConfig(
            motion_threshold=_env_float("SENTINEL_MOTION_THRESHOLD", 18.0),
            min_motion_area=_env_int("SENTINEL_MIN_MOTION_AREA", 700),
            inactivity_seconds=_env_float("SENTINEL_INACTIVITY_SECONDS", 30.0),
            inactivity_motion_threshold=_env_float(
                "SENTINEL_INACTIVITY_MOTION_THRESHOLD",
                4.0,
            ),
            background_history=_env_int("SENTINEL_BACKGROUND_HISTORY", 120),
            direction_window=_env_int("SENTINEL_DIRECTION_WINDOW", 8),
        ),
        anomalies=AnomalyConfig(
            phone_person_overlap_ratio=_env_float("SENTINEL_PHONE_OVERLAP_RATIO", 0.12),
            phone_alert_min_confidence=_env_float("SENTINEL_PHONE_ALERT_MIN_CONFIDENCE", 0.65),
            person_alert_min_confidence=_env_float("SENTINEL_PERSON_ALERT_MIN_CONFIDENCE", 0.55),
            door_entry_requires_center_inside=_env_bool(
                "SENTINEL_DOOR_ENTRY_REQUIRES_CENTER",
                True,
            ),
            door_entry_max_track_age_seconds=_env_float(
                "SENTINEL_DOOR_ENTRY_MAX_TRACK_AGE",
                3.0,
            ),
            invigilator_left_seconds=_env_float("SENTINEL_INVIGILATOR_LEFT_SECONDS", 20.0),
            grouping_distance_pixels=_env_float("SENTINEL_GROUPING_DISTANCE", 140.0),
            grouping_min_people=_env_int("SENTINEL_GROUPING_MIN_PEOPLE", 3),
            camera_blocked_brightness_threshold=_env_float(
                "SENTINEL_CAMERA_BLOCKED_BRIGHTNESS",
                25.0,
            ),
            camera_blocked_dark_pixel_ratio=_env_float(
                "SENTINEL_CAMERA_BLOCKED_DARK_PIXEL_RATIO",
                0.92,
            ),
            duplicate_alert_cooldown_seconds=_env_float(
                "SENTINEL_DUPLICATE_ALERT_COOLDOWN",
                10.0,
            ),
        ),
        evidence=EvidenceConfig(
            screenshot_dir=_env_path("SENTINEL_SCREENSHOT_DIR", SCREENSHOTS_DIR),
            image_format=os.getenv("SENTINEL_SCREENSHOT_FORMAT", "jpg"),
            jpeg_quality=_env_int("SENTINEL_JPEG_QUALITY", 90),
            draw_annotations=_env_bool("SENTINEL_DRAW_ANNOTATIONS", True),
            max_retained_screenshots=_env_int("SENTINEL_MAX_SCREENSHOTS", 500),
        ),
        alert=AlertConfig(
            backend_url=os.getenv("SENTINEL_BACKEND_URL", "http://localhost:8000/api/alerts"),
            request_timeout_seconds=_env_float("SENTINEL_ALERT_TIMEOUT", 2.0),
            max_retries=_env_int("SENTINEL_ALERT_MAX_RETRIES", 3),
            retry_backoff_seconds=_env_float("SENTINEL_ALERT_RETRY_BACKOFF", 0.5),
            send_alerts=_env_bool("SENTINEL_SEND_ALERTS", True),
            queue_max_size=_env_int("SENTINEL_ALERT_QUEUE_SIZE", 128),
        ),
        logging=LoggingConfig(
            log_dir=_env_path("SENTINEL_LOG_DIR", LOGS_DIR),
            level=os.getenv("SENTINEL_LOG_LEVEL", "INFO"),
            file_name=os.getenv("SENTINEL_LOG_FILE", "sentinel_ai.log"),
            rotation=os.getenv("SENTINEL_LOG_ROTATION", "10 MB"),
            retention=os.getenv("SENTINEL_LOG_RETENTION", "7 days"),
        ),
        zones=_load_zones_from_env(),
        risk_scores=_load_risk_scores_from_env(),
    )
    config.ensure_directories()
    return config


SETTINGS = load_config()


__all__ = [
    "AlertConfig",
    "AnomalyConfig",
    "AppConfig",
    "BoundingBox",
    "CameraConfig",
    "EventType",
    "EvidenceConfig",
    "LoggingConfig",
    "ModelConfig",
    "MotionConfig",
    "PROJECT_ROOT",
    "SETTINGS",
    "ZoneConfig",
    "ZoneType",
    "default_zones",
    "load_config",
]
