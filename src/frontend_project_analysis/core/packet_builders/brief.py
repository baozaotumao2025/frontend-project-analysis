"""Brief assistant packet builder."""

from __future__ import annotations

from ..contracts import build_isolation_contract


def build_brief_assistant_packet(
    answers: dict[str, str],
    transcript: list[tuple[str, str]],
    remaining_budget: int,
    *,
    stage: str,
) -> dict[str, object]:
    return {
        "stage": stage,
        "answers": answers,
        "transcript": transcript,
        "remaining_budget": remaining_budget,
        "llm_isolation": build_isolation_contract("fresh_brief_assistant_context"),
    }
