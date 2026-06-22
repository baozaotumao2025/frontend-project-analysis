from __future__ import annotations

from frontend_project_analysis.core.config import Settings
from frontend_project_analysis.core.packet_specs import PACKET_SPECS
from frontend_project_analysis.core.packet_registry import (
    PACKET_REGISTRY,
    get_packet_spec,
    list_packet_specs,
)
from frontend_project_analysis.core.packets import (
    build_brief_assistant_packet,
    build_review_llm_context,
    build_submission_packet,
)
from frontend_project_analysis.core.prompts import build_release_review_packet_manifest


def test_packet_registry_lists_expected_specs() -> None:
    names = {spec.name for spec in list_packet_specs()}

    assert names == {
        "brief_assistant",
        "release_review",
        "review_llm_context",
        "submission_router",
    }
    assert get_packet_spec("brief_assistant") is PACKET_REGISTRY["brief_assistant"]
    assert set(PACKET_SPECS) == names


def test_packet_registry_validates_expected_builders() -> None:
    review_spec = get_packet_spec("review_llm_context")
    review_packet = build_review_llm_context(
        Settings.model_construct(llm_provider="mock", llm_model="mock-model")
    )
    review_spec.validate(review_packet)

    brief_spec = get_packet_spec("brief_assistant")
    brief_packet = build_brief_assistant_packet(
        {"what": "Manage customer assignments."},
        [("1/3 What does the product do?", "Manage customer assignments.")],
        1,
        stage="followup",
    )
    brief_spec.validate(brief_packet)

    submission_spec = get_packet_spec("submission_router")
    submission_packet = build_submission_packet(
        "Please submit the current generated project",
        repository_context={"project": "crm-web"},
        available_actions=["downstream_submit"],
        routing_rules=["Return JSON only."],
    )
    submission_spec.validate(submission_packet)

    release_spec = get_packet_spec("release_review")
    release_packet = build_release_review_packet_manifest(
        {
            "repository_context": {"branch": "main"},
            "changed_surface": ["README.md"],
            "prompt_rules": ["Return JSON only."],
            "audit_focus": ["release parity"],
        }
    )
    release_spec.validate(release_packet)
