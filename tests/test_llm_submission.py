from __future__ import annotations

import pytest

from frontend_project_analysis.core.config import Settings
from frontend_project_analysis.core.errors import ConfigurationError
from frontend_project_analysis.llm import run_submission_intent
from frontend_project_analysis.llm.types import ProviderResponse
from frontend_project_analysis.schemas import SubmissionIntentPayload


def test_llm_facade_exposes_submission_router() -> None:
    assert run_submission_intent.__name__ == "run_submission_intent"


def test_host_submission_routing_is_blocked() -> None:
    settings = Settings(llm_provider="host")

    with pytest.raises(ConfigurationError, match="submission intent router"):
        run_submission_intent({"user_message": "帮我发布 skill 仓库"}, settings)


def test_mock_submission_routing_resolves_downstream_submit() -> None:
    settings = Settings(llm_provider="mock", llm_model="mock-model")
    packet = {
        "user_message": "Please submit the current generated project",
        "repository_context": {"project": "crm-web"},
        "routing_rules": ["be conservative"],
    }

    result = run_submission_intent(packet, settings)

    assert isinstance(result, ProviderResponse)
    assert isinstance(result.payload, SubmissionIntentPayload)
    assert result.payload.intent == "downstream_submit"
    assert result.payload.summary.startswith("Mock routing resolved the request")
    assert result.payload.reviewer_ref == "mock:mock"
    assert result.payload.model == "mock-model"
    assert result.payload.suggested_action == "Proceed with downstream submit flow."
    assert result.audit.provider_name == "mock"
    assert result.audit.endpoint == "mock://submission-intent"

