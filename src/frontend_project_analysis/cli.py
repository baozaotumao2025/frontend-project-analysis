"""Typer CLI for workflow governance."""

from __future__ import annotations

import typer

from .commands import (
    register_artifact_commands,
    register_db_commands,
    register_export_commands,
    register_import_commands,
    register_project_commands,
    register_review_commands,
    register_workflow_commands,
)
from .core.config import get_paths, get_settings
from .infrastructure.logging_utils import configure_logging, get_logger

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
register_workflow_commands(app)


if __name__ == "__main__":
    app()
