"""Anthropic semantic review adapter."""

from __future__ import annotations

from ...core.config import Settings
from ..payloads import build_anthropic_request, resolve_call_ids
from ..provider_utils import (
    anthropic_api_path,
    anthropic_base_url,
    normalize_endpoint,
    require_provider_credentials,
)
from ..types import ProviderResponse
from ..validation import extract_anthropic_text
from .common import run_review_provider


def run_anthropic_review(packet: dict, settings: Settings) -> ProviderResponse:
    require_provider_credentials(settings)

    endpoint = normalize_endpoint(anthropic_base_url(settings), anthropic_api_path(settings))
    trace_id, request_id = resolve_call_ids(packet)
    body = build_anthropic_request(settings, packet)
    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": settings.anthropic_version,
        "Content-Type": "application/json",
    }
    from ...schemas import AnthropicReviewResponse

    return run_review_provider(
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
    )
