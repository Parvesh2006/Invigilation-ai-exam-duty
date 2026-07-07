from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Union


BASE_DIR = Path(__file__).resolve().parent
EVIDENCE_DIR = BASE_DIR / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def save_screenshot(content: Union[bytes, bytearray], filename: str | None = None) -> str:
    """Placeholder helper for saving evidence images later."""
    if filename is None:
        filename = f"evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

    file_path = EVIDENCE_DIR / filename
    file_path.write_bytes(bytes(content))
    return str(file_path)


def ensure_evidence_folder() -> str:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    return str(EVIDENCE_DIR)

