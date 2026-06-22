from __future__ import annotations

from frontend_project_analysis.core.config import Settings
from frontend_project_analysis.core.packets import (
    build_brief_assistant_packet,
    build_review_llm_context,
    build_submission_packet,
)


def test_build_review_llm_context_attaches_isolation_contract() -> None:
    settings = Settings.model_construct(llm_provider="mock", llm_model="mock-model")

    context = build_review_llm_context(settings)

    assert context["provider"] == "mock"
    assert context["review_isolation"]["mode"] == "fresh_reviewer_subagent"
    assert context["review_isolation"]["fork_context"] is False
    assert context["review_isolation"]["required"] is True


def test_build_brief_assistant_packet_attaches_isolation_contract() -> None:
    packet = build_brief_assistant_packet(
        {"what": "Manage customer assignments."},
        [("1/3 What does the product do?", "Manage customer assignments.")],
        2,
        stage="summary",
    )

    assert packet["stage"] == "summary"
    assert packet["llm_isolation"]["mode"] == "fresh_brief_assistant_context"
    assert packet["llm_isolation"]["fork_context"] is False
    assert packet["llm_isolation"]["required"] is True


def test_build_submission_packet_attaches_isolation_contract() -> None:
    packet = build_submission_packet(
        "Please submit the current generated project",
        repository_context={"project": "crm-web"},
        available_actions=["downstream_submit"],
        routing_rules=["Return JSON only."],
    )

    assert packet["user_message"].startswith("Please submit")
    assert packet["repository_context"]["project"] == "crm-web"
    assert packet["available_actions"] == ["downstream_submit"]
    assert packet["routing_rules"] == ["Return JSON only."]
    assert packet["llm_isolation"]["mode"] == "fresh_submission_router_context"
    assert packet["llm_isolation"]["fork_context"] is False
    assert packet["llm_isolation"]["required"] is True
