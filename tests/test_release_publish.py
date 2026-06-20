from __future__ import annotations

import subprocess
from pathlib import Path

from frontend_project_analysis.release_policy import validate_release_metadata


def test_release_metadata_validation_accepts_current_repository() -> None:
    root = Path(__file__).resolve().parents[1]

    assert validate_release_metadata(root) == []


def test_release_metadata_validation_rejects_version_mismatch(tmp_path: Path) -> None:
    (tmp_path / "src" / "frontend_project_analysis").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "frontend-project-analysis"',
                'version = "9.9.9"',
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "src" / "frontend_project_analysis" / "__init__.py").write_text(
        '__version__ = "9.9.8"\n',
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                "## [Unreleased]",
                "",
                "## [9.9.9] - 2026-06-20",
                "",
                "### Added",
                "",
                "- Placeholder.",
            ]
        ),
        encoding="utf-8",
    )

    issues = validate_release_metadata(tmp_path)

    assert any("Version mismatch" in issue for issue in issues)
    assert not any("dated release section" in issue for issue in issues)


def test_release_publish_help_is_discoverable() -> None:
    root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        ["./scripts/release-publish.sh", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "maintainer publish" in result.stdout.lower()
