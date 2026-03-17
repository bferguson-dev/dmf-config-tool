"""CLI interface tests."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from dmf_tool.cli.main import cli
from tests.helpers.workbook_builder import WorkbookBuilder


def test_validate_command_succeeds_for_valid_workbook(tmp_path: Path) -> None:
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")
    result = CliRunner().invoke(
        cli,
        ["validate", "--input", str(workbook_path), "--dmf-version", "8.8"],
    )

    assert result.exit_code == 0
    assert "Linting input..." in result.output
    assert "BPR002" in result.output
    assert "Summary: 0 error(s), 3 warning(s), 0 info" in result.output
    assert "Validation complete. No output files written." in result.output


def test_validate_command_reports_structural_error(tmp_path: Path) -> None:
    workbook_path = (
        WorkbookBuilder()
        .with_missing_tab("fabric_settings")
        .save(tmp_path / "bad.xlsx")
    )
    result = CliRunner().invoke(
        cli,
        ["validate", "--input", str(workbook_path), "--dmf-version", "8.8"],
    )

    assert result.exit_code == 1
    assert "STR005" in result.output
    assert "Summary: 1 error(s), 0 warning(s), 0 info" in result.output
    assert "Validation blocked. Fix errors and re-run." in result.output


def test_generate_command_writes_expected_artifacts(tmp_path: Path) -> None:
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")
    output_dir = tmp_path / "output"
    result = CliRunner().invoke(
        cli,
        [
            "generate",
            "--input",
            str(workbook_path),
            "--dmf-version",
            "8.8",
            "--output",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Rendering templates... ✓" in result.output
    assert "Verifying output...    ✓" in result.output
    assert "cli-config.txt (SENSITIVE)" in result.output
    assert (output_dir / "findings.json").exists() is False
    run_dirs = list(output_dir.iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "findings.json").exists()
    assert (run_dirs[0] / "cli-config.txt").exists()
    assert (run_dirs[0] / "summary.md").exists()


def test_check_command_reports_success_without_writing_files(tmp_path: Path) -> None:
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")
    result = CliRunner().invoke(
        cli,
        ["check", "--input", str(workbook_path), "--dmf-version", "8.8"],
    )

    assert result.exit_code == 0
    assert "Rendering templates... ✓" in result.output
    assert "Check complete. No output files written." in result.output
    assert sorted(path.name for path in tmp_path.iterdir()) == ["valid.xlsx"]


def test_versions_command_lists_all_supported_bundles() -> None:
    result = CliRunner().invoke(cli, ["versions"])

    assert result.exit_code == 0
    assert "Supported DMF versions:" in result.output
    assert "- 8.6" in result.output
    assert "- 8.7" in result.output
    assert "- 8.8" in result.output


def test_bad_arguments_return_tool_error_exit_code() -> None:
    result = CliRunner().invoke(cli, ["validate", "--dmf-version", "8.8"])

    assert result.exit_code == 2
    assert "Missing option '--input'" in result.output
