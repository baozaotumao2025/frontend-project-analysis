"""HTTP status code helpers for LLM provider transport."""

from __future__ import annotations

from ...core.errors import (
    ProviderAuthenticationError,
    ProviderAuthorizationError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderTransportError,
)


def error_code_for_status(status_code: int | None) -> str | None:
    if status_code is None:
        return None
    if status_code == 401:
        return ProviderAuthenticationError.error_code
    if status_code == 403:
        return ProviderAuthorizationError.error_code
    if status_code == 429:
        return ProviderRateLimitError.error_code
    if status_code == 408:
        return ProviderTimeoutError.error_code
    if status_code >= 500:
        return ProviderServerError.error_code
    return ProviderTransportError.error_code


def status_code_from_error_message(message: str | None) -> int | None:
    if not message:
        return None
    if message.startswith("HTTP "):
        try:
            return int(message.split(" ", 1)[1])
        except ValueError:
            return None
    return None


def error_code_for_http_message(message: str | None) -> str | None:
    return error_code_for_status(status_code_from_error_message(message))
