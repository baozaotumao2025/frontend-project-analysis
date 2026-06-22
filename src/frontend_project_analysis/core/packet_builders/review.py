"""Semantic review packet builder."""

from __future__ import annotations

from ..config import Settings
from ..contracts import build_isolation_contract


def build_review_llm_context(settings: Settings) -> dict[str, object]:
    provider = (settings.llm_provider or "host").strip() or "host"
    return {
        "provider": provider,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "api_path": settings.llm_api_path,
        "max_output_tokens": settings.llm_max_output_tokens,
        "timeout_seconds": settings.llm_timeout_seconds,
        "temperature": settings.llm_temperature,
        "organization": settings.llm_organization,
        "anthropic_version": settings.anthropic_version,
        "review_isolation": build_isolation_contract("fresh_reviewer_subagent"),
    }
