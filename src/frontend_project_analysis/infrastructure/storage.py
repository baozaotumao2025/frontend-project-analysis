"""Database setup and low-level filesystem operations."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ..core.config import AppPaths, ensure_state_dirs, get_paths
from ..core.errors import StorageError
from .logging_utils import get_logger
from .migrations import ensure_database_migrated, get_migration_state

logger = get_logger(__name__)


def make_engine(paths: AppPaths | None = None):
    app_paths = paths or get_paths()
    ensure_state_dirs(app_paths)
    return create_engine(f"sqlite+pysqlite:///{app_paths.db_path}", future=True)


def initialize_database(paths: AppPaths | None = None) -> Path:
    app_paths = paths or get_paths()
    ensure_state_dirs(app_paths)
    try:
        ensure_database_migrated(app_paths)
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("Failed to initialize database at %s", app_paths.db_path)
        raise StorageError(f"Failed to initialize database at {app_paths.db_path}") from exc
    logger.info("Initialized database at %s", app_paths.db_path)
    return app_paths.db_path


@contextmanager
def session_scope(paths: AppPaths | None = None) -> Iterator[Session]:
    engine = make_engine(paths)
    ensure_database_migrated(paths or get_paths())
    with Session(engine, expire_on_commit=False) as session:
        session.execute(text("PRAGMA foreign_keys = ON"))
        yield session


def get_migration_status(paths: AppPaths | None = None):
    app_paths = paths or get_paths()
    return get_migration_state(app_paths)


def backup_database(paths: AppPaths | None = None, output_path: Path | None = None) -> Path:
    app_paths = paths or get_paths()
    ensure_state_dirs(app_paths)
    if not app_paths.db_path.exists():
        raise FileNotFoundError("Database has not been initialized yet.")
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    target = output_path or app_paths.backup_dir / f"{timestamp}.db"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(app_paths.db_path, target)
    logger.info("Backed up database to %s", target)
    return target


def restore_database(
    paths: AppPaths | None = None,
    source_path: Path | None = None,
) -> tuple[Path, Path]:
    app_paths = paths or get_paths()
    if source_path is None:
        raise ValueError("A source backup path is required.")
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    previous = (
        backup_database(app_paths)
        if app_paths.db_path.exists()
        else app_paths.backup_dir / "pre-restore-empty.db"
    )
    source_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, app_paths.db_path)
    logger.info("Restored database from %s to %s", source_path, app_paths.db_path)
    return previous, app_paths.db_path


def wipe_database(paths: AppPaths | None = None) -> None:
    app_paths = paths or get_paths()
    if app_paths.db_path.exists():
        app_paths.db_path.unlink()
        logger.warning("Deleted database file %s", app_paths.db_path)
