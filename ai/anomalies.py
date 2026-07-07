"""Rule engine for invigilation-duty anomaly detection."""

from __future__ import annotations

import itertools
import time

import numpy as np

from ai.config import AppConfig, BoundingBox, EventType, SETTINGS, ZoneType
from ai.utils import (
    Anomaly,
    Detection,
    MotionResult,
    TrackedObject,
    distance,
    overlap_ratio,
    union_bbox,
)
from ai.zones import ZoneManager


class AnomalyDetector:
    """Detect required anomalies from detections, tracks, zones, and motion."""

    def __init__(self, config: AppConfig = SETTINGS, zone_manager: ZoneManager | None = None) -> None:
        self.config = config
        self.zone_manager = zone_manager or ZoneManager(config)
        self._last_alert_at: dict[str, float] = {}
        self._door_seen_ids: set[int] = set()
        self._entry_alerted_ids: set[int] = set()
        self._left_room_alerted_ids: set[int] = set()

    def detect(
        self,
        *,
        frame: np.ndarray,
        detections: list[Detection],
        active_tracks: list[TrackedObject],
        missing_tracks: list[TrackedObject],
        motion: MotionResult,
        timestamp: float | None = None,
    ) -> list[Anomaly]:
        now = time.time() if timestamp is None else timestamp
        anomalies: list[Anomaly] = []
        anomalies.extend(self._detect_phone_usage(detections, active_tracks, now))
        anomalies.extend(self._detect_unauthorized_entry(active_tracks, now))
        anomalies.extend(self._detect_invigilator_left(missing_tracks, now))
        anomalies.extend(self._detect_long_inactivity(active_tracks, now))
        anomalies.extend(self._detect_student_grouping(active_tracks, now))
        anomalies.extend(self._detect_camera_blocked(frame, motion, now))
        return anomalies

    def _detect_phone_usage(
        self,
        detections: list[Detection],
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        phones = [
            det
            for det in detections
            if det.class_name == "cell phone"
            and det.confidence >= self.config.anomalies.phone_alert_min_confidence
        ]
        anomalies: list[Anomaly] = []
        for phone in phones:
            for track in active_tracks:
                ratio = overlap_ratio(phone.bbox, track.bbox)
                if ratio < self.config.anomalies.phone_person_overlap_ratio:
                    continue
                key = f"{EventType.PHONE_USAGE}:{track.tracking_id}"
                if not self._can_alert(key, now):
                    continue
                anomalies.append(
                    Anomaly(
                        event_type=EventType.PHONE_USAGE,
                        tracking_id=str(track.tracking_id),
                        confidence=min(1.0, phone.confidence),
                        bounding_box=union_bbox((phone.bbox, track.bbox)),
                        description=(
                            f"Cell phone detected overlapping tracked person "
                            f"{track.tracking_id}."
                        ),
                    )
                )
        return anomalies

    def _detect_unauthorized_entry(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for track in active_tracks:
            if track.confidence < self.config.anomalies.person_alert_min_confidence:
                continue

            track_age = now - track.first_seen
            if track_age > self.config.anomalies.door_entry_max_track_age_seconds:
                continue

            if self.config.anomalies.door_entry_requires_center_inside:
                in_door = self.zone_manager.center_inside(track.bbox, ZoneType.DOOR)
            else:
                in_door = self.zone_manager.intersects(track.bbox, ZoneType.DOOR)
            if not in_door:
                continue
            self._door_seen_ids.add(track.tracking_id)
            if track.tracking_id in self._entry_alerted_ids:
                continue
            key = f"{EventType.UNAUTHORIZED_ENTRY}:{track.tracking_id}"
            if not self._can_alert(key, now):
                continue
            self._entry_alerted_ids.add(track.tracking_id)
            anomalies.append(
                Anomaly(
                    event_type=EventType.UNAUTHORIZED_ENTRY,
                    tracking_id=str(track.tracking_id),
                    confidence=track.confidence,
                    bounding_box=track.bbox,
                    description=(
                        f"New tracked person {track.tracking_id} entered through "
                        "the configured door zone."
                    ),
                )
            )
        return anomalies

    def _detect_invigilator_left(
        self,
        missing_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for track in missing_tracks:
            if track.confidence < self.config.anomalies.person_alert_min_confidence:
                continue
            if track.tracking_id not in self._door_seen_ids:
                continue
            if track.tracking_id in self._left_room_alerted_ids:
                continue
            absent_seconds = now - track.last_seen
            if absent_seconds < self.config.anomalies.invigilator_left_seconds:
                continue
            key = f"{EventType.INVIGILATOR_LEFT_ROOM}:{track.tracking_id}"
            if not self._can_alert(key, now):
                continue
            self._left_room_alerted_ids.add(track.tracking_id)
            anomalies.append(
                Anomaly(
                    event_type=EventType.INVIGILATOR_LEFT_ROOM,
                    tracking_id=str(track.tracking_id),
                    confidence=track.confidence,
                    bounding_box=track.bbox,
                    description=(
                        f"Tracked person {track.tracking_id} disappeared after door-zone "
                        f"activity and has been absent for {absent_seconds:.1f} seconds."
                    ),
                )
            )
        return anomalies

    def _detect_long_inactivity(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for track in active_tracks:
            inactive_seconds = now - track.last_moved_at
            if inactive_seconds < self.config.motion.inactivity_seconds:
                continue
            key = f"{EventType.LONG_INACTIVITY}:{track.tracking_id}"
            if not self._can_alert(key, now):
                continue
            anomalies.append(
                Anomaly(
                    event_type=EventType.LONG_INACTIVITY,
                    tracking_id=str(track.tracking_id),
                    confidence=track.confidence,
                    bounding_box=track.bbox,
                    description=(
                        f"Tracked person {track.tracking_id} movement stayed below "
                        f"threshold for {inactive_seconds:.1f} seconds."
                    ),
                )
            )
        return anomalies

    def _detect_student_grouping(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        min_people = self.config.anomalies.grouping_min_people
        if len(active_tracks) < min_people:
            return []

        threshold = self.config.anomalies.grouping_distance_pixels
        for group in itertools.combinations(active_tracks, min_people):
            distances = [
                distance(a.center, b.center)
                for a, b in itertools.combinations(group, 2)
            ]
            if not distances or max(distances) > threshold:
                continue
            ids = ",".join(str(track.tracking_id) for track in group)
            key = f"{EventType.STUDENT_GROUPING}:{ids}"
            if not self._can_alert(key, now):
                continue
            confidence = sum(track.confidence for track in group) / len(group)
            return [
                Anomaly(
                    event_type=EventType.STUDENT_GROUPING,
                    tracking_id=ids,
                    confidence=confidence,
                    bounding_box=union_bbox(track.bbox for track in group),
                    description=(
                        f"{len(group)} tracked persons are within "
                        f"{threshold:.0f}px of each other."
                    ),
                )
            ]
        return []

    def _detect_camera_blocked(
        self,
        frame: np.ndarray,
        motion: MotionResult,
        now: float,
    ) -> list[Anomaly]:
        if not motion.camera_blocked:
            return []
        key = EventType.CAMERA_BLOCKED.value
        if not self._can_alert(key, now):
            return []
        height, width = frame.shape[:2]
        confidence = min(1.0, max(0.0, motion.dark_pixel_ratio))
        return [
            Anomaly(
                event_type=EventType.CAMERA_BLOCKED,
                tracking_id="",
                confidence=confidence,
                bounding_box=BoundingBox(x=0, y=0, width=width, height=height),
                description=(
                    "Camera feed appears blocked or too dark "
                    f"(brightness={motion.brightness:.1f}, dark_ratio={motion.dark_pixel_ratio:.2f})."
                ),
            )
        ]

    def _can_alert(self, key: str, now: float) -> bool:
        last_alert = self._last_alert_at.get(key)
        cooldown = self.config.anomalies.duplicate_alert_cooldown_seconds
        if last_alert is not None and now - last_alert < cooldown:
            return False
        self._last_alert_at[key] = now
        return True
