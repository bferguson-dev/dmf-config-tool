"""Relational linter tests."""

from __future__ import annotations

from dmf_tool.core.linters.input.relational import RelationalLinter
from dmf_tool.core.models.workbook import (
    RawAnalyticsNode,
    RawController,
    RawGroup,
    RawGroupMember,
    RawInterface,
    RawPolicy,
    RawRecorderNode,
    RawServiceNode,
    RawSwitch,
    RawWorkbook,
)


def _valid_workbook() -> RawWorkbook:
    return RawWorkbook(
        dmf_version="8.8",
        workbook_schema_version="1.0",
        controllers=[
            RawController(name="controller-a", ha_peer="controller-b"),
            RawController(name="controller-b", ha_peer="controller-a"),
        ],
        switches=[RawSwitch(name="leaf-1"), RawSwitch(name="leaf-2")],
        interfaces=[
            RawInterface(switch_name="leaf-1", name="ethernet1"),
            RawInterface(switch_name="leaf-2", name="ethernet2"),
        ],
        groups=[
            RawGroup(
                name="group-a",
                members=[
                    RawGroupMember(
                        switch_name="leaf-1",
                        interface_name="ethernet1",
                    )
                ],
            )
        ],
        policies=[
            RawPolicy(
                name="policy-a",
                source_interface="leaf-1:ethernet1",
                delivery_interface="leaf-2:ethernet2",
                source_group="group-a",
                delivery_group="group-a",
            )
        ],
        service_nodes=[
            RawServiceNode(
                name="service-a",
                switch_name="leaf-1",
                interface_name="ethernet1",
            )
        ],
        analytics_nodes=[
            RawAnalyticsNode(
                name="analytics-a",
                switch_name="leaf-1",
                interface_name="ethernet1",
            )
        ],
        recorder_nodes=[
            RawRecorderNode(
                name="recorder-a",
                switch_name="leaf-1",
                interface_name="ethernet1",
            )
        ],
        fabric_settings=None,
        sites=[],
    )


def test_relational_linter_passes_valid_workbook() -> None:
    assert RelationalLinter().run(_valid_workbook()) == []


def test_relational_linter_reports_missing_policy_interface() -> None:
    workbook = _valid_workbook()
    workbook.policies[0].source_interface = "leaf-1:missing"

    findings = RelationalLinter().run(workbook)

    assert any(finding.code == "REL001" for finding in findings)


def test_relational_linter_reports_missing_group_member_interface() -> None:
    workbook = _valid_workbook()
    workbook.groups[0].members[0].interface_name = "missing"

    findings = RelationalLinter().run(workbook)

    assert any(finding.code == "REL002" for finding in findings)


def test_relational_linter_reports_missing_switch_reference() -> None:
    workbook = _valid_workbook()
    workbook.interfaces[0].switch_name = "missing"

    findings = RelationalLinter().run(workbook)

    assert any(finding.code == "REL003" for finding in findings)


def test_relational_linter_reports_missing_group_reference() -> None:
    workbook = _valid_workbook()
    workbook.policies[0].source_group = "missing"

    findings = RelationalLinter().run(workbook)

    assert any(finding.code == "REL004" for finding in findings)


def test_relational_linter_reports_invalid_node_reference() -> None:
    workbook = _valid_workbook()
    workbook.service_nodes[0].interface_name = "missing"

    findings = RelationalLinter().run(workbook)

    assert any(finding.code == "REL005" for finding in findings)


def test_relational_linter_reports_invalid_ha_peer() -> None:
    workbook = _valid_workbook()
    workbook.controllers[0].ha_peer = "missing"

    findings = RelationalLinter().run(workbook)

    assert any(finding.code == "REL006" for finding in findings)
