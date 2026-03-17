"""Artifact output tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jinja2 import UndefinedError

from dmf_tool.core.generator import Generator
from dmf_tool.core.models.fabric import Fabric, FabricSettings
from dmf_tool.core.rendering import build_environment, render_config
from dmf_tool.core.versions.dmf_8_8 import BUNDLE as DMF88_BUNDLE
from tests.helpers.workbook_builder import WorkbookBuilder


def test_strict_undefined_raises_for_missing_variables() -> None:
    environment = build_environment(DMF88_BUNDLE.template_dir)
    template = environment.get_template("provenance_header.j2")

    with pytest.raises(UndefinedError):
        template.render()


def test_provenance_header_fields_are_present() -> None:
    fabric = Fabric(
        dmf_version="8.8",
        fabric_settings=FabricSettings(fabric_name="fabric-a"),
    )
    rendered = render_config(
        DMF88_BUNDLE,
        fabric,
        {
            "tool_version": "0.1.0",
            "template_bundle_version": "8.8",
            "workbook_schema_version": "1.0",
            "dmf_version": "8.8",
            "timestamp": "2026-03-17T14:32:01",
            "input_hash": "abc123",
            "error_count": 0,
            "warning_count": 0,
        },
    )

    assert "Tool Version:         0.1.0" in rendered
    assert "Template Bundle:      8.8" in rendered
    assert "Workbook Schema:      1.0" in rendered
    assert "Target DMF Version:   8.8" in rendered
    assert "Generated:            2026-03-17T14:32:01" in rendered
    assert "Input Hash:           abc123" in rendered
    assert "Findings:             0 errors, 0 warnings" in rendered


def test_generator_redacts_secrets_from_non_sensitive_artifacts(tmp_path: Path) -> None:
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")
    result = Generator(clock=lambda: "2026-03-17T14:32:01").run(
        workbook_path,
        "8.8",
        tmp_path / "output",
    )

    findings_text = (result.output_dir / "findings.txt").read_text()
    summary_text = (result.output_dir / "summary.md").read_text()
    redacted_text = (result.output_dir / "cli-config-redacted.txt").read_text()

    assert "public" not in findings_text
    assert "enable" not in findings_text
    assert "token" not in findings_text
    assert "public" not in summary_text
    assert "## Provenance" in summary_text
    assert "<REDACTED-snmp_community>" in redacted_text
    assert "<REDACTED-enable_password>" in redacted_text
    assert "<REDACTED-api_token>" in redacted_text


def test_generator_is_deterministic_with_fixed_clock(tmp_path: Path) -> None:
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")
    generator = Generator(clock=lambda: "2026-03-17T14:32:01")

    first = generator.run(workbook_path, "8.8", tmp_path / "output-a")
    second = generator.run(workbook_path, "8.8", tmp_path / "output-b")

    assert (first.output_dir / "cli-config.txt").read_text() == (
        second.output_dir / "cli-config.txt"
    ).read_text()


def test_generator_result_fields_are_populated_for_failure(tmp_path: Path) -> None:
    workbook_path = tmp_path / "corrupt.xlsx"
    workbook_path.write_bytes(b"bad")
    result = Generator(clock=lambda: "2026-03-17T14:32:01").run(
        workbook_path,
        "8.8",
        tmp_path / "output",
    )

    assert result.success is False
    assert result.diagnostic_artifacts
    assert result.config_artifacts == []
    assert result.provenance.error_count >= 1


def test_findings_json_includes_provenance(tmp_path: Path) -> None:
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")
    result = Generator(clock=lambda: "2026-03-17T14:32:01").run(
        workbook_path,
        "8.8",
        tmp_path / "output",
    )

    payload = json.loads((result.output_dir / "findings.json").read_text())

    assert payload["provenance"]["tool_version"] == "0.1.0"
    assert isinstance(payload["findings"], list)
