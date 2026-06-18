"""Database command group."""

from __future__ import annotations

import typer

db_app = typer.Typer(help="Database lifecycle commands.")


def register_db_commands(app: typer.Typer) -> None:
    app.add_typer(db_app, name="db")


from . import backup, init, restore, wipe  # noqa: E402,F401
