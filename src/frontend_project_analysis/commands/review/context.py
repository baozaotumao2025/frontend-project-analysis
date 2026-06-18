"""Shared helpers for review commands."""

from __future__ import annotations

from ...core.config import Settings


def build_semantic_review_llm_context(settings: Settings) -> dict[str, object]:
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
    }


def is_host_review_mode(settings: Settings) -> bool:
    return (settings.llm_provider or "host").strip().lower() == "host"
