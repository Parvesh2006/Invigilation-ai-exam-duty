"""Configurable zone utilities for hall regions."""

from __future__ import annotations

import cv2
import numpy as np

from ai.config import AppConfig, BoundingBox, SETTINGS, ZoneConfig, ZoneType
from ai.utils import bbox_center, bbox_intersection, point_in_bbox


class ZoneManager:
    """Query and visualize configured zones."""

    def __init__(self, config: AppConfig = SETTINGS) -> None:
        self.config = config
        self.zones = config.active_zones

    def zones_for_bbox(self, box: BoundingBox) -> list[ZoneConfig]:
        return [zone for zone in self.zones if bbox_intersection(box, zone.box) > 0]

    def intersects(self, box: BoundingBox, zone_type: ZoneType) -> bool:
        return any(bbox_intersection(box, zone.box) > 0 for zone in self.zones_by_type(zone_type))

    def center_inside(self, box: BoundingBox, zone_type: ZoneType) -> bool:
        center = bbox_center(box)
        return any(point_in_bbox(center, zone.box) for zone in self.zones_by_type(zone_type))

    def zones_by_type(self, zone_type: ZoneType) -> tuple[ZoneConfig, ...]:
        return tuple(zone for zone in self.zones if zone.zone_type == zone_type)

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        annotated = frame.copy()
        colors = {
            ZoneType.DOOR: (0, 255, 255),
            ZoneType.INVIGILATOR: (255, 180, 0),
            ZoneType.STUDENT: (0, 200, 0),
            ZoneType.RESTRICTED: (0, 0, 255),
        }
        for zone in self.zones:
            color = colors.get(zone.zone_type, (255, 255, 255))
            box = zone.box
            cv2.rectangle(annotated, (box.x, box.y), (box.x2, box.y2), color, 2)
            cv2.putText(
                annotated,
                zone.name,
                (box.x + 6, max(18, box.y + 18)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )
        return annotated

