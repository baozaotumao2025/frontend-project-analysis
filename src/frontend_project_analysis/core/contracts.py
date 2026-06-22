"""Shared contract helpers for isolated packet-driven flows."""

from __future__ import annotations

from .errors import ConfigurationError


def build_isolation_contract(mode: str) -> dict[str, object]:
    return {
        "mode": mode,
        "fork_context": False,
        "required": True,
    }


def assert_isolation_contract(packet: dict, *, key: str, mode: str, label: str) -> None:
    isolation = packet.get(key)
    if not isinstance(isolation, dict):
        if label == "Semantic review":
            raise ConfigurationError(
                "Semantic review packet must include a fresh reviewer sub-agent contract."
            )
        raise ConfigurationError(f"{label} packet must include a fresh isolated context contract.")
    if isolation.get("mode") != mode:
        raise ConfigurationError(f"{label} packet must declare {mode} isolation.")
    if isolation.get("fork_context") is not False or isolation.get("required") is not True:
        raise ConfigurationError(
            f"{label} packet must require a non-forked isolated context."
        )
