"""Lightweight multi-object tracker for person detections."""

from __future__ import annotations

import time

from ai.config import SETTINGS
from ai.utils import Detection, TrackedObject, bbox_iou, distance


class MultiObjectTracker:
    """Track people with detector IDs when available, otherwise IoU matching."""

    def __init__(
        self,
        *,
        iou_threshold: float = 0.20,
        max_center_distance: float = 120.0,
        max_missed_frames: int | None = None,
        movement_threshold: float | None = None,
        trajectory_limit: int = 64,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.max_center_distance = max_center_distance
        self.max_missed_frames = (
            max_missed_frames
            if max_missed_frames is not None
            else int(
                SETTINGS.camera.target_fps
                * (SETTINGS.anomalies.invigilator_left_seconds + 5.0)
            )
        )
        self.movement_threshold = (
            SETTINGS.motion.inactivity_motion_threshold
            if movement_threshold is None
            else movement_threshold
        )
        self.trajectory_limit = trajectory_limit
        self._tracks: dict[int, TrackedObject] = {}
        self._next_id = 1

    def update(self, detections: list[Detection], timestamp: float | None = None) -> list[TrackedObject]:
        now = time.time() if timestamp is None else timestamp
        person_detections = [det for det in detections if det.class_name == "person"]
        assigned_track_ids: set[int] = set()

        for detection in person_detections:
            track_id = detection.tracking_id if detection.tracking_id is not None else None
            if track_id is None or track_id not in self._tracks:
                track_id = self._match_existing_track(detection, assigned_track_ids)
            if track_id is None:
                track_id = self._next_id
                self._next_id += 1
                self._tracks[track_id] = TrackedObject(
                    tracking_id=track_id,
                    class_name=detection.class_name,
                    confidence=detection.confidence,
                    bbox=detection.bbox,
                    first_seen=now,
                    last_seen=now,
                    last_moved_at=now,
                    trajectory=[detection.center],
                )
            else:
                self._update_track(self._tracks[track_id], detection, now)
            assigned_track_ids.add(track_id)

        for track_id, track in tuple(self._tracks.items()):
            if track_id in assigned_track_ids:
                continue
            track.missed_frames += 1
            track.active = False
            if track.missed_frames > self.max_missed_frames:
                del self._tracks[track_id]

        return self.active_tracks()

    def active_tracks(self) -> list[TrackedObject]:
        return [track for track in self._tracks.values() if track.active]

    def get_active_tracks(self) -> list[TrackedObject]:
        """Compatibility API required by the AI engine contract."""

        return self.active_tracks()

    def missing_tracks(self) -> list[TrackedObject]:
        return [track for track in self._tracks.values() if not track.active]

    def all_tracks(self) -> list[TrackedObject]:
        return list(self._tracks.values())

    def _match_existing_track(
        self,
        detection: Detection,
        assigned_track_ids: set[int],
    ) -> int | None:
        best_track_id: int | None = None
        best_score = 0.0
        for track_id, track in self._tracks.items():
            if track_id in assigned_track_ids:
                continue
            iou = bbox_iou(detection.bbox, track.bbox)
            center_distance = distance(detection.center, track.center)
            distance_score = max(0.0, 1.0 - center_distance / self.max_center_distance)
            score = max(iou, distance_score)
            if (iou >= self.iou_threshold or center_distance <= self.max_center_distance) and score > best_score:
                best_track_id = track_id
                best_score = score
        return best_track_id

    def _update_track(self, track: TrackedObject, detection: Detection, now: float) -> None:
        previous_center = track.center
        new_center = detection.center
        movement_distance = distance(previous_center, new_center)
        track.movement_history.append(movement_distance)
        if movement_distance >= self.movement_threshold:
            track.last_moved_at = now

        track.class_name = detection.class_name
        track.confidence = detection.confidence
        track.bbox = detection.bbox
        track.last_seen = now
        track.missed_frames = 0
        track.active = True
        track.trajectory.append(new_center)
        if len(track.trajectory) > self.trajectory_limit:
            del track.trajectory[: len(track.trajectory) - self.trajectory_limit]
        if len(track.movement_history) > self.trajectory_limit:
            del track.movement_history[: len(track.movement_history) - self.trajectory_limit]
