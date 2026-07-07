"""Screenshot capture and evidence file management."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from ai.config import AppConfig, SETTINGS
from ai.utils import Anomaly, TrackedObject, evidence_timestamp


class EvidenceManager:
    """Capture annotated screenshots for anomalies."""

    def __init__(self, config: AppConfig = SETTINGS) -> None:
        self.config = config
        self.config.evidence.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def capture(
        self,
        frame: np.ndarray,
        anomaly: Anomaly,
        tracks: list[TrackedObject] | None = None,
    ) -> str:
        image = frame.copy()
        if self.config.evidence.draw_annotations:
            self._draw_anomaly(image, anomaly, tracks or [])

        file_path = self._build_path(anomaly)
        params: list[int] = []
        if self.config.evidence.image_format in {"jpg", "jpeg"}:
            params = [cv2.IMWRITE_JPEG_QUALITY, self.config.evidence.jpeg_quality]
        ok = cv2.imwrite(str(file_path), image, params)
        if not ok:
            raise RuntimeError(f"Failed to write screenshot: {file_path}")
        self._prune_old_screenshots()
        return str(file_path)

    def _build_path(self, anomaly: Anomaly) -> Path:
        safe_tracking_id = anomaly.tracking_id.replace(",", "-") if anomaly.tracking_id else "camera"
        filename = (
            f"{anomaly.event_type.value}_{evidence_timestamp()}_"
            f"{safe_tracking_id}.{self.config.evidence.image_format}"
        )
        return self.config.evidence.screenshot_dir / filename

    def _draw_anomaly(
        self,
        image: np.ndarray,
        anomaly: Anomaly,
        tracks: list[TrackedObject],
    ) -> None:
        timestamp = evidence_timestamp()
        for track in tracks:
            box = track.bbox
            cv2.rectangle(image, (box.x, box.y), (box.x2, box.y2), (0, 180, 255), 1)
            cv2.putText(
                image,
                f"ID {track.tracking_id} {track.zone}",
                (box.x, max(16, box.y - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 180, 255),
                1,
                cv2.LINE_AA,
            )

        box = anomaly.bounding_box
        color = (0, 0, 255)
        cv2.rectangle(image, (box.x, box.y), (box.x2, box.y2), color, 2)
        label = (
            f"{anomaly.event_type.value} ID:{anomaly.tracking_id or 'camera'} "
            f"conf:{anomaly.confidence:.2f} zone:{anomaly.zone}"
        )
        cv2.putText(
            image,
            label,
            (box.x, max(20, box.y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            timestamp,
            (12, image.shape[0] - 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    def _prune_old_screenshots(self) -> None:
        max_files = self.config.evidence.max_retained_screenshots
        screenshot_dir = self.config.evidence.screenshot_dir
        files = sorted(
            (
                path
                for path in screenshot_dir.iterdir()
                if path.is_file() and path.suffix.lower().lstrip(".") in {"jpg", "jpeg", "png"}
            ),
            key=lambda path: path.stat().st_mtime,
        )
        excess = len(files) - max_files
        if excess <= 0:
            return
        for path in files[:excess]:
            try:
                path.unlink()
            except OSError:
                continue

