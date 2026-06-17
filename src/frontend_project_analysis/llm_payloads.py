"""LLM request builders and mock adapter."""

from __future__ import annotations

from uuid import uuid4

from .config import Settings
from .prompts import SEMANTIC_REVIEW_SYSTEM_PROMPT, build_semantic_review_user_prompt
from .schemas import (
    AnthropicReviewRequest,
    GeminiReviewRequest,
    OpenAIReviewRequest,
    ProviderAttemptPayload,
    ProviderAuditEventPayload,
    ProviderAuditPayload,
    SemanticReviewPayload,
)
from .llm_types import ProviderResponse, SEMANTIC_REVIEW_SCHEMA


def resolve_call_ids(packet: dict) -> tuple[str, str]:
    trace_id = str(packet.get("trace_id") or uuid4().hex)
    request_id = str(packet.get("request_id") or uuid4().hex)
    return trace_id, request_id


def build_openai_request(settings: Settings, packet: dict) -> dict:
    return OpenAIReviewRequest(
        model=settings.llm_model or "",
        input=[
            {"role": "developer", "content": SEMANTIC_REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": build_semantic_review_user_prompt(packet)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": SEMANTIC_REVIEW_SCHEMA["name"],
                "schema": SEMANTIC_REVIEW_SCHEMA["schema"],
                "strict": SEMANTIC_REVIEW_SCHEMA["strict"],
            }
        },
        max_output_tokens=settings.llm_max_output_tokens,
    ).model_dump()


def build_anthropic_request(settings: Settings, packet: dict) -> dict:
    return AnthropicReviewRequest(
        model=settings.llm_model or "",
        max_tokens=settings.llm_max_output_tokens,
        system=SEMANTIC_REVIEW_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": build_semantic_review_user_prompt(packet),
            }
        ],
    ).model_dump()


def build_gemini_request(settings: Settings, packet: dict) -> dict:
    return GeminiReviewRequest(
        system_instruction={
            "parts": [{"text": SEMANTIC_REVIEW_SYSTEM_PROMPT}],
        },
        contents=[
            {
                "role": "user",
                "parts": [{"text": build_semantic_review_user_prompt(packet)}],
            }
        ],
        generationConfig={
            "temperature": settings.llm_temperature,
            "maxOutputTokens": settings.llm_max_output_tokens,
            "responseMimeType": "application/json",
        },
    ).model_dump()


def run_mock_review(packet: dict, settings: Settings) -> ProviderResponse:
    artifact = packet["artifact"]["ref"]
    trace_id, request_id = resolve_call_ids(packet)
    payload = SemanticReviewPayload(
        decision="needs_revision",
        summary=f"Mock semantic review for {artifact}.",
        reviewer_ref=f"{settings.llm_provider}:mock",
        model=settings.llm_model or "mock-model",
        findings=[
            {
                "severity": "WARN",
                "code": "mock_review",
                "message": "Mock provider does not assess business quality.",
                "details": {"artifact_ref": artifact},
            }
        ],
    )
    events = [
        ProviderAuditEventPayload(
            event_type="mock_response_generated",
            message="Mock provider generated a deterministic response.",
            offset_ms=0,
            data={"artifact_ref": artifact},
        ),
        ProviderAuditEventPayload(
            event_type="semantic_payload_ready",
            message="Mock semantic review payload is ready for persistence.",
            offset_ms=0,
            data={"artifact_ref": artifact},
        ),
    ]
    audit = ProviderAuditPayload(
        trace_id=trace_id,
        request_id=request_id,
        provider_name="mock",
        error_code=None,
        model_name=payload.model,
        endpoint="mock://semantic-review",
        call_status="mocked",
        attempt_count=1,
        duration_ms=0,
        request_json={"artifact_ref": artifact},
        response_json={"provider": "mock", "payload": payload.model_dump()},
        attempts=[
            ProviderAttemptPayload(
                attempt_no=1,
                status="mocked",
                duration_ms=0,
            )
        ],
        events=events,
    )
    return ProviderResponse(payload=payload, raw_response={"provider": "mock"}, audit=audit)
