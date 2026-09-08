from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from llm_observability_sdk import config
from llm_observability_sdk.integrations.openai import instrument_openai


class FakeTransport:
    def __init__(self) -> None:
        self.events = []

    def enqueue(self, event) -> None:
        self.events.append(event)


@dataclass
class FakeUsage:
    prompt_tokens: int
    completion_tokens: int


@dataclass
class FakeMessage:
    content: str


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    model: str
    choices: list
    usage: FakeUsage


class FakeCompletions:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception
        self.received_kwargs = None

    def create(self, **kwargs):
        self.received_kwargs = kwargs
        if self._exception is not None:
            raise self._exception
        return self._response


class FakeChat:
    def __init__(self, completions: FakeCompletions):
        self.completions = completions


class FakeOpenAIClient:
    def __init__(self, completions: FakeCompletions):
        self.chat = FakeChat(completions)


@pytest.fixture()
def fake_transport():
    transport = FakeTransport()
    config.init(transport=transport)
    return transport


def test_traces_successful_completion(fake_transport):
    response = FakeCompletion(
        model="gpt-4o",
        choices=[FakeChoice(message=FakeMessage(content="hi there"))],
        usage=FakeUsage(prompt_tokens=10, completion_tokens=5),
    )
    client = instrument_openai(FakeOpenAIClient(FakeCompletions(response=response)))

    result = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "hello"}]
    )

    assert result is response
    assert len(fake_transport.events) == 1
    event = fake_transport.events[0]
    assert event.provider == "openai"
    assert event.model == "gpt-4o"
    assert event.completion == "hi there"
    assert event.prompt_tokens == 10
    assert event.completion_tokens == 5
    assert event.status == "success"
    assert "user: hello" in event.prompt


def test_traces_and_reraises_on_error(fake_transport):
    client = instrument_openai(
        FakeOpenAIClient(FakeCompletions(exception=ValueError("rate limited")))
    )

    with pytest.raises(ValueError, match="rate limited"):
        client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])

    assert len(fake_transport.events) == 1
    event = fake_transport.events[0]
    assert event.status == "error"
    assert event.error_message == "rate limited"


def test_does_not_mutate_call_arguments(fake_transport):
    response = FakeCompletion(
        model="gpt-4o", choices=[FakeChoice(message=FakeMessage(content="ok"))], usage=FakeUsage(1, 1)
    )
    completions = FakeCompletions(response=response)
    client = instrument_openai(FakeOpenAIClient(completions))

    client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}], temperature=0.2)

    assert completions.received_kwargs["temperature"] == 0.2
