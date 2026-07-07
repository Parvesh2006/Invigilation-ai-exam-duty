"""Collect classroom webcam frames for custom YOLO labeling."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2

from ai.config import SETTINGS
from ai.utils import evidence_timestamp
from ai.webcam import WebcamStream


def collect_frames(output_dir: Path, count: int, interval_seconds: float) -> None:
    """Save frames from the configured webcam for later annotation."""

    output_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    last_saved_at = 0.0
    with WebcamStream(SETTINGS.camera) as webcam:
        while saved < count:
            packet = webcam.read()
            if packet is None:
                time.sleep(0.02)
                continue

            now = time.time()
            if now - last_saved_at < interval_seconds:
                time.sleep(0.02)
                continue

            path = output_dir / f"frame_{evidence_timestamp()}_{saved:04d}.jpg"
            cv2.imwrite(str(path), packet.frame)
            saved += 1
            last_saved_at = now
            print(f"Saved {saved}/{count}: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect webcam frames for YOLO labeling.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ai/datasets/exam_hall/images/raw"),
        help="Directory where raw frames will be saved.",
    )
    parser.add_argument("--count", type=int, default=100, help="Number of frames to save.")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between saved frames.",
    )
    args = parser.parse_args()
    collect_frames(args.output, args.count, args.interval)


if __name__ == "__main__":
    main()

