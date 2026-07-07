"""Evaluate a YOLO model on classroom sample images and save predictions."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from ai.config import MODELS_DIR, PROJECT_ROOT


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def prepare_eval_environment() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(MODELS_DIR))
    os.environ.setdefault("MPLCONFIGDIR", str(MODELS_DIR / "matplotlib"))
    os.environ.setdefault("TORCH_HOME", str(MODELS_DIR / "torch"))
    os.environ.setdefault("ULTRALYTICS_SKIP_REQUIREMENTS_CHECKS", "1")


def evaluate_images(model_path: Path, source_dir: Path, output_dir: Path, confidence: float) -> None:
    """Run YOLO prediction on a folder of images."""

    prepare_eval_environment()
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Install ai/requirements.txt before evaluation.") from exc

    images = sorted(path for path in source_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
    if not images:
        raise RuntimeError(f"No images found in {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(model_path))
    class_counts: dict[str, int] = {}
    for image_path in images:
        results = model.predict(
            str(image_path),
            conf=confidence,
            save=True,
            project=str(output_dir),
            name="predictions",
            exist_ok=True,
            verbose=False,
        )
        for result in results:
            names = result.names
            for box in result.boxes:
                class_name = str(names[int(box.cls[0].item())])
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

    print(f"Evaluated {len(images)} image(s). Annotated outputs: {output_dir / 'predictions'}")
    print("Detected class counts:")
    for class_name, count in sorted(class_counts.items()):
        print(f"  {class_name}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate YOLO on classroom sample images.")
    parser.add_argument(
        "--model",
        type=Path,
        default=MODELS_DIR / "yolo11n.pt",
        help="YOLO checkpoint to evaluate.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "exam_hall" / "images" / "sample",
        help="Folder containing sample images.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "runs" / "eval",
        help="Folder for annotated outputs.",
    )
    parser.add_argument("--conf", type=float, default=0.55)
    args = parser.parse_args()
    evaluate_images(args.model, args.source, args.output, args.conf)


if __name__ == "__main__":
    main()

