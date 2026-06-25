import pytest

from frontend_project_analysis.core.config import Settings
from frontend_project_analysis.core.errors import ConfigurationError
from frontend_project_analysis.llm import run_brief_assistant, run_semantic_review
from frontend_project_analysis.llm.transport.errors import (
    error_code_for_http_message,
    error_for_http_failure,
)
from frontend_project_analysis.llm.transport.retry import (
    should_retry_http,
    sleep_backoff,
)


def test_llm_facade_exposes_router() -> None:
    assert run_semantic_review.__name__ == "run_semantic_review"


def test_llm_package_exposes_transport_helpers() -> None:
    assert error_code_for_http_message("HTTP 429") is not None
    assert callable(error_for_http_failure)
    assert callable(should_retry_http)
    assert callable(sleep_backoff)


def test_host_semantic_review_is_blocked_from_direct_llm_execution() -> None:
    settings = Settings(llm_provider="host", llm_model="mock-model")

    with pytest.raises(ConfigurationError, match="fresh reviewer sub-agent"):
        run_semantic_review(
            {
                "artifact": {"ref": "feature:alpha-feature"},
                "review_isolation": {
                    "mode": "fresh_reviewer_subagent",
                    "fork_context": False,
                    "required": True,
                },
            },
            settings,
        )


def test_semantic_review_requires_isolation_contract() -> None:
    settings = Settings(llm_provider="mock", llm_model="mock-model")

    with pytest.raises(ConfigurationError, match="fresh reviewer sub-agent contract"):
        run_semantic_review({"artifact": {"ref": "feature:alpha-feature"}}, settings)


def test_host_brief_assistant_is_blocked_from_direct_llm_execution() -> None:
    settings = Settings(llm_provider="host")

    with pytest.raises(ConfigurationError, match="Host mode does not execute the brief assistant"):
        run_brief_assistant(
            {
                "transcript": [],
                "answers": {},
                "remaining_budget": 0,
                "llm_isolation": {
                    "mode": "fresh_brief_assistant_context",
                    "fork_context": False,
                    "required": True,
                },
            },
            settings,
        )


def test_brief_assistant_requires_isolation_contract() -> None:
    settings = Settings(llm_provider="mock", llm_model="mock-model")

    with pytest.raises(ConfigurationError, match="fresh isolated context contract"):
        run_brief_assistant({"transcript": [], "answers": {}, "remaining_budget": 0}, settings)
