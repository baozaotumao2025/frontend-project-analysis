"""HTTP transport and retry helpers for LLM providers."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .errors import (
    ProviderAuthenticationError,
    ProviderAuthorizationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderTransportError,
)
from .logging_utils import get_logger
from .schemas import ProviderAttemptPayload, ProviderAuditEventPayload, ProviderAuditPayload

logger = get_logger(__name__)


def post_json(
    provider_name: str,
    endpoint: str,
    request_json: dict[str, Any],
    headers: dict[str, str],
    settings: Settings,
    trace_id: str,
    request_id: str,
) -> tuple[dict[str, Any], ProviderAuditPayload]:
    payload_bytes = json.dumps(request_json, ensure_ascii=True).encode("utf-8")
    attempts: list[ProviderAttemptPayload] = []
    events: list[ProviderAuditEventPayload] = [
        ProviderAuditEventPayload(
            event_type="request_prepared",
            message="Provider request payload prepared.",
            offset_ms=0,
            data={"provider": provider_name, "endpoint": endpoint},
        )
    ]
    started = time.perf_counter()
    last_error: str | None = None

    for attempt_no in range(1, settings.llm_max_retries + 1):
        attempt_started_wall = int((time.perf_counter() - started) * 1000)
        events.append(
            ProviderAuditEventPayload(
                event_type="attempt_started",
                message="Sending provider request attempt.",
                offset_ms=attempt_started_wall,
                attempt_no=attempt_no,
            )
        )
        request = Request(endpoint, data=payload_bytes, headers=headers, method="POST")
        attempt_started = time.perf_counter()
        try:
            with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
            attempt_ms = int((time.perf_counter() - attempt_started) * 1000)
            attempts.append(
                ProviderAttemptPayload(
                    attempt_no=attempt_no,
                    status="success",
                    duration_ms=attempt_ms,
                    http_status=200,
                )
            )
            duration_ms = int((time.perf_counter() - started) * 1000)
            events.append(
                ProviderAuditEventPayload(
                    event_type="attempt_succeeded",
                    message="Provider request attempt completed successfully.",
                    offset_ms=duration_ms,
                    attempt_no=attempt_no,
                    data={"http_status": 200},
                )
            )
            audit = ProviderAuditPayload(
                trace_id=trace_id,
                request_id=request_id,
                provider_name=provider_name,
                error_code=None,
                endpoint=endpoint,
                call_status="success",
                attempt_count=attempt_no,
                duration_ms=duration_ms,
                request_json=request_json,
                response_json=raw_response,
                attempts=attempts,
                events=events,
            )
            return raw_response, audit
        except HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            attempt_ms = int((time.perf_counter() - attempt_started) * 1000)
            attempts.append(
                ProviderAttemptPayload(
                    attempt_no=attempt_no,
                    status="http_error",
                    duration_ms=attempt_ms,
                    error=body_text,
                    http_status=exc.code,
                )
            )
            logger.error("Provider HTTP error %s: %s", exc.code, body_text)
            events.append(
                ProviderAuditEventPayload(
                    event_type="attempt_failed",
                    message="Provider returned an HTTP error.",
                    offset_ms=int((time.perf_counter() - started) * 1000),
                    attempt_no=attempt_no,
                    data={"http_status": exc.code, "error": body_text},
                )
            )
            last_error = f"HTTP {exc.code}"
            if not should_retry_http(exc.code, attempt_no, settings):
                break
            events.append(
                ProviderAuditEventPayload(
                    event_type="retry_scheduled",
                    message="Retry scheduled after HTTP error.",
                    offset_ms=int((time.perf_counter() - started) * 1000),
                    attempt_no=attempt_no,
                    data={"next_attempt": attempt_no + 1},
                )
            )
        except URLError as exc:
            attempt_ms = int((time.perf_counter() - attempt_started) * 1000)
            attempts.append(
                ProviderAttemptPayload(
                    attempt_no=attempt_no,
                    status="url_error",
                    duration_ms=attempt_ms,
                    error=str(exc.reason),
                )
            )
            logger.error("Provider URL error: %s", exc)
            events.append(
                ProviderAuditEventPayload(
                    event_type="attempt_failed",
                    message="Provider request failed with URL error.",
                    offset_ms=int((time.perf_counter() - started) * 1000),
                    attempt_no=attempt_no,
                    data={"error": str(exc.reason)},
                )
            )
            if isinstance(exc.reason, TimeoutError):
                last_error = "HTTP 408"
            else:
                last_error = str(exc.reason)
            if attempt_no >= settings.llm_max_retries:
                break
            events.append(
                ProviderAuditEventPayload(
                    event_type="retry_scheduled",
                    message="Retry scheduled after transport error.",
                    offset_ms=int((time.perf_counter() - started) * 1000),
                    attempt_no=attempt_no,
                    data={"next_attempt": attempt_no + 1},
                )
            )

        sleep_backoff(attempt_no, settings)

    duration_ms = int((time.perf_counter() - started) * 1000)
    audit = ProviderAuditPayload(
        trace_id=trace_id,
        request_id=request_id,
        provider_name=provider_name,
        error_code=_error_code_for_http_message(last_error)
        or (
            ProviderTimeoutError.error_code
            if last_error == "HTTP 408"
            else ProviderTransportError.error_code
            if last_error
            else None
        ),
        endpoint=endpoint,
        call_status="failed",
        attempt_count=len(attempts),
        duration_ms=duration_ms,
        request_json=request_json,
        response_json=None,
        error_message=last_error,
        attempts=attempts,
        events=events
        + [
            ProviderAuditEventPayload(
                event_type="request_exhausted",
                message="Provider request failed after retry budget was exhausted.",
                offset_ms=duration_ms,
                data={"attempt_count": len(attempts)},
            )
        ],
    )
    raise _error_for_http_failure(
        provider_name=provider_name,
        audit=audit,
        status_code=_status_code_from_error_message(last_error),
    )


def should_retry_http(status_code: int, attempt_no: int, settings: Settings) -> bool:
    retryable = {408, 409, 429, 500, 502, 503, 504}
    return status_code in retryable and attempt_no < settings.llm_max_retries


def sleep_backoff(attempt_no: int, settings: Settings) -> None:
    if attempt_no >= settings.llm_max_retries:
        return
    delay = min(
        settings.llm_retry_initial_backoff_seconds * (2 ** (attempt_no - 1)),
        settings.llm_retry_max_backoff_seconds,
    )
    time.sleep(delay)


def _error_code_for_status(status_code: int | None) -> str | None:
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


def _status_code_from_error_message(message: str | None) -> int | None:
    if not message:
        return None
    if message.startswith("HTTP "):
        try:
            return int(message.split(" ", 1)[1])
        except ValueError:
            return None
    return None


def _error_code_for_http_message(message: str | None) -> str | None:
    return _error_code_for_status(_status_code_from_error_message(message))


def _error_for_http_failure(
    provider_name: str,
    audit: ProviderAuditPayload,
    status_code: int | None,
) -> ProviderError:
    error_code = _error_code_for_status(status_code)
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
