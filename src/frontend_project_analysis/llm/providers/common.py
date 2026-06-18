"""Shared execution helper for semantic review providers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from ...core.config import Settings
from ..provider_utils import validate_response_envelope
from ..transport import post_json
from ..types import ProviderResponse
from ..validation import validate_provider_payload


def run_review_provider(
    *,
    provider_name: str,
    endpoint: str,
    request_json: dict[str, Any],
    headers: dict[str, str],
    settings: Settings,
    trace_id: str,
    request_id: str,
    response_model: type[BaseModel],
    response_message: str,
    extract_text: Callable[[dict[str, Any]], str],
) -> ProviderResponse:
    raw_response, audit = post_json(
        provider_name=provider_name,
        endpoint=endpoint,
        request_json=request_json,
        headers=headers,
        settings=settings,
        trace_id=trace_id,
        request_id=request_id,
    )
    validate_response_envelope(
        response_model,
        raw_response,
        provider_name,
        audit,
        response_message,
    )
    content = extract_text(raw_response)
    parsed = validate_provider_payload(
        content,
        settings,
        provider_name=provider_name,
        audit=audit,
    )
    audit.response_json = raw_response
    audit.model_name = parsed.model
    audit.call_status = "completed"
    return ProviderResponse(payload=parsed, raw_response=raw_response, audit=audit)
