"""Visual debug overlay for local AI engine testing."""

from __future__ import annotations

import time

import cv2
import numpy as np

from ai.config import AppConfig, SETTINGS
from ai.utils import Anomaly, Detection, MotionResult, TrackedObject
from ai.zones import ZoneManager


class DebugOverlay:
    """Draw runtime diagnostics without changing detection behavior."""

    def __init__(self, config: AppConfig = SETTINGS, zone_manager: ZoneManager | None = None) -> None:
        self.config = config
        self.zone_manager = zone_manager or ZoneManager(config)

    def draw(
        self,
        frame: np.ndarray,
        *,
        detections: list[Detection],
        tracks: list[TrackedObject],
        motion: MotionResult,
        anomalies: list[Anomaly],
        fps: float,
    ) -> np.ndarray:
        now = time.time()
        image = self.zone_manager.draw_zones(frame)
        for detection in detections:
            color = (255, 255, 0) if detection.class_name != "person" else (0, 255, 0)
            box = detection.bbox
            cv2.rectangle(image, (box.x, box.y), (box.x2, box.y2), color, 1)
            cv2.putText(
                image,
                f"{detection.class_name} {detection.confidence:.2f}",
                (box.x, max(14, box.y - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                1,
                cv2.LINE_AA,
            )

        for track in tracks:
            box = track.bbox
            cv2.rectangle(image, (box.x, box.y), (box.x2, box.y2), (0, 165, 255), 2)
            cv2.putText(
                image,
                f"ID:{track.tracking_id} zone:{track.zone} speed:{track.average_speed:.1f}",
                (box.x, min(image.shape[0] - 8, box.y2 + 18)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 165, 255),
                1,
                cv2.LINE_AA,
            )
            for start, end in zip(track.trajectory, track.trajectory[1:]):
                cv2.line(
                    image,
                    (int(start[0]), int(start[1])),
                    (int(end[0]), int(end[1])),
                    (0, 165, 255),
                    1,
                )

        active_anomalies = [anomaly for anomaly in anomalies if anomaly.status != "resolved"]
        current_risk = min(
            100,
            sum(self.config.risk_score_for(anomaly.event_type) for anomaly in active_anomalies),
        )
        integrity_score = max(0, 100 - current_risk)
        self._draw_active_alerts(image, anomalies, now)

        status_lines = [
            f"FPS: {fps:.1f}",
            f"Objects: {len(detections)} Tracks: {len(tracks)}",
            f"Motion: {motion.direction} intensity:{motion.intensity:.1f}",
            f"Camera blocked: {motion.camera_blocked}",
            f"Active alerts: {len(active_anomalies)} Risk: {current_risk} Integrity: {integrity_score}",
        ]
        y = 22
        for line in status_lines:
            cv2.putText(
                image,
                line,
                (12, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            y += 22
        return image

    def _draw_active_alerts(
        self,
        image: np.ndarray,
        anomalies: list[Anomaly],
        now: float,
    ) -> None:
        if not anomalies:
            return

        active = [anomaly for anomaly in anomalies if anomaly.status != "resolved"]
        if active and self._should_flash(now):
            cv2.rectangle(image, (0, 0), (image.shape[1], 48), (0, 0, 220), -1)
            cv2.putText(
                image,
                f"LIVE ALERT  active={len(active)}",
                (18, 33),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        panel_x = max(10, image.shape[1] - 360)
        panel_y = 60
        for index, anomaly in enumerate(anomalies[:5]):
            risk = self.config.risk_score_for(anomaly.event_type)
            color = (0, 0, 255) if anomaly.status != "resolved" else (120, 120, 120)
            box = anomaly.bounding_box
            cv2.rectangle(image, (box.x, box.y), (box.x2, box.y2), color, 3)
            cv2.putText(
                image,
                f"{anomaly.event_type.value} risk:{risk}",
                (box.x, max(18, box.y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )

            top = panel_y + index * 142
            cv2.rectangle(image, (panel_x, top), (image.shape[1] - 10, top + 128), (30, 30, 30), -1)
            cv2.rectangle(image, (panel_x, top), (image.shape[1] - 10, top + 128), color, 2)
            lines = [
                "[LIVE ALERT]" if anomaly.status != "resolved" else "[RESOLVED]",
                anomaly.event_type.value,
                f"Track: #{anomaly.tracking_id or 'camera'}",
                f"Zone: {anomaly.zone}",
                f"Confidence: {anomaly.confidence:.2f}  Risk: {risk}",
                f"Time: {time.strftime('%H:%M:%S', time.localtime(anomaly.timestamp or now))}",
            ]
            text_y = top + 20
            for line in lines:
                cv2.putText(
                    image,
                    line,
                    (panel_x + 8, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.46,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                text_y += 19

    def _should_flash(self, now: float) -> bool:
        period = self.config.debug.flash_period_seconds
        return int(now / period) % 2 == 0
