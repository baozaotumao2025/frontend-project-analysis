"""LLM brief assistant integration."""

from __future__ import annotations

from ..core.config import Settings
from ..core.contracts import assert_isolation_contract
from ..core.errors import ConfigurationError, ProviderValidationError
from ..core.prompts import (
    build_brief_assistant_system_prompt,
    build_brief_assistant_user_prompt,
)
from ..schemas import (
    AnthropicReviewResponse,
    BriefAssistantPayload,
    GeminiReviewResponse,
    OpenAIReviewResponse,
    ProviderAttemptPayload,
    ProviderAuditEventPayload,
    ProviderAuditPayload,
)
from .payloads import resolve_call_ids
from .provider_utils import (
    anthropic_api_path,
    anthropic_base_url,
    gemini_api_path,
    gemini_base_url,
    normalize_endpoint,
    openai_api_path,
    openai_base_url,
    require_provider_credentials,
)
from .providers.common import run_structured_provider
from .structured import (
    build_anthropic_structured_request,
    build_gemini_structured_request,
    build_openai_structured_request,
)
from .types import ProviderResponse
from .validation import extract_anthropic_text, extract_gemini_text, extract_output_text

BRIEF_ASSISTANT_SCHEMA = {
    "name": "brief_assistant_result",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "stage",
            "summary",
            "reviewer_ref",
            "model",
            "can_finalize",
            "confidence",
            "gaps",
            "recommended_questions",
            "draft_brief",
        ],
        "properties": {
            "stage": {"type": "string", "enum": ["followup", "summary"]},
            "summary": {"type": "string"},
            "reviewer_ref": {"type": "string"},
            "model": {"type": ["string", "null"]},
            "can_finalize": {"type": "boolean"},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "gaps": {"type": "array", "items": {"type": "string"}},
            "recommended_questions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "draft_brief": {"type": ["string", "null"]},
        },
    },
    "strict": True,
}


def validate_brief_assistant_content(
    content: str,
    settings: Settings,
    provider_name: str,
    audit: ProviderAuditPayload,
) -> BriefAssistantPayload:
    try:
        parsed = BriefAssistantPayload.model_validate_json(content)
    except Exception as exc:  # pragma: no cover - depends on provider output
        audit.events.append(
            ProviderAuditEventPayload(
                event_type="brief_payload_validation_failed",
                message="Brief assistant payload JSON validation failed.",
                offset_ms=audit.duration_ms,
                data={"provider": provider_name},
            )
        )
        raise ProviderValidationError(
            "Provider returned invalid brief assistant JSON.",
            audit_payload=audit.model_dump(),
            provider_name=provider_name,
        ) from exc

    if not parsed.model:
        parsed.model = settings.llm_model
    if not parsed.reviewer_ref:
        parsed.reviewer_ref = provider_name
    audit.events.append(
        ProviderAuditEventPayload(
            event_type="brief_payload_validated",
            message="Brief assistant payload validated successfully.",
            offset_ms=audit.duration_ms,
            data={"provider": provider_name},
        )
    )
    return parsed


def run_brief_assistant(
    packet: dict,
    settings: Settings,
    *,
    stage: str = "followup",
) -> ProviderResponse:
    assert_isolation_contract(
        packet,
        key="llm_isolation",
        mode="fresh_brief_assistant_context",
        label="Brief assistant",
    )
    provider = (settings.llm_provider or "host").strip().lower()
    if provider == "host":
        raise ConfigurationError(
            "Host mode does not execute the brief assistant. "
            "Use an external provider or mock for LLM-assisted brief collection."
        )

    system_prompt = build_brief_assistant_system_prompt(stage=stage)
    user_prompt = build_brief_assistant_user_prompt(packet, stage=stage)
    if provider == "openai":
        return _run_openai_brief_assistant(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
            stage=stage,
        )
    if provider in {"openai-compatible", "openai_compatible"}:
        return _run_openai_compatible_brief_assistant(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
            stage=stage,
        )
    if provider == "anthropic":
        return _run_anthropic_brief_assistant(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
            stage=stage,
        )
    if provider in {"gemini", "google", "google-gemini"}:
        return _run_gemini_brief_assistant(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
            stage=stage,
        )
    if provider == "mock":
        return _run_mock_brief_assistant(packet, settings, stage=stage)
    raise ConfigurationError(f"Unsupported FPA_LLM_PROVIDER '{settings.llm_provider}'.")


