"""OpenAI-compatible semantic review adapter."""

from __future__ import annotations

from .config import Settings
from .errors import ConfigurationError, ProviderResponseError
from .llm_common import (
    ProviderResponse,
    build_openai_request,
    extract_output_text,
    post_json,
    resolve_call_ids,
    validate_provider_payload,
)


def run_openai_review(packet: dict, settings: Settings) -> ProviderResponse:
    base_url = settings.llm_base_url or "https://api.openai.com/v1"
    return run_openai_compatible_review(packet, settings, default_base_url=base_url)


def run_openai_compatible_review(
    packet: dict,
    settings: Settings,
    default_base_url: str | None = None,
) -> ProviderResponse:
    if not settings.llm_model:
        raise ConfigurationError("FPA_LLM_MODEL is required for provider execution.")
    if not settings.llm_api_key:
        raise ConfigurationError("FPA_LLM_API_KEY is required for provider execution.")

    base_url = (settings.llm_base_url or default_base_url or "https://api.openai.com/v1").rstrip(
        "/"
    )
    api_path = (
        settings.llm_api_path
        if settings.llm_api_path.startswith("/")
        else f"/{settings.llm_api_path}"
    )
    endpoint = f"{base_url}{api_path}"
    trace_id, request_id = resolve_call_ids(packet)
    body = build_openai_request(settings, packet)
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    if settings.llm_organization:
        headers["OpenAI-Organization"] = settings.llm_organization

    raw_response, audit = post_json(
        provider_name=settings.llm_provider,
        endpoint=endpoint,
        request_json=body,
        headers=headers,
        settings=settings,
        trace_id=trace_id,
        request_id=request_id,
    )
    try:
        from .schemas import OpenAIReviewResponse

        OpenAIReviewResponse.model_validate(raw_response)
    except Exception as exc:
        audit.error_code = ProviderResponseError.error_code
        raise ProviderResponseError(
            "OpenAI response did not match the expected schema.",
            audit_payload={**audit.model_dump(), "response_json": raw_response},
            provider_name=settings.llm_provider,
        ) from exc
    content = extract_output_text(raw_response)
    parsed = validate_provider_payload(
        content,
        settings,
        provider_name=settings.llm_provider,
        audit=audit,
    )
    audit.response_json = raw_response
    audit.model_name = parsed.model
    audit.call_status = "completed"
    return ProviderResponse(payload=parsed, raw_response=raw_response, audit=audit)
