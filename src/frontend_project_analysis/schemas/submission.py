"""Submission intent payload models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SubmissionIntentPayload(BaseModel):
    intent: Literal["maintainer_publish", "downstream_submit", "ambiguous"]
    summary: str
    reviewer_ref: str = "intent-router"
    model: str | None = None
    confidence: Literal["low", "medium", "high"] = "medium"
    matched_signals: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)
    suggested_action: str | None = None
