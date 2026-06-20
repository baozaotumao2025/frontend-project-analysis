from __future__ import annotations

import re
import tomllib
from pathlib import Path


class ReleaseValidationError(RuntimeError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__("\n".join(issues))


def read_project_version(root: Path) -> str:
    pyproject_path = root / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def read_package_version(root: Path) -> str:
    init_path = root / "src" / "frontend_project_analysis" / "__init__.py"
    init_text = init_path.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"\s*$', init_text, re.MULTILINE)
    if match is None:
        raise ValueError("Could not find __version__ in src/frontend_project_analysis/__init__.py")
    return match.group(1)


def _has_changelog_release_section(changelog_text: str, version: str) -> bool:
    pattern = rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$"
    return re.search(pattern, changelog_text, re.MULTILINE) is not None


def validate_release_metadata(root: Path) -> list[str]:
    issues: list[str] = []

    project_version = read_project_version(root)
    package_version = read_package_version(root)
    if project_version != package_version:
        issues.append(
            "Version mismatch: pyproject.toml has "
            f"{project_version!r} but src/frontend_project_analysis/__init__.py has "
            f"{package_version!r}."
        )

    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        issues.append("CHANGELOG.md is missing.")
    else:
        changelog_text = changelog_path.read_text(encoding="utf-8")
        if "## [Unreleased]" not in changelog_text:
            issues.append("CHANGELOG.md must keep an Unreleased section at the top.")
        if not _has_changelog_release_section(changelog_text, project_version):
            issues.append(
                "CHANGELOG.md does not contain a dated release section for "
                f"{project_version!r}."
            )

    return issues


def assert_release_metadata(root: Path) -> None:
    issues = validate_release_metadata(root)
    if issues:
        raise ReleaseValidationError(issues)

