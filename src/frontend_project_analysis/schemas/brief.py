"""Brief assistant payload models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BriefAssistantPayload(BaseModel):
    stage: Literal["followup", "summary"]
    summary: str
    reviewer_ref: str = "brief-assistant"
    model: str | None = None
    can_finalize: bool = False
    confidence: Literal["low", "medium", "high"] = "medium"
    gaps: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)
    draft_brief: str | None = None
