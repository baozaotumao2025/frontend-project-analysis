"""Compatibility facade for packet builders."""

from __future__ import annotations

from .packet_builders import (
    build_brief_assistant_packet,
    build_review_llm_context,
    build_submission_packet,
)

__all__ = [
    "build_brief_assistant_packet",
    "build_review_llm_context",
    "build_submission_packet",
]
