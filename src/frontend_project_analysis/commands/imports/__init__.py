"""Import command group."""

from __future__ import annotations

import typer

import_app = typer.Typer(help="Import commands for manifests and Markdown sources.")


def register_import_commands(app: typer.Typer) -> None:
    app.add_typer(import_app, name="import")


from . import manifest, markdown_scan  # noqa: E402,F401
