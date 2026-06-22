"""Submission routing packet builder."""

from __future__ import annotations

from ..contracts import build_isolation_contract


def build_submission_packet(
    request: str,
    *,
    repository_context: dict[str, object],
    available_actions: list[str] | None = None,
    routing_rules: list[str] | None = None,
) -> dict[str, object]:
    return {
        "user_message": request,
        "repository_context": repository_context,
        "available_actions": available_actions
        or ["maintainer_publish", "downstream_submit", "ambiguous"],
        "routing_rules": routing_rules
        or [
            "Be conservative when the request is ambiguous.",
            "Return JSON only.",
            "Use repository context to distinguish skill publication from downstream submission.",
        ],
        "llm_isolation": build_isolation_contract("fresh_submission_router_context"),
    }
