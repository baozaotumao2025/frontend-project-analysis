"""Gemini semantic review adapter."""

from __future__ import annotations

from .config import Settings
from .errors import ConfigurationError, ProviderResponseError
from .llm_common import (
    ProviderResponse,
    build_gemini_request,
    extract_gemini_text,
    post_json,
    resolve_call_ids,
    validate_provider_payload,
)


def run_gemini_review(packet: dict, settings: Settings) -> ProviderResponse:
    if not settings.llm_model:
        raise ConfigurationError("FPA_LLM_MODEL is required for provider execution.")
    if not settings.llm_api_key:
        raise ConfigurationError("FPA_LLM_API_KEY is required for provider execution.")

    base_url = (settings.llm_base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip(
        "/"
    )
    api_path = (
        settings.llm_api_path
        if settings.llm_api_path not in {"", "/responses"}
        else f"/models/{settings.llm_model}:generateContent"
    )
    if not api_path.startswith("/"):
        api_path = f"/{api_path}"
    endpoint = f"{base_url}{api_path}"
    trace_id, request_id = resolve_call_ids(packet)
    body = build_gemini_request(settings, packet)
    headers = {
        "x-goog-api-key": settings.llm_api_key,
        "Content-Type": "application/json",
    }
    raw_response, audit = post_json(
        provider_name="gemini",
        endpoint=endpoint,
        request_json=body,
        headers=headers,
        settings=settings,
        trace_id=trace_id,
        request_id=request_id,
    )
    try:
        from .schemas import GeminiReviewResponse

        GeminiReviewResponse.model_validate(raw_response)
    except Exception as exc:
        audit.error_code = ProviderResponseError.error_code
        raise ProviderResponseError(
            "Gemini response did not match the expected schema.",
            audit_payload={**audit.model_dump(), "response_json": raw_response},
            provider_name="gemini",
        ) from exc
    content = extract_gemini_text(raw_response)
    parsed = validate_provider_payload(
        content,
        settings,
        provider_name="gemini",
        audit=audit,
    )
    audit.response_json = raw_response
    audit.model_name = parsed.model
    audit.call_status = "completed"
    return ProviderResponse(payload=parsed, raw_response=raw_response, audit=audit)
