"""Artifact command group."""

from __future__ import annotations

import typer

artifact_app = typer.Typer(help="Artifact registration and dependency commands.")


def register_artifact_commands(app: typer.Typer) -> None:
    app.add_typer(artifact_app, name="artifact")


from . import add, link, listing, ready  # noqa: E402,F401