def _run_openai_brief_assistant(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
    stage: str,
) -> ProviderResponse:
    require_provider_credentials(settings)
    endpoint = normalize_endpoint(
        settings.llm_base_url or openai_base_url(settings) or "https://api.openai.com/v1",
        openai_api_path(settings),
    )
    trace_id, request_id = resolve_call_ids(packet)
    body = build_openai_structured_request(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_name=BRIEF_ASSISTANT_SCHEMA["name"],
        schema=BRIEF_ASSISTANT_SCHEMA["schema"],
        strict=BRIEF_ASSISTANT_SCHEMA["strict"],
    )
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    if settings.llm_organization:
        headers["OpenAI-Organization"] = settings.llm_organization
    return run_structured_provider(
        provider_name=settings.llm_provider,
        endpoint=endpoint,
        request_json=body,
        headers=headers,
        settings=settings,
        trace_id=trace_id,
        request_id=request_id,
        response_model=OpenAIReviewResponse,
        response_message="OpenAI response did not match the expected schema.",
        extract_text=extract_output_text,
        parse_payload=validate_brief_assistant_content,
    )


def _run_openai_compatible_brief_assistant(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
    stage: str,
) -> ProviderResponse:
    require_provider_credentials(settings)
    endpoint = normalize_endpoint(
        settings.llm_base_url or "https://api.openai.com/v1",
        openai_api_path(settings),
    )
    trace_id, request_id = resolve_call_ids(packet)
    body = build_openai_structured_request(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_name=BRIEF_ASSISTANT_SCHEMA["name"],
        schema=BRIEF_ASSISTANT_SCHEMA["schema"],
        strict=BRIEF_ASSISTANT_SCHEMA["strict"],
    )
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    if settings.llm_organization:
        headers["OpenAI-Organization"] = settings.llm_organization
    return run_structured_provider(
        provider_name=settings.llm_provider,
        endpoint=endpoint,
        request_json=body,
        headers=headers,
        settings=settings,
        trace_id=trace_id,
        request_id=request_id,
        response_model=OpenAIReviewResponse,
        response_message="OpenAI response did not match the expected schema.",
        extract_text=extract_output_text,
        parse_payload=validate_brief_assistant_content,
    )


def _run_anthropic_brief_assistant(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
    stage: str,
) -> ProviderResponse:
    require_provider_credentials(settings)
    endpoint = normalize_endpoint(anthropic_base_url(settings), anthropic_api_path(settings))
    trace_id, request_id = resolve_call_ids(packet)
    body = build_anthropic_structured_request(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": settings.anthropic_version,
        "Content-Type": "application/json",
    }
    return run_structured_provider(
        provider_name="anthropic",
        endpoint=endpoint,
        request_json=body,
        headers=headers,
        settings=settings,
        trace_id=trace_id,
        request_id=request_id,
        response_model=AnthropicReviewResponse,
        response_message="Anthropic response did not match the expected schema.",
        extract_text=extract_anthropic_text,
        parse_payload=validate_brief_assistant_content,
    )


def _run_gemini_brief_assistant(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
    stage: str,
) -> ProviderResponse:
    require_provider_credentials(settings)
    endpoint = normalize_endpoint(gemini_base_url(settings), gemini_api_path(settings))
    trace_id, request_id = resolve_call_ids(packet)
    body = build_gemini_structured_request(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    headers = {
        "x-goog-api-key": settings.llm_api_key,
        "Content-Type": "application/json",
    }
    return run_structured_provider(
        provider_name="gemini",
        endpoint=endpoint,
        request_json=body,
        headers=headers,
        settings=settings,
        trace_id=trace_id,
        request_id=request_id,
        response_model=GeminiReviewResponse,
        response_message="Gemini response did not match the expected schema.",
        extract_text=extract_gemini_text,
        parse_payload=validate_brief_assistant_content,
    )


def _run_mock_brief_assistant(packet: dict, settings: Settings, *, stage: str) -> ProviderResponse:
    trace_id, request_id = resolve_call_ids(packet)
    payload = BriefAssistantPayload(
        stage=stage,  # type: ignore[arg-type]
        summary="Mock brief assistant response.",
        reviewer_ref=f"{settings.llm_provider}:mock",
        model=settings.llm_model or "mock-model",
        can_finalize=False,
        confidence="medium",
        gaps=["Mock assistant does not analyze the brief."],
        recommended_questions=[
            "What is the primary business outcome the brief should support?"
        ],
        draft_brief="Mock brief assistant draft.",
    )
    audit = ProviderAuditPayload(
        trace_id=trace_id,
        request_id=request_id,
        provider_name="mock",
        endpoint="mock://brief-assistant",
        call_status="mocked",
        attempt_count=1,
        duration_ms=0,
        request_json={"stage": stage},
        response_json={"provider": "mock", "payload": payload.model_dump()},
        attempts=[ProviderAttemptPayload(attempt_no=1, status="mocked", duration_ms=0)],
        events=[],
    )
    return ProviderResponse(payload=payload, raw_response={"provider": "mock"}, audit=audit)
