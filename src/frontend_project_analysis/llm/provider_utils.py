"""Shared helpers for provider-specific LLM adapters."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ..core.config import Settings
from ..core.errors import ConfigurationError, ProviderResponseError
from ..schemas import ProviderAuditPayload


def require_provider_credentials(settings: Settings) -> None:
    if not settings.llm_model:
        raise ConfigurationError("FPA_LLM_MODEL is required for provider execution.")
    if not settings.llm_api_key:
        raise ConfigurationError("FPA_LLM_API_KEY is required for provider execution.")


def normalize_endpoint(base_url: str, api_path: str) -> str:
    normalized_base = base_url.rstrip("/")
    normalized_path = api_path if api_path.startswith("/") else f"/{api_path}"
    return f"{normalized_base}{normalized_path}"


def openai_base_url(settings: Settings, default_base_url: str | None = None) -> str:
    return settings.llm_base_url or default_base_url or "https://api.openai.com/v1"


def anthropic_base_url(settings: Settings) -> str:
    return settings.llm_base_url or "https://api.anthropic.com"


def gemini_base_url(settings: Settings) -> str:
    return settings.llm_base_url or "https://generativelanguage.googleapis.com/v1beta"


def anthropic_api_path(settings: Settings) -> str:
    if settings.llm_api_path not in {"", "/responses"}:
        return settings.llm_api_path
    return "/v1/messages"


def gemini_api_path(settings: Settings) -> str:
    return (
        settings.llm_api_path
        if settings.llm_api_path not in {"", "/responses"}
        else f"/models/{settings.llm_model}:generateContent"
    )


def openai_api_path(settings: Settings) -> str:
    if settings.llm_api_path.startswith("/"):
        return settings.llm_api_path
    return f"/{settings.llm_api_path}"


def validate_response_envelope(
    response_model: type[BaseModel],
    raw_response: dict[str, Any],
    provider_name: str,
    audit: ProviderAuditPayload,
    message: str,
) -> None:
    try:
        response_model.model_validate(raw_response)
    except Exception as exc:  # pragma: no cover - provider specific envelopes
        audit.error_code = ProviderResponseError.error_code
        raise ProviderResponseError(
            message,
            audit_payload={**audit.model_dump(), "response_json": raw_response},
            provider_name=provider_name,
        ) from exc
