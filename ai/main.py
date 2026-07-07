"""Runnable Sentinel AI engine entry point."""

from __future__ import annotations

import logging
import signal
import sys
import time

from ai.alert import AlertDispatcher
from ai.anomalies import AnomalyDetector
from ai.config import SETTINGS
from ai.detector import ObjectDetector
from ai.evidence import EvidenceManager
from ai.motion import MotionAnalyzer
from ai.tracker import MultiObjectTracker
from ai.utils import AlertEvent
from ai.webcam import WebcamStream
from ai.zones import ZoneManager


def configure_logging() -> None:
    SETTINGS.logging.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = SETTINGS.logging.log_dir / SETTINGS.logging.file_name
    logging.basicConfig(
        level=getattr(logging, SETTINGS.logging.level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def run() -> None:
    """Run the real-time detection loop until interrupted."""

    configure_logging()
    logger = logging.getLogger(__name__)
    stop_requested = False

    def request_stop(signum: int, frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True
        logger.info("Shutdown requested by signal %s", signum)

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    detector = ObjectDetector(SETTINGS.model)
    logger.info("Loading detector model=%s", SETTINGS.model.primary_model)
    detector.load()

    tracker = MultiObjectTracker()
    motion = MotionAnalyzer(SETTINGS.motion)
    zones = ZoneManager(SETTINGS)
    anomaly_detector = AnomalyDetector(SETTINGS, zones)
    evidence = EvidenceManager(SETTINGS)
    alerts = AlertDispatcher(SETTINGS.alert).start()
    webcam = WebcamStream(SETTINGS.camera).start()

    logger.info("Sentinel AI started for camera_id=%s", SETTINGS.camera.camera_id)
    try:
        while not stop_requested:
            packet = webcam.read()
            if packet is None:
                time.sleep(0.02)
                continue

            detections = detector.detect(packet.frame)
            active_tracks = tracker.update(detections, packet.timestamp)
            motion_result = motion.analyze(packet.frame)
            anomalies = anomaly_detector.detect(
                frame=packet.frame,
                detections=detections,
                active_tracks=active_tracks,
                missing_tracks=tracker.missing_tracks(),
                motion=motion_result,
                timestamp=packet.timestamp,
            )

            for anomaly in anomalies:
                screenshot = evidence.capture(packet.frame, anomaly)
                event = AlertEvent.from_anomaly(
                    anomaly,
                    camera_id=SETTINGS.camera.camera_id,
                    risk_score=SETTINGS.risk_score_for(anomaly.event_type),
                    screenshot=screenshot,
                )
                alerts.submit(event)
                logger.info(
                    "Alert generated: event_type=%s tracking_id=%s fps=%.1f",
                    event.event_type,
                    event.tracking_id,
                    packet.fps,
                )
    finally:
        webcam.stop()
        alerts.stop()
        logger.info("Sentinel AI stopped")


if __name__ == "__main__":
    run()
