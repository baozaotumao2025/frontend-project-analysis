"""Shared LLM provider types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..schemas import ProviderAuditPayload, SemanticReviewPayload


@dataclass
class ProviderResponse:
    payload: SemanticReviewPayload
    raw_response: dict[str, Any]
    audit: ProviderAuditPayload
