"""Generator pipeline tests."""

from click.testing import CliRunner

from dmf_tool.cli.main import cli


def test_cli_help_renders() -> None:
    """Exercise the bootstrap CLI entry point."""
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Run the DMF tool command group." in result.output
