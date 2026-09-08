from __future__ import annotations

from dataclasses import dataclass

import pytest

from llm_observability_sdk import config
from llm_observability_sdk.integrations.anthropic import instrument_anthropic


class FakeTransport:
    def __init__(self) -> None:
        self.events = []

    def enqueue(self, event) -> None:
        self.events.append(event)


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeTextBlock:
    text: str


@dataclass
class FakeMessage:
    model: str
    content: list
    usage: FakeUsage


class FakeMessages:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception

    def create(self, **kwargs):
        if self._exception is not None:
            raise self._exception
        return self._response


class FakeAnthropicClient:
    def __init__(self, messages: FakeMessages):
        self.messages = messages


@pytest.fixture()
def fake_transport():
    transport = FakeTransport()
    config.init(transport=transport)
    return transport


def test_traces_successful_message(fake_transport):
    response = FakeMessage(
        model="claude-sonnet-5",
        content=[FakeTextBlock(text="hi there")],
        usage=FakeUsage(input_tokens=10, output_tokens=5),
    )
    client = instrument_anthropic(FakeAnthropicClient(FakeMessages(response=response)))

    result = client.messages.create(
        model="claude-sonnet-5", max_tokens=1024, messages=[{"role": "user", "content": "hello"}]
    )

    assert result is response
    event = fake_transport.events[0]
    assert event.provider == "anthropic"
    assert event.model == "claude-sonnet-5"
    assert event.completion == "hi there"
    assert event.prompt_tokens == 10
    assert event.completion_tokens == 5
    assert event.cost == (10 / 1000) * 0.002 + (5 / 1000) * 0.010


def test_traces_and_reraises_on_error(fake_transport):
    client = instrument_anthropic(
        FakeAnthropicClient(FakeMessages(exception=RuntimeError("overloaded")))
    )

    with pytest.raises(RuntimeError, match="overloaded"):
        client.messages.create(model="claude-sonnet-5", max_tokens=1024, messages=[{"role": "user", "content": "hi"}])

    event = fake_transport.events[0]
    assert event.status == "error"
    assert event.error_message == "overloaded"
