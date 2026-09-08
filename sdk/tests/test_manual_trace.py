from __future__ import annotations

import pytest

from llm_observability_sdk import config
from llm_observability_sdk.manual import trace


class FakeTransport:
    def __init__(self) -> None:
        self.events = []

    def enqueue(self, event) -> None:
        self.events.append(event)


@pytest.fixture()
def fake_transport():
    transport = FakeTransport()
    config.init(transport=transport)
    return transport


def test_trace_records_success(fake_transport):
    with trace(model="local-model", provider="custom", prompt="hello") as t:
        t.set_completion("hi there", prompt_tokens=2, completion_tokens=3, cost=0.001)

    assert len(fake_transport.events) == 1
    event = fake_transport.events[0]
    assert event.status == "success"
    assert event.completion == "hi there"
    assert event.prompt_tokens == 2
    assert event.completion_tokens == 3
    assert event.cost == 0.001
    assert event.latency_ms > 0


def test_trace_records_failure_and_reraises(fake_transport):
    with pytest.raises(RuntimeError, match="boom"):
        with trace(model="local-model", provider="custom", prompt="hello"):
            raise RuntimeError("boom")

    assert len(fake_transport.events) == 1
    event = fake_transport.events[0]
    assert event.status == "error"
    assert event.error_message == "boom"


def test_trace_carries_tags_through(fake_transport):
    with trace(model="m", provider="custom", prompt="p", tags={"env": "test"}) as t:
        t.set_completion("c")

    assert fake_transport.events[0].tags == {"env": "test"}


def test_trace_without_init_raises():
    config._transport = None
    with pytest.raises(RuntimeError, match="init"):
        with trace(model="m", provider="custom", prompt="p"):
            pass
