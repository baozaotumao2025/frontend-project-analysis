"""Shared LLM provider types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from ..schemas import ProviderAuditPayload


@dataclass
class ProviderResponse:
    payload: BaseModel
    raw_response: dict[str, Any]
    audit: ProviderAuditPayload
