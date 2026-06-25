"""Export command group."""

from __future__ import annotations

import typer

export_app = typer.Typer(help="Export commands for manifests and relations.")


def register_export_commands(app: typer.Typer) -> None:
    app.add_typer(export_app, name="export")


from . import graph_html, graph_json, manifest, relations  # noqa: E402,F401
