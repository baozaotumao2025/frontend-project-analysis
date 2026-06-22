from __future__ import annotations

import json
from pathlib import Path

from frontend_project_analysis.llm.types import ProviderResponse
from frontend_project_analysis.schemas import ProviderAuditPayload, SubmissionIntentPayload
from tests.cli_support import invoke_with_root


def _fake_submission_router(packet: dict, settings) -> ProviderResponse:
    assert packet["llm_isolation"]["mode"] == "fresh_submission_router_context"
    assert packet["llm_isolation"]["fork_context"] is False
    assert packet["llm_isolation"]["required"] is True
    user_message = packet.get("user_message", "").lower()
    if "publish" in user_message:
        intent = "maintainer_publish"
        summary = "Mock routing resolved the request as maintainer publish."
        suggested_action = "Proceed with maintainer publish flow."
    elif "submit" in user_message or "提交" in user_message:
        intent = "downstream_submit"
        summary = "Mock routing resolved the request as downstream submit."
        suggested_action = "Proceed with downstream submit flow."
    else:
        intent = "ambiguous"
        summary = "Mock routing resolved the request as ambiguous."
        suggested_action = "Ask a clarifying question about the target repository."
    payload = SubmissionIntentPayload(
        intent=intent,
        confidence="high" if intent != "ambiguous" else "medium",
        summary=summary,
        reviewer_ref="mock:mock",
        model="mock-model",
        suggested_action=suggested_action,
    )
    audit = ProviderAuditPayload(
        trace_id="trace",
        request_id="request",
        provider_name="mock",
        endpoint="mock://submission-intent",
        call_status="mocked",
        attempt_count=1,
        duration_ms=0,
        request_json={"packet": True},
    )
    return ProviderResponse(payload=payload, raw_response={"provider": "mock"}, audit=audit)


def test_submit_command_routes_to_maintainer_publish(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    monkeypatch.setenv("FPA_LLM_MODEL", "mock-model")
    monkeypatch.setattr("frontend_project_analysis.commands.submit.run_submission_intent", _fake_submission_router)

    result = invoke_with_root(tmp_path, ["submit", "Please publish the skill repository"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["command"] == "submit"
    assert payload["intent"] == "maintainer_publish"
    assert payload["suggested_action"] == "Proceed with maintainer publish flow."


def test_submit_command_routes_to_downstream_submit(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    monkeypatch.setenv("FPA_LLM_MODEL", "mock-model")
    monkeypatch.setattr("frontend_project_analysis.commands.submit.run_submission_intent", _fake_submission_router)

    result = invoke_with_root(tmp_path, ["submit", "帮我提交当前生成物"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["command"] == "submit"
    assert payload["intent"] == "downstream_submit"
    assert payload["suggested_action"] == "Proceed with downstream submit flow."


def test_submit_command_rejects_ambiguous_request(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    monkeypatch.setenv("FPA_LLM_MODEL", "mock-model")
    monkeypatch.setattr("frontend_project_analysis.commands.submit.run_submission_intent", _fake_submission_router)

    result = invoke_with_root(tmp_path, ["submit", "请帮我处理一下"])

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["intent"] == "ambiguous"
    assert payload["suggested_action"] == "Ask a clarifying question about the target repository."
