"""Domain models for the Sentinel AI engine.

This module exists as the stable import surface for backend-facing and
pipeline-facing data contracts. The concrete implementations live in utils.py
to preserve backward compatibility with the existing code.
"""

from ai.utils import (
    AlertBoundingBox,
    AlertEvent,
    Anomaly,
    Detection,
    MotionResult,
    TrackedObject,
)


TrackedPerson = TrackedObject


__all__ = [
    "AlertBoundingBox",
    "AlertEvent",
    "Anomaly",
    "Detection",
    "MotionResult",
    "TrackedObject",
    "TrackedPerson",
]
