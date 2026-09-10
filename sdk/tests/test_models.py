from llm_observability_sdk.models import TraceEvent


def make_event() -> TraceEvent:
    return TraceEvent(model="gpt-4o", provider="openai", prompt="hi", latency_ms=10.0)


def test_each_event_gets_a_unique_client_trace_id():
    a = make_event()
    b = make_event()
    assert a.client_trace_id != b.client_trace_id


def test_client_trace_id_is_stable_across_to_dict_calls():
    event = make_event()
    assert event.to_dict()["client_trace_id"] == event.client_trace_id
    assert event.to_dict()["client_trace_id"] == event.to_dict()["client_trace_id"]
