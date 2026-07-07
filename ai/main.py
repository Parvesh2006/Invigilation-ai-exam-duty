"""Runnable Sentinel AI engine entry point."""

from __future__ import annotations

import signal
import time

import cv2

from ai.alert import AlertDispatcher
from ai.anomalies import AnomalyDetector
from ai.config import SETTINGS
from ai.debug import DebugOverlay
from ai.detector import ObjectDetector
from ai.evidence import EvidenceManager
from ai.intelligence import ExaminationIntelligenceEngine
from ai.logger import configure_logging, get_logger
from ai.motion import MotionAnalyzer
from ai.tracker import MultiObjectTracker
from ai.utils import AlertEvent
from ai.webcam import WebcamStream
from ai.zones import ZoneManager


def run() -> None:
    """Run the real-time detection loop until interrupted."""

    configure_logging()
    logger = get_logger(__name__)
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
    debug_overlay = DebugOverlay(SETTINGS, zones)
    anomaly_detector = AnomalyDetector(SETTINGS, zones)
    intelligence = ExaminationIntelligenceEngine()
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
            zones.update_track_zones(active_tracks)
            motion_result = motion.analyze(packet.frame)
            intelligence.update_scene(
                tracks=active_tracks,
                zones=list(zones.zones),
                fps=packet.fps,
                camera_connected=True,
                yolo_running=True,
                backend_connected=SETTINGS.alert.send_alerts,
            )
            anomalies = anomaly_detector.detect(
                frame=packet.frame,
                detections=detections,
                active_tracks=active_tracks,
                missing_tracks=tracker.missing_tracks(),
                motion=motion_result,
                timestamp=packet.timestamp,
            )

            for anomaly in anomalies:
                screenshot = evidence.capture(packet.frame, anomaly, active_tracks)
                event = AlertEvent.from_anomaly(
                    anomaly,
                    camera_id=SETTINGS.camera.camera_id,
                    risk_score=SETTINGS.risk_score_for(anomaly.event_type),
                    screenshot=screenshot,
                )
                intelligence.ingest_alert(event.model_dump())
                alerts.submit(event)
                logger.info(
                    "Alert generated: event_type=%s tracking_id=%s fps=%.1f",
                    event.event_type,
                    event.tracking_id,
                    packet.fps,
                )

            if SETTINGS.debug.enabled or SETTINGS.debug.show_window:
                visible_anomalies = anomaly_detector.active_anomalies(packet.timestamp)
                debug_frame = debug_overlay.draw(
                    packet.frame,
                    detections=detections,
                    tracks=active_tracks,
                    motion=motion_result,
                    anomalies=visible_anomalies,
                    fps=packet.fps,
                )
                if SETTINGS.debug.show_window:
                    cv2.imshow(SETTINGS.debug.window_name, debug_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        stop_requested = True
    finally:
        webcam.stop()
        alerts.stop()
        if SETTINGS.debug.show_window:
            cv2.destroyAllWindows()
        logger.info("Sentinel AI stopped")


if __name__ == "__main__":
    run()
