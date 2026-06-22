"""Brief assistant packet spec."""

from __future__ import annotations

from ..packet_builders import build_brief_assistant_packet
from ..packet_types import PacketSpec

BRIEF_ASSISTANT_SPEC = PacketSpec(
    name="brief_assistant",
    description="Brief assistant packet",
    builder=build_brief_assistant_packet,
    required_keys=("stage", "answers", "transcript", "remaining_budget", "llm_isolation"),
    isolation_key="llm_isolation",
    isolation_mode="fresh_brief_assistant_context",
)
