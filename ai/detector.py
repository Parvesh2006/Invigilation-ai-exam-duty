"""YOLO object detection wrapper for Sentinel AI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from ai.config import ModelConfig, SETTINGS
from ai.utils import Detection, bbox_from_xyxy


class ObjectDetector:
    """Runs YOLO detection and normalizes outputs for downstream modules."""

    def __init__(self, config: ModelConfig = SETTINGS.model) -> None:
        self.config = config
        self._model: Any | None = None
        self._class_ids: list[int] | None = None

    def load(self) -> None:
        """Load the primary YOLO model, falling back to YOLOv8n when needed."""

        if self._model is not None:
            return

        self._prepare_ultralytics_environment()
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is required for detection. Install ai/requirements.txt first."
            ) from exc

        model_candidates = (
            self._resolve_model_path(self.config.primary_model),
            self._resolve_model_path(self.config.fallback_model),
        )
        last_error: Exception | None = None
        for model_path in model_candidates:
            try:
                self._model = YOLO(str(model_path))
                self._class_ids = self._resolve_class_ids()
                return
            except Exception as exc:  # pragma: no cover - depends on local model/runtime
                last_error = exc
        raise RuntimeError("Unable to load YOLO primary or fallback model.") from last_error

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Detect configured classes in one frame."""

        self.load()
        assert self._model is not None

        kwargs: dict[str, Any] = {
            "conf": self.config.confidence_threshold,
            "iou": self.config.iou_threshold,
            "imgsz": self.config.image_size,
            "verbose": False,
        }
        if self._class_ids:
            kwargs["classes"] = self._class_ids
        if self.config.device != "auto":
            kwargs["device"] = self.config.device

        results = self._model.predict(frame, **kwargs)
        if not results:
            return []
        return self._parse_result(results[0])

    def _resolve_model_path(self, model_name: str) -> Path | str:
        local_path = self.config.model_dir / model_name
        if model_name.endswith(".pt") and not Path(model_name).is_absolute():
            return local_path
        return local_path if local_path.exists() else model_name

    def _prepare_ultralytics_environment(self) -> None:
        """Keep Ultralytics runtime files inside the project workspace."""

        self.config.model_dir.mkdir(parents=True, exist_ok=True)
        matplotlib_dir = self.config.model_dir / "matplotlib"
        torch_dir = self.config.model_dir / "torch"
        matplotlib_dir.mkdir(parents=True, exist_ok=True)
        torch_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("YOLO_CONFIG_DIR", str(self.config.model_dir))
        os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_dir))
        os.environ.setdefault("TORCH_HOME", str(torch_dir))
        os.environ.setdefault("ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS", "1")

    def _resolve_class_ids(self) -> list[int] | None:
        assert self._model is not None
        names = getattr(self._model, "names", None)
        if not isinstance(names, dict):
            return None
        wanted = {self._normalize_class_name(name) for name in self.config.classes}
        return [
            int(class_id)
            for class_id, name in names.items()
            if self._normalize_class_name(str(name)) in wanted
        ]

    def _parse_result(self, result: Any) -> list[Detection]:
        boxes = getattr(result, "boxes", None)
        names = getattr(result, "names", None) or getattr(self._model, "names", {})
        if boxes is None:
            return []

        detections: list[Detection] = []
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())
            class_name = str(names.get(class_id, class_id))
            canonical_name = self._canonical_class_name(class_name)
            if canonical_name is None:
                continue
            confidence = float(box.conf[0].item())
            min_confidence = self.config.class_confidence_thresholds.get(
                canonical_name,
                self.config.confidence_threshold,
            )
            if confidence < min_confidence:
                continue
            track_id = None
            if getattr(box, "id", None) is not None:
                track_id = int(box.id[0].item())
            detections.append(
                Detection(
                    class_name=canonical_name,
                    confidence=confidence,
                    bbox=bbox_from_xyxy(*xyxy),
                    tracking_id=track_id,
                )
            )
        return detections

    def _canonical_class_name(self, class_name: str) -> str | None:
        normalized = self._normalize_class_name(class_name)
        for configured_name in self.config.classes:
            if self._normalize_class_name(configured_name) == normalized:
                return configured_name
        return None

    @staticmethod
    def _normalize_class_name(class_name: str) -> str:
        return class_name.lower().replace("_", " ").replace("-", " ").strip()
