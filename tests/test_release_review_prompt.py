from __future__ import annotations

from frontend_project_analysis.core.prompts import (
    build_release_review_packet_manifest,
    build_release_review_reviewer_card,
    build_release_review_prompt,
)


def test_release_review_packet_manifest_includes_isolation_contract() -> None:
    packet = {
        "repository_context": {"branch": "main"},
        "changed_surface": ["README.md"],
        "prompt_rules": ["Return JSON only."],
        "audit_focus": ["release parity"],
    }

    manifest = build_release_review_packet_manifest(packet)

    assert manifest["review_kind"] == "release"
    assert manifest["packet_only"] is True
    assert manifest["fresh_session_required"] is True
    assert manifest["review_isolation"]["mode"] == "fresh_release_reviewer_context"
    assert manifest["review_isolation"]["fork_context"] is False
    assert manifest["review_isolation"]["required"] is True


def test_release_review_reviewer_card_mentions_isolation_contract() -> None:
    packet = build_release_review_packet_manifest(
        {
            "repository_context": {"branch": "main"},
            "changed_surface": ["README.md"],
            "prompt_rules": ["Return JSON only."],
            "audit_focus": ["release parity"],
        }
    )

    card = build_release_review_reviewer_card(packet)
    prompt = build_release_review_prompt(
        {
            "repository_context": {"branch": "main"},
            "changed_surface": ["README.md"],
            "prompt_rules": ["Return JSON only."],
            "audit_focus": ["release parity"],
        }
    )

    assert "fresh reviewer session" in card
    assert '"mode": "fresh_release_reviewer_context"' in card
    assert "fresh-session isolation" in prompt
