"""Train a custom YOLO model for classroom invigilation objects."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from ai.config import MODELS_DIR, PROJECT_ROOT


def prepare_training_environment() -> None:
    """Keep third-party runtime files inside the project workspace."""

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(MODELS_DIR))
    os.environ.setdefault("MPLCONFIGDIR", str(MODELS_DIR / "matplotlib"))
    os.environ.setdefault("TORCH_HOME", str(MODELS_DIR / "torch"))
    os.environ.setdefault("ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS", "1")


def train_model(
    *,
    data: Path,
    model: str,
    epochs: int,
    image_size: int,
    batch: int,
    device: str,
    project: Path,
    name: str,
) -> Path:
    """Train YOLO and copy the best checkpoint into ai/models."""

    prepare_training_environment()
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Install ai/requirements.txt before training.") from exc

    yolo = YOLO(model)
    results = yolo.train(
        data=str(data),
        epochs=epochs,
        imgsz=image_size,
        batch=batch,
        device=None if device == "auto" else device,
        project=str(project),
        name=name,
        exist_ok=True,
    )
    save_dir = Path(results.save_dir)
    best_path = save_dir / "weights" / "best.pt"
    target_path = MODELS_DIR / "exam_hall_best.pt"
    if best_path.exists():
        target_path.write_bytes(best_path.read_bytes())
    return target_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a custom Sentinel AI YOLO model.")
    parser.add_argument(
        "--data",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "exam_hall" / "data.yaml",
        help="YOLO dataset YAML path.",
    )
    parser.add_argument(
        "--model",
        default=str(MODELS_DIR / "yolo11n.pt"),
        help="Base YOLO checkpoint.",
    )
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--project", type=Path, default=PROJECT_ROOT / "runs" / "train")
    parser.add_argument("--name", default="exam_hall_yolo")
    args = parser.parse_args()

    output = train_model(
        data=args.data,
        model=args.model,
        epochs=args.epochs,
        image_size=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
    )
    print(f"Best model copied to: {output}")


if __name__ == "__main__":
    main()

