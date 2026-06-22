"""Semantic review packet spec."""

from __future__ import annotations

from ..packet_builders import build_review_llm_context
from ..packet_types import PacketSpec

REVIEW_LLM_CONTEXT_SPEC = PacketSpec(
    name="review_llm_context",
    description="Semantic review packet context",
    builder=build_review_llm_context,
    required_keys=(
        "provider",
        "model",
        "base_url",
        "api_path",
        "max_output_tokens",
        "timeout_seconds",
        "temperature",
        "organization",
        "anthropic_version",
        "review_isolation",
    ),
    isolation_key="review_isolation",
    isolation_mode="fresh_reviewer_subagent",
)
