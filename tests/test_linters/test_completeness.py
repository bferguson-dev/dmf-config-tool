"""Output completeness tests."""

from __future__ import annotations

from ipaddress import ip_address

from dmf_tool.core.linters.output.completeness import CompletenessLinter
from dmf_tool.core.models.fabric import (
    Fabric,
    FabricSettings,
    Interface,
    Policy,
    Switch,
)


def _sample_fabric() -> Fabric:
    return Fabric(
        dmf_version="8.8",
        switches=[
            Switch(
                name="leaf-1",
                management_ip=ip_address("10.0.0.1"),
                role="filter",
                site_name="site-a",
            )
        ],
        interfaces=[Interface(switch_name="leaf-1", name="ethernet1", role="filter")],
        policies=[Policy(name="policy-a", priority=100, action="forward")],
        fabric_settings=FabricSettings(fabric_name="fabric-a"),
    )


def test_completeness_linter_passes_clean_output() -> None:
    rendered = """
! BEGIN SWITCHES
switch leaf-1
exit
! END SWITCHES
! BEGIN INTERFACES
interface leaf-1 ethernet1
exit
! END INTERFACES
! BEGIN FABRIC SETTINGS
fabric-settings fabric-a
exit
! END FABRIC SETTINGS
! BEGIN POLICIES
policy policy-a
exit
! END POLICIES
""".strip()
    assert CompletenessLinter().run(_sample_fabric(), rendered) == []


def test_completeness_linter_reports_missing_section() -> None:
    findings = CompletenessLinter().run(_sample_fabric(), "! BEGIN SWITCHES\n")
    assert any(finding.code == "OUT004" for finding in findings)


def test_completeness_linter_reports_empty_switch_block() -> None:
    fabric = _sample_fabric()
    fabric.interfaces = []
    rendered = "! BEGIN SWITCHES\nswitch leaf-1\nexit\n"
    findings = CompletenessLinter().run(fabric, rendered)
    assert any(finding.code == "OUT010" for finding in findings)


def test_completeness_linter_reports_duplicate_blocks() -> None:
    rendered = """
! BEGIN SWITCHES
switch leaf-1
switch leaf-1
! END SWITCHES
! BEGIN INTERFACES
interface leaf-1 ethernet1
! END INTERFACES
! BEGIN FABRIC SETTINGS
fabric-settings fabric-a
! END FABRIC SETTINGS
! BEGIN POLICIES
policy policy-a
! END POLICIES
""".strip()
    findings = CompletenessLinter().run(_sample_fabric(), rendered)
    assert any(finding.code == "OUT010" for finding in findings)


def test_completeness_linter_reports_ordering_issues() -> None:
    rendered = """
! BEGIN POLICIES
policy policy-a
! END POLICIES
! BEGIN INTERFACES
interface leaf-1 ethernet1
! END INTERFACES
! BEGIN SWITCHES
switch leaf-1
! END SWITCHES
! BEGIN FABRIC SETTINGS
fabric-settings fabric-a
! END FABRIC SETTINGS
""".strip()
    findings = CompletenessLinter().run(_sample_fabric(), rendered)
    assert any(finding.value == "interfaces-before-switches" for finding in findings)
    assert any(finding.value == "policies-before-interfaces" for finding in findings)
