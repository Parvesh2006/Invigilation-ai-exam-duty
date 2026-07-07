"""Central logging setup for Sentinel AI."""

from __future__ import annotations

import logging
import sys

from ai.config import SETTINGS, LoggingConfig


def configure_logging(config: LoggingConfig = SETTINGS.logging) -> None:
    """Configure console and file logging once."""

    config.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = config.log_dir / config.file_name
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(getattr(logging, config.level.upper(), logging.INFO))
        return

    logging.basicConfig(
        level=getattr(logging, config.level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
