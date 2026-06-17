"""Prompt builders for semantic review."""

from __future__ import annotations

import json

SEMANTIC_REVIEW_SYSTEM_PROMPT = """You are a strict product analysis reviewer.

Review the provided artifact packet and return only JSON that matches the supplied schema.

Focus on semantic quality, not syntax:
- Persona: role boundaries, real goals, permission realism
- Story Map: business-valid sequence, goal orientation, no UI leakage
- Page: surface boundaries, path coverage, shared-surface correctness
- Feature: business independence, delivery boundary clarity, coupling quality
- GWT: scenario completeness and business-facing wording
- Feature Spec: implementation boundary clarity and dependency honesty

Use `passed` only when the artifact is semantically strong enough to move forward.
Use `needs_revision` when the artifact is promising but needs edits.
Use `failed` only when the artifact is fundamentally wrong or unusable.
"""


def build_semantic_review_user_prompt(packet: dict) -> str:
    return (
        "Review this artifact packet and produce a semantic review result.\n\n"
        "Return JSON only.\n\n"
        f"{json.dumps(packet, indent=2, ensure_ascii=True)}"
    )
