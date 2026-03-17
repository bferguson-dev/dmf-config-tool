"""Best-practice linter tests."""

from __future__ import annotations

from ipaddress import ip_address

from dmf_tool.core.linters.input.bestpractice import BestPracticeLinter
from dmf_tool.core.models.fabric import (
    Controller,
    Fabric,
    FabricSettings,
    Interface,
    MatchRule,
    Policy,
    Site,
    Switch,
)


def _base_fabric() -> Fabric:
    return Fabric(
        dmf_version="8.8",
        controllers=[
            Controller(
                name="controller-a",
                management_ip=ip_address("10.0.0.10"),
                cluster_name="cluster-a",
                role="active",
                ha_peer="controller-b",
                site_name="site-a",
            ),
            Controller(
                name="controller-b",
                management_ip=ip_address("10.0.0.11"),
                cluster_name="cluster-a",
                role="standby",
                ha_peer="controller-a",
                site_name="site-a",
            ),
        ],
        switches=[
            Switch(
                name="leaf-1",
                management_ip=ip_address("10.0.0.1"),
                role="filter",
                site_name="site-a",
            ),
            Switch(
                name="leaf-2",
                management_ip=ip_address("10.0.0.2"),
                role="delivery",
                site_name="site-a",
            ),
        ],
        interfaces=[
            Interface(
                switch_name="leaf-1",
                name="ethernet1",
                role="filter",
                description="capture",
            ),
            Interface(
                switch_name="leaf-2",
                name="ethernet2",
                role="delivery",
                description="tool",
            ),
        ],
        groups=[],
        policies=[
            Policy(
                name="policy-a",
                priority=100,
                action="forward",
                match_rules=[MatchRule(sequence=10)],
            )
        ],
        service_nodes=[],
        analytics_nodes=[],
        recorder_nodes=[],
        fabric_settings=FabricSettings(fabric_name="fabric-a"),
        sites=[Site(name="site-a")],
    )


def test_bestpractice_linter_passes_clean_fabric() -> None:
    assert BestPracticeLinter().run(_base_fabric()) == []


def test_bestpractice_linter_reports_policy_without_match_rules() -> None:
    fabric = _base_fabric()
    fabric.policies[0].match_rules = []
    assert any(f.code == "BPR001" for f in BestPracticeLinter().run(fabric))


def test_bestpractice_linter_reports_interface_without_description() -> None:
    fabric = _base_fabric()
    fabric.interfaces[0].description = None
    assert any(f.code == "BPR002" for f in BestPracticeLinter().run(fabric))


def test_bestpractice_linter_reports_switch_without_interfaces() -> None:
    fabric = _base_fabric()
    fabric.interfaces = fabric.interfaces[:1]
    assert any(f.code == "BPR003" for f in BestPracticeLinter().run(fabric))


def test_bestpractice_linter_reports_duplicate_switch_ip() -> None:
    fabric = _base_fabric()
    fabric.switches[1].management_ip = ip_address("10.0.0.1")
    assert any(f.code == "BPR004" for f in BestPracticeLinter().run(fabric))


def test_bestpractice_linter_reports_missing_ha_controller() -> None:
    fabric = _base_fabric()
    fabric.controllers = fabric.controllers[:1]
    fabric.controllers[0].ha_peer = None
    assert any(f.code == "BPR005" for f in BestPracticeLinter().run(fabric))


def test_bestpractice_linter_reports_missing_delivery_interfaces() -> None:
    fabric = _base_fabric()
    fabric.interfaces[1].role = "filter"
    assert any(f.code == "BPR006" for f in BestPracticeLinter().run(fabric))
