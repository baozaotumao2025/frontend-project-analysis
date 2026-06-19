"""LLM provider facade for brief assistance and review workflows."""

from __future__ import annotations

from ..core.config import Settings, require_llm_settings
from ..core.errors import ConfigurationError
from .brief import run_brief_assistant
from .payloads import run_mock_review
from .providers.anthropic import run_anthropic_review
from .providers.gemini import run_gemini_review
from .providers.openai import run_openai_compatible_review, run_openai_review
from .types import ProviderResponse

__all__ = [
    "run_brief_assistant",
    "run_mock_review",
    "run_semantic_review",
]


def run_semantic_review(packet: dict, settings: Settings | None = None) -> ProviderResponse:
    resolved = require_llm_settings(settings)
    provider = (resolved.llm_provider or "host").strip().lower()
    if provider == "host":
        raise ConfigurationError(
            "Host review mode does not call an external LLM. "
            "Use `fpa review semantic-packet` or `fpa review semantic-run` to hand the packet "
            "to Codex or Claude Code, then record the result with `fpa review semantic-record`."
        )
    if provider == "openai":
        return run_openai_review(packet, resolved)
    if provider in {"openai-compatible", "openai_compatible"}:
        return run_openai_compatible_review(packet, resolved)
    if provider == "anthropic":
        return run_anthropic_review(packet, resolved)
    if provider in {"gemini", "google", "google-gemini"}:
        return run_gemini_review(packet, resolved)
    if provider == "mock":
        return run_mock_review(packet, resolved)
    raise ConfigurationError(f"Unsupported FPA_LLM_PROVIDER '{resolved.llm_provider}'.")
