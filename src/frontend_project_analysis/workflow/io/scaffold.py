"""Project scaffold installation helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

SCAFFOLD_MANAGED_PATHS = (
    ".gitignore",
    ".python-version",
    "AGENTS.md",
    "Makefile",
    "README.md",
    "SKILL.md",
    "alembic.ini",
    "agents",
    "migrations",
    "pyproject.toml",
    "references",
    "scripts",
    "src",
)

_SKIP_PATH_SEGMENTS = {
    ".frontend-project-analysis",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "analysis",
    "docs",
    "specs",
}


def _template_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _iter_source_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(source).parts
        if any(part in _SKIP_PATH_SEGMENTS for part in relative_parts):
            continue
        files.append(path)
    return files


def _copy_file(source: Path, destination: Path, force: bool, dry_run: bool) -> str:
    if source.resolve() == destination.resolve():
        return "unchanged"

    if destination.exists():
        if not force:
            return "skipped_existing"
        if destination.is_dir():
            if not dry_run:
                shutil.rmtree(destination)
        else:
            if not dry_run:
                destination.unlink()
        action = "overwritten"
    else:
        action = "created"

    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return action


def install_project_scaffold(
    root: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> list[dict[str, str]]:
    """Legacy no-op compatibility hook.

    The target project no longer receives scaffold files from this hook.
    It intentionally leaves the repository tree untouched.
    """

    return []
