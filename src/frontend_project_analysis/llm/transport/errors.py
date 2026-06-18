"""HTTP error construction helpers for LLM provider transport."""

from __future__ import annotations

from ...core.errors import (
    ProviderAuthenticationError,
    ProviderAuthorizationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderTransportError,
)
from ...schemas import ProviderAuditPayload
from .status_codes import (
    error_code_for_http_message,
    error_code_for_status,
    status_code_from_error_message,
)


def error_for_http_failure(
    provider_name: str,
    audit: ProviderAuditPayload,
    status_code: int | None,
) -> ProviderError:
    error_code = error_code_for_status(status_code)
    payload = audit.model_dump()
    if status_code == 401:
        return ProviderAuthenticationError(
            "Provider authentication failed.",
            audit_payload=payload,
            provider_name=provider_name,
            status_code=status_code,
        )
    if status_code == 403:
        return ProviderAuthorizationError(
            "Provider authorization failed.",
            audit_payload=payload,
            provider_name=provider_name,
            status_code=status_code,
        )
    if status_code == 429:
        return ProviderRateLimitError(
            "Provider rate limit exceeded.",
            audit_payload=payload,
            provider_name=provider_name,
            status_code=status_code,
        )
    if status_code == 408:
        return ProviderTimeoutError(
            "Provider request timed out.",
            audit_payload=payload,
            provider_name=provider_name,
            status_code=status_code,
        )
    if status_code is not None and status_code >= 500:
        return ProviderServerError(
            "Provider returned a server error.",
            audit_payload=payload,
            provider_name=provider_name,
            status_code=status_code,
        )
    return ProviderTransportError(
        "Provider request failed after retries.",
        audit_payload={**payload, "error_code": error_code},
        provider_name=provider_name,
        status_code=status_code,
    )


__all__ = [
    "error_code_for_http_message",
    "error_code_for_status",
    "error_for_http_failure",
    "status_code_from_error_message",
]
