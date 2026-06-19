import pytest
from typer.testing import CliRunner

from frontend_project_analysis.cli import app

pytestmark = pytest.mark.smoke


runner = CliRunner()


def test_cli_exposes_expected_top_level_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "brief" in result.stdout
    assert "init" in result.stdout
    assert "project" in result.stdout
    assert "artifact" in result.stdout
    assert "review" in result.stdout
    assert "export" in result.stdout
    assert "import" in result.stdout
    assert "db" in result.stdout


def test_cli_subcommand_groups_render_help() -> None:
    for args in (
        ["brief", "--help"],
        ["project", "--help"],
        ["artifact", "--help"],
        ["review", "--help"],
        ["workflow", "--help"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code == 0


def test_workflow_help_shows_explore_entrypoint() -> None:
    result = runner.invoke(app, ["workflow", "--help"])

    assert result.exit_code == 0
    assert "explore" in result.stdout
