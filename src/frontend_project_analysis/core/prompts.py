"""Prompt builders for review workflows."""

from __future__ import annotations

import json

from .domain import SEMANTIC_REVIEW_RUBRICS, ArtifactType

_SEMANTIC_REVIEW_BASE_PROMPT = """You are a strict product analysis reviewer.

Review the provided artifact packet and return only JSON that matches the supplied schema.

Use only the packet in this request. Do not rely on prior drafting context or hidden scratch work.
First look for counterexamples and failure cases, then decide whether the artifact can pass.
"""


def _artifact_type_value(artifact_type: ArtifactType | str | None) -> str:
    if artifact_type is None:
        return ""
    if isinstance(artifact_type, ArtifactType):
        return artifact_type.value
    return str(artifact_type).strip()


def _format_rubric_lines(artifact_type: ArtifactType | str | None) -> str:
    value = _artifact_type_value(artifact_type)
    if not value:
        return ""
    try:
        resolved = ArtifactType(value)
    except ValueError:
        return ""
    rubric = SEMANTIC_REVIEW_RUBRICS.get(resolved, [])
    if not rubric:
        return ""
    lines = ["Focus on semantic quality, not syntax:", ""]
    lines.extend(f"- {item}" for item in rubric)
    return "\n".join(lines)


def build_semantic_review_system_prompt(
    artifact_type: ArtifactType | str | None = None,
) -> str:
    rubric = _format_rubric_lines(artifact_type)
    sections = [_SEMANTIC_REVIEW_BASE_PROMPT.rstrip()]
    if rubric:
        sections.append(rubric)
    sections.append(
        "Every finding must include concrete evidence strings taken from the packet.\n"
        "Use `passed` only when you have checked counterexamples, found at least one "
        "evidence-backed reason to trust the artifact, and see no material blocker.\n"
        "Use `needs_revision` when the artifact is promising but needs edits.\n"
        "Use `failed` only when the artifact is fundamentally wrong or unusable."
    )
    return "\n\n".join(sections)


def build_semantic_review_user_prompt(packet: dict) -> str:
    artifact_type = packet.get("artifact", {}).get("type")
    return (
        "Review this artifact packet and produce a semantic review result.\n\n"
        f"Artifact type: {artifact_type or 'unknown'}\n\n"
        "Checklist:\n"
        "1. List counterexamples or failure cases first.\n"
        "2. Cite concrete evidence from the packet for every finding.\n"
        "3. Return `needs_revision` if evidence is missing or too vague.\n\n"
        "Return JSON only.\n\n"
        f"{json.dumps(packet, indent=2, ensure_ascii=True)}"
    )


def build_release_review_prompt(packet: dict) -> str:
    return "\n\n".join(
        [
            build_release_review_system_prompt(),
            build_release_review_user_prompt(packet),
        ]
    )


def build_release_review_system_prompt() -> str:
    return (
        "You are a strict release reviewer.\n\n"
        "Review only the frozen packet in this message. Do not use drafting context.\n"
        "Return JSON only. List counterexamples first and then evidence-backed findings.\n\n"
        "Focus on:\n"
        "- code/document parity\n"
        "- terminology alignment\n"
        "- release readiness\n"
        "- fresh-session isolation\n"
    )


def build_release_review_user_prompt(packet: dict) -> str:
    changed_surface = packet.get("changed_surface", [])
    audit_focus = packet.get("audit_focus", [])
    repository_context = packet.get("repository_context", {})
    prompt_rules = packet.get("prompt_rules", [])
    return (
        "Review this frozen release packet and produce a release review result.\n\n"
        f"Repository context:\n{json.dumps(repository_context, indent=2, ensure_ascii=True)}\n\n"
        "Checklist:\n"
        "- List counterexamples first.\n"
        "- Cite concrete evidence from the packet for every finding.\n"
        "- Use only the packet, not drafting context.\n"
        "- Return JSON only.\n\n"
        f"Prompt rules:\n{json.dumps(prompt_rules, indent=2, ensure_ascii=True)}\n\n"
        f"Changed surface:\n{json.dumps(changed_surface, indent=2, ensure_ascii=True)}\n\n"
        f"Audit focus:\n{json.dumps(audit_focus, indent=2, ensure_ascii=True)}\n"
    )


def build_release_review_packet_manifest(packet: dict) -> dict:
    return {
        "review_kind": "release",
        "fresh_session_required": True,
        "packet_only": True,
        "response_format": "json",
        "findings_order": "counterexamples-first",
        "focus": [
            "code/document parity",
            "terminology alignment",
            "release readiness",
            "fresh-session isolation",
        ],
        "repository_context": packet.get("repository_context", {}),
        "changed_surface_count": len(packet.get("changed_surface", [])),
        "prompt_rules": packet.get("prompt_rules", []),
        "audit_focus": packet.get("audit_focus", []),
    }


def build_release_review_reviewer_card(packet: dict) -> str:
    repository_context = packet.get("repository_context", {})
    changed_surface = packet.get("changed_surface", [])
    prompt_rules = packet.get("prompt_rules", [])
    audit_focus = packet.get("audit_focus", [])
    lines = [
        "# Release Reviewer Card",
        "",
        "Use this card only in a fresh reviewer session.",
        "",
        "## What to do",
        "1. Read only the frozen packet.",
        "2. Do not inspect the drafting conversation or hidden scratch work.",
        "3. Return JSON only.",
        "4. List counterexamples first, then evidence-backed findings.",
        "",
        "## What to review",
        f"- Repository context: `{json.dumps(repository_context, ensure_ascii=True)}`",
        f"- Changed surface count: `{len(changed_surface)}`",
        f"- Audit focus count: `{len(audit_focus)}`",
        "",
        "## Prompt rules",
        *[f"- {rule}" for rule in prompt_rules],
        "",
        "## Audit focus",
        *[f"- {item}" for item in audit_focus],
    ]
    return "\n".join(lines)


def build_brief_assistant_system_prompt(stage: str = "followup") -> str:
    return (
        "You are a careful brief assistant that helps refine a project brief through"
        " Socratic questioning and synthesis.\n\n"
        "Use only the interview transcript and current brief packet.\n"
        "Do not invent facts.\n"
        "Prefer concrete gaps, follow-up questions, and concise synthesis.\n\n"
        "Return JSON only.\n"
        f"Stage: {stage}\n"
        "For followup stage, recommend the most useful next questions.\n"
        "For summary stage, produce a concise brief synthesis and mark "
        "whether the brief can finalize.\n"
    )


def build_brief_assistant_user_prompt(packet: dict, stage: str = "followup") -> str:
    transcript = packet.get("transcript", [])
    answers = packet.get("answers", {})
    budget = packet.get("remaining_budget")
    return (
        "Review the current brief interview packet and produce a brief assistant result.\n\n"
        f"Stage: {stage}\n"
        f"Remaining question budget: {budget}\n\n"
        f"Transcript:\n{json.dumps(transcript, indent=2, ensure_ascii=True)}\n\n"
        f"Current answers:\n{json.dumps(answers, indent=2, ensure_ascii=True)}\n"
    )
