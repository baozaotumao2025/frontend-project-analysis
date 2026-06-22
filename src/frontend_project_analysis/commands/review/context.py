"""Shared helpers for review commands."""

from __future__ import annotations

from ...core.config import Settings
from ...core.packets import build_review_llm_context


def build_semantic_review_llm_context(settings: Settings) -> dict[str, object]:
    return build_review_llm_context(settings)


def is_host_review_mode(settings: Settings) -> bool:
    return (settings.llm_provider or "host").strip().lower() == "host"
