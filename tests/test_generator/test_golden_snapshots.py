"""Golden snapshot tests."""

from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path

from dmf_tool.core.models.fabric import (
    AnalyticsNode,
    Controller,
    Fabric,
    FabricSettings,
    Interface,
    InterfaceGroup,
    MatchRule,
    Policy,
    RecorderNode,
    ServiceNode,
    Site,
    Switch,
)
from dmf_tool.core.rendering import render_config
from dmf_tool.core.versions.dmf_8_6 import BUNDLE as DMF86_BUNDLE
from dmf_tool.core.versions.dmf_8_7 import BUNDLE as DMF87_BUNDLE
from dmf_tool.core.versions.dmf_8_8 import BUNDLE as DMF88_BUNDLE


def _sample_fabric() -> Fabric:
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
                description="primary",
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
                model="7050",
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
                speed="10g",
                vlan_id=100,
            ),
            Interface(
                switch_name="leaf-2",
                name="ethernet2",
                role="delivery",
                description="tool",
                speed="10g",
            ),
        ],
        groups=[
            InterfaceGroup(
                name="collectors",
                role="filter",
                members=["leaf-1:ethernet1"],
            )
        ],
        policies=[
            Policy(
                name="policy-a",
                priority=100,
                source_interface="leaf-1:ethernet1",
                delivery_interface="leaf-2:ethernet2",
                action="forward",
                description="mirror traffic",
                match_rules=[
                    MatchRule(
                        sequence=10,
                        source_ip="10.0.0.1",
                        destination_ip="10.0.0.2",
                        source_port=80,
                        destination_port=443,
                        vlan_id=100,
                        protocol="tcp",
                    )
                ],
            )
        ],
        service_nodes=[
            ServiceNode(
                name="service-a",
                switch_name="leaf-1",
                interface_name="ethernet1",
                management_ip=ip_address("10.0.0.20"),
            )
        ],
        analytics_nodes=[
            AnalyticsNode(
                name="analytics-a",
                switch_name="leaf-1",
                interface_name="ethernet1",
                management_ip=ip_address("10.0.0.21"),
            )
        ],
        recorder_nodes=[
            RecorderNode(
                name="recorder-a",
                switch_name="leaf-1",
                interface_name="ethernet1",
                management_ip=ip_address("10.0.0.22"),
            )
        ],
        fabric_settings=FabricSettings.model_validate(
            {
                "fabric_name": "fabric-a",
                "syslog_server": ip_address("10.0.0.30"),
                "ntp_server": ip_address("10.0.0.31"),
                "snmp_community": "public",
                "enable_password": "generated-enable",
                "api_token": "generated-token",
            }
        ),
        sites=[Site(name="site-a")],
    )


def _provenance() -> dict[str, object]:
    return {
        "tool_version": "0.1.0",
        "template_bundle_version": "8.8",
        "workbook_schema_version": "1.0",
        "dmf_version": "8.8",
        "timestamp": "2026-03-17T14:32:01",
        "input_hash": "abc123",
        "error_count": 0,
        "warning_count": 1,
    }


def _body_only(rendered: str) -> str:
    for marker in ("! BEGIN CONTROLLERS", "! BEGIN SWITCHES"):
        index = rendered.find(marker)
        if index != -1:
            return rendered[index:].strip() + "\n"
    raise AssertionError("Rendered output did not include a section marker.")


def test_all_bundle_templates_render() -> None:
    fabric = _sample_fabric()
    provenance = _provenance()
    for bundle in (DMF86_BUNDLE, DMF87_BUNDLE, DMF88_BUNDLE):
        rendered = render_config(bundle, fabric, provenance)
        assert "policy policy-a" in rendered


def test_config_body_matches_golden_snapshot() -> None:
    rendered = render_config(DMF88_BUNDLE, _sample_fabric(), _provenance())
    golden_path = Path("tests/fixtures/golden/valid_complete_88_cli.txt")
    assert _body_only(rendered) == golden_path.read_text()


def test_identical_fabric_and_clock_are_deterministic() -> None:
    first = render_config(DMF88_BUNDLE, _sample_fabric(), _provenance())
    second = render_config(DMF88_BUNDLE, _sample_fabric(), _provenance())
    assert first == second
