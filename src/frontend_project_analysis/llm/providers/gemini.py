"""Gemini semantic review adapter."""

from __future__ import annotations

from ...core.config import Settings
from ..payloads import build_gemini_request, resolve_call_ids
from ..provider_utils import (
    gemini_api_path,
    gemini_base_url,
    normalize_endpoint,
    require_provider_credentials,
)
from ..types import ProviderResponse
from ..validation import extract_gemini_text
from .common import run_review_provider


def run_gemini_review(packet: dict, settings: Settings) -> ProviderResponse:
    require_provider_credentials(settings)

    endpoint = normalize_endpoint(gemini_base_url(settings), gemini_api_path(settings))
    trace_id, request_id = resolve_call_ids(packet)
    body = build_gemini_request(settings, packet)
    headers = {
        "x-goog-api-key": settings.llm_api_key,
        "Content-Type": "application/json",
    }
    from ...schemas import GeminiReviewResponse

    return run_review_provider(
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
    )
