"""Generator pipeline tests."""

from __future__ import annotations

from pathlib import Path

from dmf_tool.core.generator import Generator
from tests.helpers.workbook_builder import WorkbookBuilder


def test_generator_pipeline_succeeds_for_valid_workbook(tmp_path: Path) -> None:
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")
    result = Generator(clock=lambda: "2026-03-17T14:32:01").run(
        workbook_path,
        "8.8",
        tmp_path / "output",
    )

    assert result.success is True
    assert result.run_id == "2026-03-17T14-32-01"
    assert (result.output_dir / "findings.json").exists()
    assert (result.output_dir / "findings.txt").exists()
    assert (result.output_dir / "cli-config.txt").exists()
    assert (result.output_dir / "summary.md").exists()


def test_generator_pipeline_halts_on_structural_error(tmp_path: Path) -> None:
    builder = WorkbookBuilder().with_missing_tab("fabric_settings")
    workbook_path = builder.save(tmp_path / "invalid.xlsx")

    result = Generator(clock=lambda: "2026-03-17T14:32:01").run(
        workbook_path,
        "8.8",
        tmp_path / "output",
    )

    assert result.success is False
    assert (result.output_dir / "findings.json").exists()
    assert not (result.output_dir / "cli-config.txt").exists()
