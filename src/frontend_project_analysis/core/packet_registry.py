"""Packet registry for packet-driven workflows."""

from __future__ import annotations

from .packet_specs import PACKET_SPECS
from .packet_types import PacketSpec

PACKET_REGISTRY: dict[str, PacketSpec] = PACKET_SPECS


def get_packet_spec(name: str) -> PacketSpec:
    try:
        return PACKET_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown packet spec '{name}'.") from exc


def list_packet_specs() -> tuple[PacketSpec, ...]:
    return tuple(PACKET_REGISTRY[name] for name in sorted(PACKET_REGISTRY))
