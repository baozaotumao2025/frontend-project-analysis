"""Workflow gate command group."""

from __future__ import annotations

import typer

workflow_app = typer.Typer(help="Workflow round gate commands.")


def register_workflow_commands(app: typer.Typer) -> None:
    app.add_typer(workflow_app, name="workflow")


from . import gate  # noqa: E402,F401
