"""Packet registry types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .contracts import assert_isolation_contract

PacketBuilder = Callable[..., dict[str, object]]
PacketValidator = Callable[[dict], None]


@dataclass(frozen=True)
class PacketSpec:
    name: str
    description: str
    builder: PacketBuilder
    required_keys: tuple[str, ...]
    isolation_key: str | None = None
    isolation_mode: str | None = None

    def validate(self, packet: dict) -> None:
        missing = [key for key in self.required_keys if key not in packet]
        if missing:
            raise ValueError(
                f"Packet '{self.name}' is missing required keys: {', '.join(missing)}"
            )
        if self.isolation_key and self.isolation_mode:
            assert_isolation_contract(
                packet,
                key=self.isolation_key,
                mode=self.isolation_mode,
                label=self.description,
            )
