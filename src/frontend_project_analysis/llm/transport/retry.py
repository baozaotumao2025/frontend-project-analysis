"""Retry helpers for LLM provider transport."""

from __future__ import annotations

import time

from ...core.config import Settings


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
