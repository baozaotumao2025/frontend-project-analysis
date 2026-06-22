"""Submission routing packet spec."""

from __future__ import annotations

from ..packet_builders.submission import build_submission_packet
from ..packet_types import PacketSpec

SUBMISSION_ROUTER_SPEC = PacketSpec(
    name="submission_router",
    description="Submission routing packet",
    builder=build_submission_packet,
    required_keys=(
        "user_message",
        "repository_context",
        "available_actions",
        "routing_rules",
        "llm_isolation",
    ),
    isolation_key="llm_isolation",
    isolation_mode="fresh_submission_router_context",
)
