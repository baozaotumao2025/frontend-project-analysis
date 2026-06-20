from __future__ import annotations

from frontend_project_analysis.core.config import Settings
from frontend_project_analysis.core.prompts import (
    build_submission_intent_prompt,
    build_submission_intent_system_prompt,
    build_submission_intent_user_prompt,
)


def test_submission_intent_prompt_uses_default_template() -> None:
    packet = {
        "user_message": "帮我发布 skill 仓库",
        "repository_context": {"branch": "main", "head": "abc123"},
        "available_actions": ["maintainer_publish", "downstream_submit"],
        "routing_rules": ["be conservative", "return JSON only"],
    }

    system_prompt = build_submission_intent_system_prompt(packet)
    user_prompt = build_submission_intent_user_prompt(packet)
    combined = build_submission_intent_prompt(packet)

    assert "strict submission intent router" in system_prompt
    assert "maintainer_publish" in system_prompt
    assert "帮我发布 skill 仓库" in user_prompt
    assert '"branch": "main"' in user_prompt
    assert "be conservative" in user_prompt
    assert system_prompt in combined
    assert user_prompt in combined


def test_submission_intent_prompt_honors_template_overrides() -> None:
    settings = Settings.model_construct(
        submission_intent_system_prompt_template="SYSTEM::{routing_rules}",
        submission_intent_user_prompt_template="USER::{user_message}::{available_actions}",
    )
    packet = {
        "user_message": "Please submit the current generated project",
        "repository_context": {"project": "crm-web"},
        "available_actions": ["downstream_submit"],
        "routing_rules": ["custom-rule"],
    }

    system_prompt = build_submission_intent_system_prompt(packet, settings=settings)
    user_prompt = build_submission_intent_user_prompt(packet, settings=settings)
    combined = build_submission_intent_prompt(packet, settings=settings)

    assert system_prompt.startswith("SYSTEM::")
    assert "custom-rule" in system_prompt
    assert user_prompt.startswith("USER::Please submit the current generated project::")
    assert "downstream_submit" in user_prompt
    assert "custom-rule" in combined
    assert "downstream_submit" in combined
