"""Artifact output tests."""

from __future__ import annotations

import pytest
from jinja2 import UndefinedError

from dmf_tool.core.models.fabric import Fabric, FabricSettings
from dmf_tool.core.rendering import build_environment, render_config
from dmf_tool.core.versions.dmf_8_8 import BUNDLE as DMF88_BUNDLE


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
