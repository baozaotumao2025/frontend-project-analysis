"""Natural-language submission routing commands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from ..core.config import get_paths, get_settings
from ..core.packets import build_submission_packet
from ..llm import run_submission_intent
from .utils import handle_service_error


def _git_output(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _build_repository_context(root: Path) -> dict[str, object]:
    return {
        "root": str(root),
        "branch": _git_output(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "head": _git_output(root, "rev-parse", "HEAD"),
        "remote": _git_output(root, "remote", "-v"),
    }


def _build_submission_packet(request: str, root: Path) -> dict[str, object]:
    return build_submission_packet(
        request,
        repository_context=_build_repository_context(root),
    )


def _render_submission_result(result) -> str:
    payload = result.payload.model_dump()
    return json.dumps(
        {
            "command": "submit",
            "intent": payload.get("intent"),
            "confidence": payload.get("confidence"),
            "summary": payload.get("summary"),
            "suggested_action": payload.get("suggested_action"),
            "payload": payload,
            "audit": result.audit.model_dump(),
        },
        indent=2,
    )


@handle_service_error
def submit(
    request: str | None = typer.Argument(None, help="Natural language request to route."),
) -> None:
    settings = get_settings()
    paths = get_paths()
    if request is None or not request.strip():
        request = typer.prompt("Describe what you want to do")
    packet = _build_submission_packet(request.strip(), paths.root)
    result = run_submission_intent(packet, settings)
    typer.echo(_render_submission_result(result))
    if result.payload.model_dump().get("intent") == "ambiguous":
        raise typer.Exit(1)
