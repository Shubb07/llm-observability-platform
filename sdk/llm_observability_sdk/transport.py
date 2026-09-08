from __future__ import annotations

import atexit
import queue
import threading
import time

import requests

from llm_observability_sdk.models import TraceEvent

DEFAULT_FLUSH_INTERVAL_SECONDS = 2.0
DEFAULT_BATCH_SIZE = 20
DEFAULT_MAX_RETRIES = 3

# Sentinel pushed onto the queue by shutdown() to wake a worker that's
# blocked waiting up to flush_interval_seconds for the next event — without
# it, shutdown() would have to wait out the full flush interval before it
# could even notice the stop request.
_SHUTDOWN_SENTINEL = object()


class BackgroundTransport:
    """Buffers trace events and flushes them to the backend on a background
    thread, so `enqueue()` never blocks the caller's application thread.

    Failures (network errors, 5xx) are retried with exponential backoff up to
    `max_retries`, then dropped — per the PRD's "degrade gracefully" principle,
    an unreachable backend must never raise into the instrumented application.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        flush_interval_seconds: float = DEFAULT_FLUSH_INTERVAL_SECONDS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        session: requests.Session | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._flush_interval_seconds = flush_interval_seconds
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._session = session or requests.Session()

        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._run, daemon=True, name="llmobs-flush")
        self._worker.start()
        atexit.register(self.shutdown)

    def enqueue(self, event: TraceEvent) -> None:
        self._queue.put(event)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            batch = self._collect_batch(timeout=self._flush_interval_seconds)
            if batch:
                self._send(batch)

        # Stop was requested — drain whatever is left before the thread exits.
        while True:
            batch = self._collect_batch(timeout=0)
            if not batch:
                break
            self._send(batch)

    def _collect_batch(self, timeout: float) -> list[TraceEvent]:
        batch: list[TraceEvent] = []
        try:
            first = self._queue.get(timeout=timeout)
        except queue.Empty:
            return batch
        if first is not _SHUTDOWN_SENTINEL:
            batch.append(first)

        while len(batch) < self._batch_size:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if item is _SHUTDOWN_SENTINEL:
                break
            batch.append(item)
        return batch

    def _send(self, batch: list[TraceEvent]) -> None:
        payload = {"traces": [event.to_dict() for event in batch]}
        backoff_seconds = 0.5

        for attempt in range(self._max_retries + 1):
            try:
                response = self._session.post(
                    f"{self._base_url}/api/v1/traces",
                    json=payload,
                    headers={"X-API-Key": self._api_key},
                    timeout=5,
                )
                # A 4xx means the backend rejected the batch (bad key, bad
                # payload) — retrying won't help, so treat it as delivered.
                if response.status_code < 500:
                    return
            except requests.RequestException:
                pass

            if attempt < self._max_retries:
                time.sleep(backoff_seconds)
                backoff_seconds *= 2

    def shutdown(self) -> None:
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        self._queue.put(_SHUTDOWN_SENTINEL)
        self._worker.join(timeout=self._flush_interval_seconds + 5)
