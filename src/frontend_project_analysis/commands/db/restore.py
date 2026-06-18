"""Database restore command."""

from __future__ import annotations

import json

import typer

from ...core.config import get_paths
from ...infrastructure.storage import restore_database
from ..utils import handle_service_error
from . import db_app


@db_app.command("restore")
@handle_service_error
def db_restore(source: str = typer.Option(..., "--from")) -> None:
    previous, current = restore_database(get_paths(), source_path=get_paths().root / source)
    typer.echo(json.dumps({"previous": str(previous), "current": str(current)}, indent=2))
