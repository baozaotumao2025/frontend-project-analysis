"""Database wipe command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import wipe_database
from ..utils import handle_service_error
from . import db_app


@db_app.command("wipe")
@handle_service_error
def db_wipe(yes: bool = typer.Option(False, "--yes")) -> None:
    if not yes:
        raise typer.BadParameter("Pass --yes to confirm wiping the database.")
    wipe_database(get_paths())
