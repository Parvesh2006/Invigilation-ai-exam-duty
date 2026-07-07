"""Camera zone calibration helper.

Run this to save one webcam frame with the configured zones drawn on top. Use
the image to tune SENTINEL_ZONES_JSON in your .env file.
"""

from __future__ import annotations

import json
import time

import cv2

from ai.config import SETTINGS
from ai.utils import evidence_timestamp
from ai.webcam import WebcamStream
from ai.zones import ZoneManager


def capture_zone_reference(wait_seconds: float = 2.0) -> str:
    """Capture and save a zone overlay image from the live camera."""

    zone_manager = ZoneManager(SETTINGS)
    output_path = SETTINGS.evidence.screenshot_dir / f"CALIBRATION_ZONES_{evidence_timestamp()}.jpg"

    with WebcamStream(SETTINGS.camera) as webcam:
        deadline = time.time() + wait_seconds
        packet = None
        while time.time() < deadline:
            packet = webcam.read()
            if packet is not None:
                time.sleep(0.1)
            else:
                time.sleep(0.02)

        if packet is None:
            raise RuntimeError("Unable to capture a webcam frame for calibration.")

        annotated = zone_manager.draw_zones(packet.frame)
        cv2.imwrite(str(output_path), annotated)
    return str(output_path)


def current_zones_json() -> str:
    """Return current zones as JSON suitable for SENTINEL_ZONES_JSON."""

    return json.dumps(
        [zone.model_dump(mode="json") for zone in SETTINGS.zones],
        indent=2,
    )


def main() -> None:
    path = capture_zone_reference()
    print(f"Saved calibration image: {path}")
    print("Current SENTINEL_ZONES_JSON:")
    print(current_zones_json())


if __name__ == "__main__":
    main()
