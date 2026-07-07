"""OpenCV-based motion and camera-blocking analysis."""

from __future__ import annotations

from collections import deque

import cv2
import numpy as np

from ai.config import MotionConfig, SETTINGS
from ai.utils import MotionResult


class MotionAnalyzer:
    """Analyze frame-to-frame motion, direction, brightness, and occlusion."""

    def __init__(self, config: MotionConfig = SETTINGS.motion) -> None:
        self.config = config
        self._previous_gray: np.ndarray | None = None
        self._centroids: deque[tuple[float, float]] = deque(maxlen=config.direction_window)

    def analyze(self, frame: np.ndarray) -> MotionResult:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        brightness = float(np.mean(gray))
        dark_pixel_ratio = float(np.mean(gray <= self.config.motion_threshold))

        if self._previous_gray is None:
            self._previous_gray = blurred
            return MotionResult(
                has_motion=False,
                intensity=0.0,
                direction="none",
                moving_area=0,
                brightness=brightness,
                dark_pixel_ratio=dark_pixel_ratio,
                camera_blocked=self._is_camera_blocked(brightness, dark_pixel_ratio),
            )

        frame_delta = cv2.absdiff(self._previous_gray, blurred)
        _, threshold = cv2.threshold(
            frame_delta,
            self.config.motion_threshold,
            255,
            cv2.THRESH_BINARY,
        )
        threshold = cv2.dilate(threshold, None, iterations=2)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        moving_area = 0
        weighted_x = 0.0
        weighted_y = 0.0
        for contour in contours:
            area = int(cv2.contourArea(contour))
            if area < self.config.min_motion_area:
                continue
            moving_area += area
            moments = cv2.moments(contour)
            if moments["m00"]:
                weighted_x += (moments["m10"] / moments["m00"]) * area
                weighted_y += (moments["m01"] / moments["m00"]) * area

        has_motion = moving_area >= self.config.min_motion_area
        intensity = float(np.mean(frame_delta))
        direction = "none"
        if has_motion and moving_area > 0:
            self._centroids.append((weighted_x / moving_area, weighted_y / moving_area))
            direction = self._estimate_direction()

        self._previous_gray = blurred
        return MotionResult(
            has_motion=has_motion,
            intensity=intensity,
            direction=direction,
            moving_area=moving_area,
            brightness=brightness,
            dark_pixel_ratio=dark_pixel_ratio,
            camera_blocked=self._is_camera_blocked(brightness, dark_pixel_ratio),
        )

    def _estimate_direction(self) -> str:
        if len(self._centroids) < 2:
            return "none"
        start_x, start_y = self._centroids[0]
        end_x, end_y = self._centroids[-1]
        dx = end_x - start_x
        dy = end_y - start_y
        if abs(dx) < 5 and abs(dy) < 5:
            return "stationary"
        if abs(dx) >= abs(dy):
            return "right" if dx > 0 else "left"
        return "down" if dy > 0 else "up"

    def _is_camera_blocked(self, brightness: float, dark_pixel_ratio: float) -> bool:
        anomalies = SETTINGS.anomalies
        return (
            brightness <= anomalies.camera_blocked_brightness_threshold
            or dark_pixel_ratio >= anomalies.camera_blocked_dark_pixel_ratio
        )

