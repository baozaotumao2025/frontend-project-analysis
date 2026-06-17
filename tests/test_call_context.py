from frontend_project_analysis.llm import _resolve_call_ids
from frontend_project_analysis.logging_utils import call_context, request_id_var, trace_id_var


def test_resolve_call_ids_prefers_packet_values() -> None:
    trace_id, request_id = _resolve_call_ids(
        {"trace_id": "trace-123", "request_id": "request-456"}
    )

    assert trace_id == "trace-123"
    assert request_id == "request-456"


def test_resolve_call_ids_generates_values() -> None:
    trace_id, request_id = _resolve_call_ids({})

    assert trace_id
    assert request_id
    assert trace_id != request_id


def test_call_context_sets_and_resets_ids() -> None:
    before_trace = trace_id_var.get()
    before_request = request_id_var.get()

    with call_context("trace-x", "request-y"):
        assert trace_id_var.get() == "trace-x"
        assert request_id_var.get() == "request-y"

    assert trace_id_var.get() == before_trace
    assert request_id_var.get() == before_request
