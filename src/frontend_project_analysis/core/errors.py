"""Shared application exceptions."""

from __future__ import annotations


class AppError(RuntimeError):
    """Base class for user-facing application errors."""


class ConfigurationError(AppError):
    """Raised when runtime configuration is invalid."""


class StorageError(AppError):
    """Raised when database or file storage operations fail."""


class ReviewError(AppError):
    """Raised when review workflow operations fail."""


class ProviderError(AppError):
    """Raised when an LLM provider request fails."""

    error_code = "provider_error"

    def __init__(
        self,
        message: str,
        audit_payload: dict | None = None,
        provider_name: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.audit_payload = audit_payload or {}
        self.provider_name = provider_name
        self.status_code = status_code
        self.error_code = self.__class__.error_code


class ProviderTransportError(ProviderError):
    """Raised when the provider cannot be reached or times out."""

    error_code = "provider_transport_error"


class ProviderTimeoutError(ProviderTransportError):
    """Raised when the provider request times out."""

    error_code = "provider_timeout_error"


class ProviderAuthenticationError(ProviderError):
    """Raised when provider authentication fails."""

    error_code = "provider_authentication_error"


class ProviderAuthorizationError(ProviderError):
    """Raised when provider authorization fails."""

    error_code = "provider_authorization_error"


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limits are exceeded."""

    error_code = "provider_rate_limit_error"


class ProviderServerError(ProviderTransportError):
    """Raised when the provider returns a 5xx response."""

    error_code = "provider_server_error"


class ProviderResponseError(ProviderError):
    """Raised when the provider returns an unexpected envelope."""

    error_code = "provider_response_error"


class ProviderValidationError(ProviderError):
    """Raised when the provider payload cannot be parsed into the semantic schema."""

    error_code = "provider_validation_error"
