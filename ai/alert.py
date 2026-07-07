"""Asynchronous JSON alert delivery to the backend."""

from __future__ import annotations

import json
import logging
import queue
import threading
import time

import requests

from ai.config import AlertConfig, SETTINGS
from ai.utils import AlertEvent


logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Queues and sends JSON alerts without blocking video processing."""

    def __init__(self, config: AlertConfig = SETTINGS.alert) -> None:
        self.config = config
        self._queue: queue.Queue[AlertEvent] = queue.Queue(maxsize=config.queue_max_size)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> AlertDispatcher:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, name="alert-dispatcher", daemon=True)
        self._thread.start()
        return self

    def submit(self, event: AlertEvent) -> bool:
        try:
            self._queue.put_nowait(event)
            return True
        except queue.Full:
            logger.warning("Alert queue full; dropping event %s", event.event_id)
            return False

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

    def send_now(self, event: AlertEvent) -> bool:
        """Send one event immediately; useful for tests and CLI smoke checks."""

        payload = event.model_dump()
        if not self.config.send_alerts:
            logger.info("Alert sending disabled. Event: %s", json.dumps(payload))
            return True

        for attempt in range(self.config.max_retries + 1):
            try:
                response = requests.post(
                    self.config.backend_url,
                    json=payload,
                    timeout=self.config.request_timeout_seconds,
                )
                if 200 <= response.status_code < 300:
                    logger.info("Alert delivered: %s", event.event_id)
                    return True
                logger.warning(
                    "Backend returned HTTP %s for event %s",
                    response.status_code,
                    event.event_id,
                )
            except requests.RequestException as exc:
                logger.warning("Alert delivery failed for %s: %s", event.event_id, exc)

            if attempt < self.config.max_retries:
                time.sleep(self.config.retry_backoff_seconds * (attempt + 1))
        return False

    def _worker(self) -> None:
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                event = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.send_now(event)
            finally:
                self._queue.task_done()

    def __enter__(self) -> AlertDispatcher:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.stop()

