"""Database initialization command."""

from __future__ import annotations

from ...core.config import get_paths
from ...infrastructure.storage import initialize_database
from ..utils import handle_service_error
from . import db_app


@db_app.command("init")
@handle_service_error
def db_init() -> None:
    initialize_database(get_paths())
