from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Union


EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def save_screenshot(content: Union[bytes, bytearray], filename: str | None = None) -> str:
    """Save screenshot bytes to the evidence folder for later review."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{timestamp}.jpg"

    file_path = EVIDENCE_DIR / filename
    file_path.write_bytes(bytes(content))
    return str(file_path)


def evidence_folder() -> str:
    return str(EVIDENCE_DIR)
