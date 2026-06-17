"""Typer CLI for workflow governance."""

from __future__ import annotations

import typer

from .artifact_commands import register_artifact_commands
from .config import get_paths, get_settings
from .db_commands import register_db_commands
from .export_commands import register_export_commands
from .import_commands import register_import_commands
from .logging_utils import configure_logging, get_logger
from .project_commands import register_project_commands
from .review_commands import register_review_commands

app = typer.Typer(help="Frontend project analysis workflow infrastructure.")
logger = get_logger(__name__)


@app.callback()
def main() -> None:
    """Bootstrap shared runtime configuration."""

    settings = get_settings()
    paths = get_paths()
    configure_logging(settings, paths)
    logger.debug("Runtime initialized with state dir %s", paths.state_dir)


register_project_commands(app)
register_artifact_commands(app)
register_review_commands(app)
register_export_commands(app)
register_import_commands(app)
register_db_commands(app)


if __name__ == "__main__":
    app()
