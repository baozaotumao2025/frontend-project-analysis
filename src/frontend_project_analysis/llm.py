"""LLM provider facade for semantic review."""

from __future__ import annotations

from .config import Settings, require_llm_settings
from .errors import ConfigurationError
from .llm_anthropic import run_anthropic_review
from .llm_common import ProviderResponse, run_mock_review
from .llm_gemini import run_gemini_review
from .llm_openai import run_openai_compatible_review, run_openai_review


def run_semantic_review(packet: dict, settings: Settings | None = None) -> ProviderResponse:
    resolved = require_llm_settings(settings)
    provider = resolved.llm_provider.strip().lower()
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
