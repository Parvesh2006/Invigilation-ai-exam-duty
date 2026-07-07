"""Rule engine for invigilation-duty anomaly detection."""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass

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


@dataclass(slots=True)
class EventState:
    """Lifecycle state for one anomaly key."""

    anomaly: Anomaly
    status: str
    started_at: float
    updated_at: float
    resolved_at: float | None = None


class AnomalyDetector:
    """Detect required anomalies from detections, tracks, zones, and motion."""

    def __init__(self, config: AppConfig = SETTINGS, zone_manager: ZoneManager | None = None) -> None:
        self.config = config
        self.zone_manager = zone_manager or ZoneManager(config)
        self._last_alert_at: dict[str, float] = {}
        self._door_seen_ids: set[int] = set()
        self._entry_alerted_ids: set[int] = set()
        self._left_room_alerted_ids: set[int] = set()
        self._group_first_seen_at: dict[str, float] = {}
        self._crowd_first_seen_at: dict[str, float] = {}
        self._proximity_first_seen_at: dict[str, float] = {}
        self._door_activity_events: list[float] = []
        self._track_in_door: dict[int, bool] = {}
        self._invigilator_track_id: int | None = None
        self._empty_invigilator_zone_since: float | None = None
        self._event_states: dict[str, EventState] = {}
        self._touched_event_keys: set[str] = set()

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
        self._touched_event_keys = set()
        self._update_invigilator_identity(active_tracks, now)
        self._update_door_activity(active_tracks, now)

        anomalies: list[Anomaly] = []
        anomalies.extend(self._detect_phone_usage(detections, active_tracks, now))
        anomalies.extend(self._detect_multiple_phone_usage(detections, active_tracks, now))
        anomalies.extend(self._detect_unauthorized_entry(active_tracks, now))
        anomalies.extend(self._detect_invigilator_left(missing_tracks, now))
        anomalies.extend(self._detect_long_inactivity(active_tracks, now))
        anomalies.extend(self._detect_student_grouping(active_tracks, now))
        anomalies.extend(self._detect_crowd_formation(active_tracks, now))
        anomalies.extend(self._detect_suspicious_proximity(active_tracks, now))
        anomalies.extend(self._detect_restricted_zone_access(active_tracks, now))
        anomalies.extend(self._detect_excessive_door_activity(now))
        anomalies.extend(self._detect_empty_invigilator_zone(active_tracks, now))
        anomalies.extend(self._detect_camera_blocked(frame, motion, now))
        self._resolve_untouched_events(now)
        return anomalies

    def active_anomalies(self, timestamp: float | None = None) -> list[Anomaly]:
        """Return active and recently resolved anomalies for visualization."""

        now = time.time() if timestamp is None else timestamp
        visible: list[Anomaly] = []
        for state in self._event_states.values():
            if state.status != "resolved":
                visible.append(state.anomaly)
                continue
            if state.resolved_at is None:
                continue
            if now - state.resolved_at <= self.config.debug.alert_visible_seconds:
                visible.append(state.anomaly)
        return visible

    def active_alert_count(self) -> int:
        """Return the number of currently active, unresolved anomalies."""

        return sum(1 for state in self._event_states.values() if state.status != "resolved")

    def _detect_phone_usage(
        self,
        detections: list[Detection],
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        phones = [
            det
            for det in detections
            if self._is_phone_detection(det)
            and det.confidence >= self.config.anomalies.phone_alert_min_confidence
        ]
        anomalies: list[Anomaly] = []
        for phone in phones:
            for track in active_tracks:
                ratio = overlap_ratio(phone.bbox, track.bbox)
                if ratio < self.config.anomalies.phone_person_overlap_ratio:
                    continue
                key = f"{EventType.PHONE_USAGE}:{track.tracking_id}"
                anomaly = Anomaly(
                        event_type=EventType.PHONE_USAGE,
                        tracking_id=str(track.tracking_id),
                        confidence=min(1.0, phone.confidence),
                        bounding_box=union_bbox((phone.bbox, track.bbox)),
                        zone=track.zone,
                        description=(
                            f"Cell phone detected overlapping tracked person "
                            f"{track.tracking_id}."
                        ),
                )
                emitted = self._start_or_update_event(key, anomaly, now)
                if emitted is not None:
                    anomalies.append(emitted)
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
            if self._is_current_invigilator(track):
                continue
            if track.tracking_id in self._entry_alerted_ids:
                continue
            key = f"{EventType.UNAUTHORIZED_ENTRY}:{track.tracking_id}"
            self._entry_alerted_ids.add(track.tracking_id)
            anomaly = Anomaly(
                    event_type=EventType.UNAUTHORIZED_ENTRY,
                    tracking_id=str(track.tracking_id),
                    confidence=track.confidence,
                    bounding_box=track.bbox,
                    zone=track.zone,
                    description=(
                        f"New tracked person {track.tracking_id} entered through "
                        "the configured door zone."
                    ),
            )
            emitted = self._start_or_update_event(key, anomaly, now)
            if emitted is not None:
                anomalies.append(emitted)
        return anomalies

    def _detect_multiple_phone_usage(
        self,
        detections: list[Detection],
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        phones = [
            detection
            for detection in detections
            if self._is_phone_detection(detection)
            and detection.confidence >= self.config.anomalies.phone_alert_min_confidence
        ]
        if len(phones) < 2:
            return []

        affected_tracks: list[TrackedObject] = []
        for phone in phones:
            for track in active_tracks:
                if overlap_ratio(phone.bbox, track.bbox) >= self.config.anomalies.phone_person_overlap_ratio:
                    affected_tracks.append(track)
                    break

        if len(affected_tracks) < 2:
            return []
        ids = ",".join(str(track.tracking_id) for track in affected_tracks)
        key = f"{EventType.MULTIPLE_PHONE_USAGE}:{ids}"
        confidence = sum(phone.confidence for phone in phones) / len(phones)
        anomaly = Anomaly(
            event_type=EventType.MULTIPLE_PHONE_USAGE,
            tracking_id=ids,
            confidence=confidence,
            bounding_box=union_bbox([phone.bbox for phone in phones] + [track.bbox for track in affected_tracks]),
            zone="student",
            description=f"{len(phones)} phones detected across tracks {ids}.",
        )
        emitted = self._start_or_update_event(key, anomaly, now)
        return [emitted] if emitted is not None else []

    def _detect_invigilator_left(
        self,
        missing_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for track in missing_tracks:
            if track.confidence < self.config.anomalies.person_alert_min_confidence:
                continue
            if not self._is_current_invigilator(track):
                continue
            if track.tracking_id not in self._door_seen_ids:
                continue
            if track.tracking_id in self._left_room_alerted_ids:
                continue
            absent_seconds = now - track.last_seen
            if absent_seconds < self.config.anomalies.invigilator_left_seconds:
                continue
            key = f"{EventType.INVIGILATOR_LEFT_ROOM}:{track.tracking_id}"
            self._left_room_alerted_ids.add(track.tracking_id)
            anomaly = Anomaly(
                    event_type=EventType.INVIGILATOR_LEFT_ROOM,
                    tracking_id=str(track.tracking_id),
                    confidence=track.confidence,
                    bounding_box=track.bbox,
                    zone=track.zone,
                    description=(
                        f"Tracked person {track.tracking_id} disappeared after door-zone "
                        f"activity and has been absent for {absent_seconds:.1f} seconds."
                    ),
            )
            emitted = self._start_or_update_event(key, anomaly, now)
            if emitted is not None:
                anomalies.append(emitted)
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
            anomaly = Anomaly(
                    event_type=EventType.LONG_INACTIVITY,
                    tracking_id=str(track.tracking_id),
                    confidence=track.confidence,
                    bounding_box=track.bbox,
                    zone=track.zone,
                    description=(
                        f"Tracked person {track.tracking_id} movement stayed below "
                        f"threshold for {inactive_seconds:.1f} seconds."
                    ),
            )
            emitted = self._start_or_update_event(key, anomaly, now)
            if emitted is not None:
                anomalies.append(emitted)
        return anomalies

    def _detect_student_grouping(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        min_people = self.config.anomalies.grouping_min_people
        if len(active_tracks) < min_people:
            self._group_first_seen_at.clear()
            return []

        threshold = self.config.anomalies.grouping_distance_pixels
        current_group_keys: set[str] = set()
        for group in itertools.combinations(active_tracks, min_people):
            distances = [
                distance(a.center, b.center)
                for a, b in itertools.combinations(group, 2)
            ]
            if not distances or max(distances) > threshold:
                continue
            ids = ",".join(str(track.tracking_id) for track in group)
            current_group_keys.add(ids)
            key = f"{EventType.STUDENT_GROUPING}:{ids}"
            first_seen = self._group_first_seen_at.setdefault(ids, now)
            if now - first_seen < self.config.anomalies.grouping_time_seconds:
                continue
            confidence = sum(track.confidence for track in group) / len(group)
            anomaly = Anomaly(
                event_type=EventType.STUDENT_GROUPING,
                tracking_id=ids,
                confidence=confidence,
                bounding_box=union_bbox(track.bbox for track in group),
                zone="student",
                description=(
                    f"{len(group)} tracked persons are within "
                    f"{threshold:.0f}px of each other."
                ),
            )
            emitted = self._start_or_update_event(key, anomaly, now)
            self._drop_stale_timer_keys(self._group_first_seen_at, current_group_keys)
            return [emitted] if emitted is not None else []
        self._drop_stale_timer_keys(self._group_first_seen_at, current_group_keys)
        return []

    def _detect_crowd_formation(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        min_people = self.config.anomalies.crowd_min_people
        student_tracks = [
            track
            for track in active_tracks
            if not self._is_current_invigilator(track)
            and track.confidence >= self.config.anomalies.person_alert_min_confidence
        ]
        if len(student_tracks) < min_people:
            self._crowd_first_seen_at.clear()
            return []

        radius = self.config.anomalies.crowd_radius_pixels
        current_crowd_keys: set[str] = set()
        for anchor in student_tracks:
            crowd = [
                track
                for track in student_tracks
                if distance(anchor.center, track.center) <= radius
            ]
            if len(crowd) < min_people:
                continue
            ids = ",".join(str(track.tracking_id) for track in sorted(crowd, key=lambda item: item.tracking_id))
            current_crowd_keys.add(ids)
            first_seen = self._crowd_first_seen_at.setdefault(ids, now)
            if now - first_seen < self.config.anomalies.crowd_time_seconds:
                continue
            confidence = sum(track.confidence for track in crowd) / len(crowd)
            key = f"{EventType.CROWD_FORMATION}:{ids}"
            anomaly = Anomaly(
                event_type=EventType.CROWD_FORMATION,
                tracking_id=ids,
                confidence=confidence,
                bounding_box=union_bbox(track.bbox for track in crowd),
                zone=anchor.zone,
                description=(
                    f"{len(crowd)} tracked students clustered within "
                    f"{radius:.0f}px around track {anchor.tracking_id}."
                ),
            )
            emitted = self._start_or_update_event(key, anomaly, now)
            self._drop_stale_timer_keys(self._crowd_first_seen_at, current_crowd_keys)
            return [emitted] if emitted is not None else []
        self._drop_stale_timer_keys(self._crowd_first_seen_at, current_crowd_keys)
        return []

    def _detect_suspicious_proximity(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        student_tracks = [
            track
            for track in active_tracks
            if not self._is_current_invigilator(track)
            and track.confidence >= self.config.anomalies.person_alert_min_confidence
        ]
        threshold = self.config.anomalies.suspicious_proximity_pixels
        hold_time = self.config.anomalies.suspicious_proximity_seconds
        current_pair_keys: set[str] = set()
        for first, second in itertools.combinations(student_tracks, 2):
            pair_distance = distance(first.center, second.center)
            if pair_distance > threshold:
                continue
            ids = ",".join(str(value) for value in sorted((first.tracking_id, second.tracking_id)))
            current_pair_keys.add(ids)
            first_seen = self._proximity_first_seen_at.setdefault(ids, now)
            if now - first_seen < hold_time:
                continue
            confidence = (first.confidence + second.confidence) / 2.0
            key = f"{EventType.SUSPICIOUS_PROXIMITY}:{ids}"
            anomaly = Anomaly(
                event_type=EventType.SUSPICIOUS_PROXIMITY,
                tracking_id=ids,
                confidence=confidence,
                bounding_box=union_bbox((first.bbox, second.bbox)),
                zone=first.zone if first.zone == second.zone else "mixed",
                description=(
                    f"Tracks {ids} remained within {threshold:.0f}px "
                    f"for {hold_time:.1f} seconds."
                ),
            )
            emitted = self._start_or_update_event(key, anomaly, now)
            self._drop_stale_timer_keys(self._proximity_first_seen_at, current_pair_keys)
            return [emitted] if emitted is not None else []
        self._drop_stale_timer_keys(self._proximity_first_seen_at, current_pair_keys)
        return []

    def _detect_restricted_zone_access(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for track in active_tracks:
            if self._is_current_invigilator(track):
                continue
            in_restricted = self.zone_manager.center_inside(track.bbox, ZoneType.RESTRICTED)
            in_invigilator_zone = self.zone_manager.center_inside(track.bbox, ZoneType.INVIGILATOR)
            if not in_restricted and not in_invigilator_zone:
                continue
            zone = ZoneType.RESTRICTED.value if in_restricted else ZoneType.INVIGILATOR.value
            key = f"{EventType.RESTRICTED_ZONE_ACCESS}:{track.tracking_id}:{zone}"
            anomaly = Anomaly(
                event_type=EventType.RESTRICTED_ZONE_ACCESS,
                tracking_id=str(track.tracking_id),
                confidence=track.confidence,
                bounding_box=track.bbox,
                zone=zone,
                description=(
                    f"Student track {track.tracking_id} entered {zone} zone."
                ),
            )
            emitted = self._start_or_update_event(key, anomaly, now)
            if emitted is not None:
                anomalies.append(emitted)
        return anomalies

    def _detect_excessive_door_activity(self, now: float) -> list[Anomaly]:
        window = self.config.anomalies.door_activity_window_seconds
        cutoff = now - window
        self._door_activity_events = [
            event_time for event_time in self._door_activity_events if event_time >= cutoff
        ]
        if len(self._door_activity_events) < self.config.anomalies.door_activity_max_events:
            return []
        key = EventType.EXCESSIVE_DOOR_ACTIVITY.value
        door_zone = self.config.zone_by_type(ZoneType.DOOR)
        box = door_zone[0].box if door_zone else BoundingBox(x=0, y=0, width=1, height=1)
        confidence = min(1.0, len(self._door_activity_events) / max(1, self.config.anomalies.door_activity_max_events))
        anomaly = Anomaly(
            event_type=EventType.EXCESSIVE_DOOR_ACTIVITY,
            tracking_id="",
            confidence=confidence,
            bounding_box=box,
            zone=ZoneType.DOOR.value,
            description=(
                f"{len(self._door_activity_events)} door-zone transitions detected "
                f"within {window:.1f} seconds."
            ),
        )
        emitted = self._start_or_update_event(key, anomaly, now)
        return [emitted] if emitted is not None else []

    def _detect_empty_invigilator_zone(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> list[Anomaly]:
        invigilator_present = any(
            self.zone_manager.center_inside(track.bbox, ZoneType.INVIGILATOR)
            and track.confidence >= self.config.anomalies.person_alert_min_confidence
            for track in active_tracks
        )
        if invigilator_present:
            self._empty_invigilator_zone_since = None
            return []
        if self._empty_invigilator_zone_since is None:
            self._empty_invigilator_zone_since = now
            return []
        absent_seconds = now - self._empty_invigilator_zone_since
        if absent_seconds < self.config.anomalies.empty_invigilator_zone_seconds:
            return []
        key = EventType.EMPTY_INVIGILATOR_ZONE.value
        invigilator_zone = self.config.zone_by_type(ZoneType.INVIGILATOR)
        box = invigilator_zone[0].box if invigilator_zone else BoundingBox(x=0, y=0, width=1, height=1)
        anomaly = Anomaly(
            event_type=EventType.EMPTY_INVIGILATOR_ZONE,
            tracking_id="",
            confidence=1.0,
            bounding_box=box,
            zone=ZoneType.INVIGILATOR.value,
            description=(
                f"No person detected in invigilator zone for "
                f"{absent_seconds:.1f} seconds."
            ),
        )
        emitted = self._start_or_update_event(key, anomaly, now)
        return [emitted] if emitted is not None else []

    def _detect_camera_blocked(
        self,
        frame: np.ndarray,
        motion: MotionResult,
        now: float,
    ) -> list[Anomaly]:
        if not motion.camera_blocked:
            return []
        key = EventType.CAMERA_BLOCKED.value
        height, width = frame.shape[:2]
        confidence = min(1.0, max(0.0, motion.dark_pixel_ratio))
        anomaly = Anomaly(
                event_type=EventType.CAMERA_BLOCKED,
                tracking_id="",
                confidence=confidence,
                bounding_box=BoundingBox(x=0, y=0, width=width, height=height),
                zone="camera",
                description=(
                    "Camera feed appears blocked or too dark "
                    f"(brightness={motion.brightness:.1f}, dark_ratio={motion.dark_pixel_ratio:.2f})."
                ),
        )
        emitted = self._start_or_update_event(key, anomaly, now)
        return [emitted] if emitted is not None else []

    def _update_invigilator_identity(
        self,
        active_tracks: list[TrackedObject],
        now: float,
    ) -> None:
        if self._invigilator_track_id is not None:
            for track in active_tracks:
                if track.tracking_id == self._invigilator_track_id:
                    if self.zone_manager.center_inside(track.bbox, ZoneType.INVIGILATOR):
                        return
                    break

        candidates = [
            track
            for track in active_tracks
            if self.zone_manager.center_inside(track.bbox, ZoneType.INVIGILATOR)
            and now - track.first_seen >= self.config.anomalies.invigilator_recognition_seconds
        ]
        if candidates:
            self._invigilator_track_id = max(candidates, key=lambda track: track.confidence).tracking_id

    def _update_door_activity(self, active_tracks: list[TrackedObject], now: float) -> None:
        for track in active_tracks:
            in_door = self.zone_manager.center_inside(track.bbox, ZoneType.DOOR)
            was_in_door = self._track_in_door.get(track.tracking_id, False)
            if in_door and not was_in_door:
                self._door_activity_events.append(now)
                self._door_seen_ids.add(track.tracking_id)
            self._track_in_door[track.tracking_id] = in_door

    def _is_current_invigilator(self, track: TrackedObject) -> bool:
        return self._invigilator_track_id == track.tracking_id

    def _is_phone_detection(self, detection: Detection) -> bool:
        return detection.class_name.lower().replace("_", " ") == "cell phone"

    def _drop_stale_timer_keys(self, timers: dict[str, float], current_keys: set[str]) -> None:
        for key in tuple(timers):
            if key not in current_keys:
                del timers[key]

    def _start_or_update_event(
        self,
        key: str,
        anomaly: Anomaly,
        now: float,
    ) -> Anomaly | None:
        self._touched_event_keys.add(key)
        anomaly.event_key = key
        anomaly.timestamp = now
        state = self._event_states.get(key)
        if state is not None and state.status != "resolved":
            anomaly.status = "active"
            state.status = "active"
            state.updated_at = now
            state.anomaly = anomaly
            return None

        last_alert = self._last_alert_at.get(key)
        cooldown = self.config.anomalies.duplicate_alert_cooldown_seconds
        if last_alert is not None and now - last_alert < cooldown:
            return None

        anomaly.status = "started"
        self._event_states[key] = EventState(
            anomaly=anomaly,
            status="started",
            started_at=now,
            updated_at=now,
        )
        self._last_alert_at[key] = now
        return anomaly

    def _resolve_untouched_events(self, now: float) -> None:
        for key, state in self._event_states.items():
            if state.status == "resolved" or key in self._touched_event_keys:
                continue
            state.status = "resolved"
            state.resolved_at = now
            state.anomaly.status = "resolved"
            state.anomaly.timestamp = now
