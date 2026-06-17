"""Alembic integration helpers.

This module keeps migration concerns separate from runtime storage helpers.
The application layer only asks for high-level operations such as
``initialize_database`` or ``upgrade_database`` and never manipulates Alembic
internals directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from .config import AppPaths


@dataclass(frozen=True)
class MigrationState:
    current_revision: str | None
    head_revision: str | None
    has_tables: bool

    @property
    def is_initialized(self) -> bool:
        return self.current_revision is not None or self.has_tables

    @property
    def is_at_head(self) -> bool:
        return self.current_revision is not None and self.current_revision == self.head_revision


def make_alembic_config(paths: AppPaths) -> Config:
    config = Config(str(paths.root / "alembic.ini"))
    config.set_main_option("script_location", str(paths.root / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{paths.db_path}")
    config.set_main_option("prepend_sys_path", str(paths.root / "src"))
    return config


def get_migration_state(paths: AppPaths) -> MigrationState:
    config = make_alembic_config(paths)
    script = ScriptDirectory.from_config(config)
    head_revision = script.get_current_head()
    if not paths.db_path.exists():
        return MigrationState(current_revision=None, head_revision=head_revision, has_tables=False)

    engine = create_engine(f"sqlite+pysqlite:///{paths.db_path}", future=True)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            has_tables = bool(inspector.get_table_names())
            context = MigrationContext.configure(connection)
            current_revision = context.get_current_revision()
    finally:
        engine.dispose()
    return MigrationState(
        current_revision=current_revision,
        head_revision=head_revision,
        has_tables=has_tables,
    )


def ensure_database_migrated(paths: AppPaths) -> MigrationState:
    config = make_alembic_config(paths)
    state = get_migration_state(paths)
    if not state.has_tables:
        command.upgrade(config, "head")
        return get_migration_state(paths)
    if state.current_revision is None:
        command.stamp(config, "head")
        return get_migration_state(paths)
    if state.current_revision != state.head_revision:
        command.upgrade(config, "head")
        return get_migration_state(paths)
    return state


def upgrade_database(paths: AppPaths, revision: str = "head") -> None:
    command.upgrade(make_alembic_config(paths), revision)


def stamp_database(paths: AppPaths, revision: str = "head") -> None:
    command.stamp(make_alembic_config(paths), revision)


def revision_directory(paths: AppPaths) -> Path:
    return paths.root / "migrations" / "versions"
