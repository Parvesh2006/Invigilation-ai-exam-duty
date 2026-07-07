"""Threaded webcam capture with FPS tracking and reconnect support."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np

from ai.config import CameraConfig, SETTINGS


@dataclass(slots=True)
class FramePacket:
    """Latest camera frame plus capture metadata."""

    frame: np.ndarray
    timestamp: float
    fps: float
    frame_index: int


class FPSCounter:
    """Rolling FPS counter updated by the capture thread."""

    def __init__(self, window_seconds: float = 1.0) -> None:
        self.window_seconds = window_seconds
        self._timestamps: list[float] = []

    def tick(self, now: float | None = None) -> float:
        current = time.time() if now is None else now
        self._timestamps.append(current)
        cutoff = current - self.window_seconds
        self._timestamps = [stamp for stamp in self._timestamps if stamp >= cutoff]
        if len(self._timestamps) < 2:
            return 0.0
        elapsed = self._timestamps[-1] - self._timestamps[0]
        return 0.0 if elapsed <= 0 else (len(self._timestamps) - 1) / elapsed


class WebcamStream:
    """Continuously reads frames in a background thread.

    Consumers call read() to get the newest frame without blocking the AI loop
    on camera I/O.
    """

    def __init__(self, config: CameraConfig = SETTINGS.camera) -> None:
        self.config = config
        self._capture: cv2.VideoCapture | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._latest: FramePacket | None = None
        self._frame_index = 0
        self._fps = FPSCounter()

    def start(self) -> WebcamStream:
        self._stop_event.clear()
        self._open_capture()
        self._thread = threading.Thread(target=self._capture_loop, name="webcam-capture", daemon=True)
        self._thread.start()
        return self

    def read(self) -> FramePacket | None:
        with self._lock:
            if self._latest is None:
                return None
            return FramePacket(
                frame=self._latest.frame.copy(),
                timestamp=self._latest.timestamp,
                fps=self._latest.fps,
                frame_index=self._latest.frame_index,
            )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._release_capture()

    def _open_capture(self) -> None:
        self._release_capture()
        self._capture = cv2.VideoCapture(self.config.device_index)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
        self._capture.set(cv2.CAP_PROP_FPS, self.config.target_fps)

    def _release_capture(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _capture_loop(self) -> None:
        last_good_read = time.time()
        while not self._stop_event.is_set():
            if self._capture is None or not self._capture.isOpened():
                time.sleep(self.config.reconnect_delay_seconds)
                self._open_capture()
                continue

            ok, frame = self._capture.read()
            now = time.time()
            if not ok or frame is None:
                if now - last_good_read >= self.config.read_timeout_seconds:
                    self._open_capture()
                    last_good_read = now
                time.sleep(0.02)
                continue

            last_good_read = now
            if self.config.mirror_frame:
                frame = cv2.flip(frame, 1)
            self._frame_index += 1
            packet = FramePacket(
                frame=frame,
                timestamp=now,
                fps=self._fps.tick(now),
                frame_index=self._frame_index,
            )
            with self._lock:
                self._latest = packet

    def __enter__(self) -> WebcamStream:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.stop()

