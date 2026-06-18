"""LLM provider response validation and text extraction."""

from __future__ import annotations

from typing import Any

from ..core.config import Settings
from ..core.errors import ProviderResponseError, ProviderValidationError
from ..infrastructure.logging_utils import get_logger
from ..schemas import ProviderAuditEventPayload, ProviderAuditPayload, SemanticReviewPayload

logger = get_logger(__name__)


def validate_provider_payload(
    content: str,
    settings: Settings,
    provider_name: str,
    audit: ProviderAuditPayload,
) -> SemanticReviewPayload:
    try:
        parsed = SemanticReviewPayload.model_validate_json(content)
    except Exception as exc:  # pragma: no cover - depends on provider output
        logger.error("Provider returned non-conforming JSON: %s", content)
        audit.events.append(
            ProviderAuditEventPayload(
                event_type="semantic_payload_validation_failed",
                message="Semantic review payload JSON validation failed.",
                offset_ms=audit.duration_ms,
                data={"provider": provider_name},
            )
        )
        audit.error_code = ProviderValidationError.error_code
        raise ProviderValidationError(
            "Provider returned invalid semantic review JSON.",
            audit_payload=audit.model_dump(),
            provider_name=provider_name,
        ) from exc

    if not parsed.model:
        parsed.model = settings.llm_model
    if not parsed.reviewer_ref:
        parsed.reviewer_ref = provider_name
    audit.events.append(
        ProviderAuditEventPayload(
            event_type="semantic_payload_validated",
            message="Semantic review payload validated successfully.",
            offset_ms=audit.duration_ms,
            data={"provider": provider_name},
        )
    )
    return parsed


def extract_anthropic_text(raw_response: dict[str, Any]) -> str:
    for item in raw_response.get("content", []):
        if item.get("type") == "text":
            return item.get("text", "")
    raise ProviderResponseError(
        "Anthropic response did not include text content.",
        provider_name="anthropic",
    )


def extract_gemini_text(raw_response: dict[str, Any]) -> str:
    candidates = raw_response.get("candidates", [])
    for candidate in candidates:
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                return text
    raise ProviderResponseError(
        "Gemini response did not include text content.",
        provider_name="gemini",
    )


def extract_output_text(raw_response: dict[str, Any]) -> str:
    output = raw_response.get("output", [])
    for item in output:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")
    raise ProviderResponseError(
        "Provider response did not include output_text content.",
        provider_name="openai",
    )
