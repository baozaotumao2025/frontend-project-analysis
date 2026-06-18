"""OpenAI-compatible semantic review adapter."""

from __future__ import annotations

from ...core.config import Settings
from ..payloads import build_openai_request, resolve_call_ids
from ..provider_utils import (
    normalize_endpoint,
    openai_api_path,
    openai_base_url,
    require_provider_credentials,
)
from ..types import ProviderResponse
from ..validation import extract_output_text
from .common import run_review_provider


def run_openai_review(packet: dict, settings: Settings) -> ProviderResponse:
    return run_openai_compatible_review(
        packet,
        settings,
        default_base_url=openai_base_url(settings),
    )


def run_openai_compatible_review(
    packet: dict,
    settings: Settings,
    default_base_url: str | None = None,
) -> ProviderResponse:
    require_provider_credentials(settings)

    endpoint = normalize_endpoint(
        settings.llm_base_url or default_base_url or "https://api.openai.com/v1",
        openai_api_path(settings),
    )
    trace_id, request_id = resolve_call_ids(packet)
    body = build_openai_request(settings, packet)
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    if settings.llm_organization:
        headers["OpenAI-Organization"] = settings.llm_organization
    from ...schemas import OpenAIReviewResponse

    return run_review_provider(
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
    )
