"""LLM submission-intent routing integration."""

from __future__ import annotations

from ..core.config import Settings
from ..core.errors import ConfigurationError, ProviderValidationError
from ..core.prompts import (
    build_submission_intent_system_prompt,
    build_submission_intent_user_prompt,
)
from ..schemas import (
    AnthropicReviewResponse,
    GeminiReviewResponse,
    OpenAIReviewResponse,
    ProviderAttemptPayload,
    ProviderAuditEventPayload,
    ProviderAuditPayload,
    SubmissionIntentPayload,
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
from ..submission_intent import classify_submission_intent
from .types import ProviderResponse
from .validation import extract_anthropic_text, extract_gemini_text, extract_output_text
from .specs import SUBMISSION_INTENT_SCHEMA


def validate_submission_intent_content(
    content: str,
    settings: Settings,
    provider_name: str,
    audit: ProviderAuditPayload,
) -> SubmissionIntentPayload:
    try:
        parsed = SubmissionIntentPayload.model_validate_json(content)
    except Exception as exc:  # pragma: no cover - depends on provider output
        audit.events.append(
            ProviderAuditEventPayload(
                event_type="submission_intent_validation_failed",
                message="Submission intent payload JSON validation failed.",
                offset_ms=audit.duration_ms,
                data={"provider": provider_name},
            )
        )
        audit.error_code = ProviderValidationError.error_code
        raise ProviderValidationError(
            "Provider returned invalid submission intent JSON.",
            audit_payload=audit.model_dump(),
            provider_name=provider_name,
        ) from exc

    if not parsed.model:
        parsed.model = settings.llm_model
    if not parsed.reviewer_ref:
        parsed.reviewer_ref = provider_name
    audit.events.append(
        ProviderAuditEventPayload(
            event_type="submission_intent_validated",
            message="Submission intent payload validated successfully.",
            offset_ms=audit.duration_ms,
            data={"provider": provider_name, "intent": parsed.intent},
        )
    )
    return parsed


def run_submission_intent(packet: dict, settings: Settings) -> ProviderResponse:
    provider = (settings.llm_provider or "host").strip().lower()
    if provider == "host":
        raise ConfigurationError(
            "Host mode does not execute the submission intent router. "
            "Use an external provider or mock for natural-language routing."
        )

    system_prompt = build_submission_intent_system_prompt(packet, settings=settings)
    user_prompt = build_submission_intent_user_prompt(packet, settings=settings)
    if provider == "openai":
        return _run_openai_submission_intent(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
        )
    if provider in {"openai-compatible", "openai_compatible"}:
        return _run_openai_compatible_submission_intent(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
        )
    if provider == "anthropic":
        return _run_anthropic_submission_intent(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
        )
    if provider in {"gemini", "google", "google-gemini"}:
        return _run_gemini_submission_intent(
            settings=settings,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            packet=packet,
        )
    if provider == "mock":
        return _run_mock_submission_intent(packet, settings)
    raise ConfigurationError(f"Unsupported FPA_LLM_PROVIDER '{settings.llm_provider}'.")


def _run_openai_submission_intent(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
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
        schema_name=SUBMISSION_INTENT_SCHEMA["name"],
        schema=SUBMISSION_INTENT_SCHEMA["schema"],
        strict=SUBMISSION_INTENT_SCHEMA["strict"],
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
        parse_payload=validate_submission_intent_content,
    )


def _run_openai_compatible_submission_intent(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
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
        schema_name=SUBMISSION_INTENT_SCHEMA["name"],
        schema=SUBMISSION_INTENT_SCHEMA["schema"],
        strict=SUBMISSION_INTENT_SCHEMA["strict"],
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
        parse_payload=validate_submission_intent_content,
    )


def _run_anthropic_submission_intent(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
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
        parse_payload=validate_submission_intent_content,
    )


def _run_gemini_submission_intent(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    packet: dict,
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
        parse_payload=validate_submission_intent_content,
    )


def _run_mock_submission_intent(packet: dict, settings: Settings) -> ProviderResponse:
    trace_id, request_id = resolve_call_ids(packet)
    inferred = classify_submission_intent(
        " ".join(
            str(item)
            for item in (
                packet.get("user_message", ""),
                packet.get("repository_context", {}),
                packet.get("routing_rules", []),
            )
        )
    )
    if inferred is None:
        intent = "ambiguous"
        summary = "The request is ambiguous."
        matched_signals: list[str] = []
        reasoning = ["No clear routing signals were found."]
        suggested_action = "Ask a clarifying question about the target repository."
    else:
        intent = inferred.kind
        summary = f"Mock routing resolved the request as {intent}."
        matched_signals = [inferred.kind]
        reasoning = ["Mock routing uses the conservative classifier."]
        suggested_action = (
            "Proceed with maintainer publish flow."
            if intent == "maintainer_publish"
            else "Proceed with downstream submit flow."
        )
    payload = SubmissionIntentPayload(
        intent=intent,  # type: ignore[arg-type]
        summary=summary,
        reviewer_ref=f"{settings.llm_provider}:mock",
        model=settings.llm_model or "mock-model",
        confidence="medium" if intent == "ambiguous" else "high",
        matched_signals=matched_signals,
        reasoning=reasoning,
        suggested_action=suggested_action,
    )
    audit = ProviderAuditPayload(
        trace_id=trace_id,
        request_id=request_id,
        provider_name="mock",
        endpoint="mock://submission-intent",
        call_status="mocked",
        attempt_count=1,
        duration_ms=0,
        request_json={"user_message": packet.get("user_message", "")},
        response_json={"provider": "mock", "payload": payload.model_dump()},
        attempts=[ProviderAttemptPayload(attempt_no=1, status="mocked", duration_ms=0)],
        events=[],
    )
    return ProviderResponse(payload=payload, raw_response={"provider": "mock"}, audit=audit)
