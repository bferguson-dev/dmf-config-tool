"""Schema linter tests."""

from __future__ import annotations

from dmf_tool.core.linters.input.schema import SchemaLinter
from dmf_tool.core.models.workbook import (
    RawController,
    RawGroup,
    RawInterface,
    RawMatchRule,
    RawPolicy,
    RawSite,
    RawWorkbook,
)


def _valid_workbook() -> RawWorkbook:
    return RawWorkbook(
        dmf_version="8.8",
        workbook_schema_version="1.0",
        controllers=[
            RawController(
                name="controller_1",
                management_ip="10.0.0.10",
                cluster_name="cluster_a",
                site_name="site_a",
            )
        ],
        switches=[],
        interfaces=[
            RawInterface(
                switch_name="leaf-1",
                name="ethernet1",
                role="filter",
                speed="10g",
                vlan_id="100",
            )
        ],
        groups=[RawGroup(name="group_a", role="filter")],
        policies=[
            RawPolicy(
                name="policy_a",
                priority="100",
                match_rules=[RawMatchRule(sequence="10", vlan_id="200")],
            )
        ],
        fabric_settings=None,
        sites=[RawSite(name="site_a")],
    )


def test_schema_linter_passes_valid_workbook() -> None:
    assert SchemaLinter().run(_valid_workbook()) == []


def test_schema_linter_reports_invalid_ip() -> None:
    workbook = _valid_workbook()
    workbook.controllers[0].management_ip = "999.999.0.1"

    findings = SchemaLinter().run(workbook)

    assert findings[0].code == "SCH001"
    assert findings[0].severity.value == "error"
    assert findings[0].suggestion is not None


def test_schema_linter_reports_invalid_interface_name() -> None:
    workbook = _valid_workbook()
    workbook.interfaces[0].name = "ethernet/1"

    findings = SchemaLinter().run(workbook)

    assert any(finding.code == "SCH002" for finding in findings)


def test_schema_linter_reports_invalid_role() -> None:
    workbook = _valid_workbook()
    workbook.interfaces[0].role = "mirror"

    findings = SchemaLinter().run(workbook)

    assert any(finding.code == "SCH003" for finding in findings)


def test_schema_linter_reports_invalid_priority() -> None:
    workbook = _valid_workbook()
    workbook.policies[0].priority = "0"

    findings = SchemaLinter().run(workbook)

    assert any(finding.code == "SCH004" for finding in findings)


def test_schema_linter_reports_invalid_vlan() -> None:
    workbook = _valid_workbook()
    workbook.interfaces[0].vlan_id = "5000"

    findings = SchemaLinter().run(workbook)

    assert any(finding.code == "SCH005" for finding in findings)


def test_schema_linter_reports_invalid_speed() -> None:
    workbook = _valid_workbook()
    workbook.interfaces[0].speed = "12g"

    findings = SchemaLinter().run(workbook)

    assert any(finding.code == "SCH006" for finding in findings)


def test_schema_linter_reports_blank_required_field() -> None:
    workbook = _valid_workbook()
    workbook.controllers[0].cluster_name = ""

    findings = SchemaLinter().run(workbook)

    assert any(finding.code == "SCH007" for finding in findings)


def test_schema_linter_reports_invalid_identifier() -> None:
    workbook = _valid_workbook()
    workbook.sites[0].name = "site a"

    findings = SchemaLinter().run(workbook)

    assert any(finding.code == "SCH008" for finding in findings)
