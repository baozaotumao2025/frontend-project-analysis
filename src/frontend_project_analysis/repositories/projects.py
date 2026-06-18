"""Project repository helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..infrastructure.logging_utils import get_logger
from ..models import Project
from .errors import RepositoryError

logger = get_logger(__name__)


def ensure_project(session: Session, key: str, name: str, root_path: Path) -> Project:
    project = session.scalar(select(Project).where(Project.key == key))
    if project is None:
        project = Project(key=key, name=name, root_path=str(root_path))
        session.add(project)
        session.flush()
        logger.info("Created project '%s' at %s", key, root_path)
    return project


def get_project(session: Session, key: str) -> Project:
    project = session.scalar(select(Project).where(Project.key == key))
    if project is None:
        raise RepositoryError(f"Project '{key}' was not found. Run `fpa project init` first.")
    return project

