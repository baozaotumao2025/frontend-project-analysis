"""Database backup command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import backup_database
from ..utils import handle_service_error
from . import db_app


@db_app.command("backup")
@handle_service_error
def db_backup() -> None:
    path = backup_database(get_paths())
    typer.echo(str(path))
