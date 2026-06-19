"""Workflow gate command group."""

from __future__ import annotations

import typer

workflow_app = typer.Typer(help="Workflow round gate commands.")
explore_workflow_app = typer.Typer(help="Exploratory workflow round gate commands.")


def register_workflow_commands(app: typer.Typer) -> None:
    app.add_typer(workflow_app, name="workflow")
    workflow_app.add_typer(explore_workflow_app, name="explore")


from . import gate  # noqa: E402,F401
