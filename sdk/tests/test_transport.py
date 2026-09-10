from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from llm_observability_sdk.models import TraceEvent
from llm_observability_sdk.transport import BackgroundTransport


@dataclass
class FakeResponse:
    status_code: int = 200


@dataclass
class FakeSession:
    """Records every POST and replays a scripted sequence of responses/errors."""

    responses: list[FakeResponse | Exception] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def post(self, url, json, headers, timeout):
        with self._lock:
            self.calls.append({"url": url, "json": json, "headers": headers})
            if self.responses:
                outcome = self.responses.pop(0)
            else:
                outcome = FakeResponse(200)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_event(model: str = "gpt-4o") -> TraceEvent:
    return TraceEvent(model=model, provider="openai", prompt="hi", latency_ms=10.0)


def wait_until(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_enqueue_flushes_to_ingestion_endpoint():
    session = FakeSession()
    transport = BackgroundTransport(
        api_key="test-key", base_url="http://localhost:8000", session=session, flush_interval_seconds=0.1
    )
    transport.enqueue(make_event())

    assert wait_until(lambda: len(session.calls) == 1)
    call = session.calls[0]
    assert call["url"] == "http://localhost:8000/api/v1/traces"
    assert call["headers"]["X-API-Key"] == "test-key"
    assert call["json"]["traces"][0]["model"] == "gpt-4o"

    transport.shutdown()


def test_batches_multiple_events_into_one_request():
    session = FakeSession()
    transport = BackgroundTransport(
        api_key="k", base_url="http://localhost:8000", session=session, flush_interval_seconds=0.2, batch_size=10
    )
    for _ in range(5):
        transport.enqueue(make_event())

    assert wait_until(lambda: len(session.calls) >= 1)
    time.sleep(0.3)  # let a possible second flush happen so we can assert there wasn't one
    assert len(session.calls) == 1
    assert len(session.calls[0]["json"]["traces"]) == 5

    transport.shutdown()


def test_retries_on_server_error_then_succeeds():
    session = FakeSession(responses=[FakeResponse(500), FakeResponse(200)])
    transport = BackgroundTransport(
        api_key="k", base_url="http://localhost:8000", session=session, flush_interval_seconds=0.1, max_retries=3
    )
    transport.enqueue(make_event())

    assert wait_until(lambda: len(session.calls) == 2, timeout=5.0)
    transport.shutdown()


def test_retry_resends_the_same_client_trace_id():
    # The backend dedups on client_trace_id, so a retry only prevents a
    # duplicate trace if it's the *same* id both times - not a freshly
    # generated one per HTTP attempt.
    session = FakeSession(responses=[FakeResponse(500), FakeResponse(200)])
    transport = BackgroundTransport(
        api_key="k", base_url="http://localhost:8000", session=session, flush_interval_seconds=0.1, max_retries=3
    )
    transport.enqueue(make_event())

    assert wait_until(lambda: len(session.calls) == 2, timeout=5.0)
    first_id = session.calls[0]["json"]["traces"][0]["client_trace_id"]
    second_id = session.calls[1]["json"]["traces"][0]["client_trace_id"]
    assert first_id == second_id

    transport.shutdown()


def test_does_not_retry_client_error():
    session = FakeSession(responses=[FakeResponse(401)])
    transport = BackgroundTransport(
        api_key="bad-key", base_url="http://localhost:8000", session=session, flush_interval_seconds=0.1
    )
    transport.enqueue(make_event())

    assert wait_until(lambda: len(session.calls) == 1)
    time.sleep(0.3)
    assert len(session.calls) == 1  # no retry attempted for a 4xx

    transport.shutdown()


def test_shutdown_drains_pending_events():
    session = FakeSession()
    transport = BackgroundTransport(
        api_key="k", base_url="http://localhost:8000", session=session, flush_interval_seconds=5.0
    )
    transport.enqueue(make_event())
    transport.shutdown()  # should not wait out the 5s flush interval to send

    assert len(session.calls) == 1
