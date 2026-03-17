"""Semantic linter tests."""

from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path

import pytest

from dmf_tool.core.linters.input.semantic import SemanticLinter
from dmf_tool.core.models.fabric import (
    Controller,
    Fabric,
    FabricSettings,
    Interface,
    InterfaceGroup,
    Policy,
    Site,
    Switch,
)
from dmf_tool.core.versions.base import VersionBundle
from dmf_tool.core.versions.dmf_8_6 import BUNDLE as DMF86_BUNDLE
from dmf_tool.core.versions.dmf_8_7 import BUNDLE as DMF87_BUNDLE
from dmf_tool.core.versions.dmf_8_8 import BUNDLE as DMF88_BUNDLE
from dmf_tool.core.versions.registry import VersionRegistry


def test_registry_returns_expected_bundle() -> None:
    """Known DMF versions should resolve to their bundle."""
    registry = VersionRegistry()

    assert registry.get("8.8") is DMF88_BUNDLE
    assert registry.get("8.7") is DMF87_BUNDLE
    assert registry.get("8.6") is DMF86_BUNDLE


def test_registry_raises_for_unknown_versions() -> None:
    """Unknown versions should fail fast."""
    registry = VersionRegistry()

    with pytest.raises(ValueError, match="Unsupported DMF version"):
        registry.get("9.0")


@pytest.mark.parametrize("bundle", [DMF86_BUNDLE, DMF87_BUNDLE, DMF88_BUNDLE])
def test_each_bundle_exposes_the_expected_interface(bundle: VersionBundle) -> None:
    """Every bundle should satisfy the abstract interface contract."""
    assert bundle.version_string in {"8.6", "8.7", "8.8"}
    assert isinstance(bundle.supported_features, frozenset)
    assert isinstance(bundle.limits, dict)
    assert bundle.minimum_workbook_schema_version == "1.0"
    assert bundle.template_dir == Path(bundle.template_dir)


def test_feature_matrix_lookups_are_version_specific() -> None:
    """Feature support should vary by version where expected."""
    assert DMF88_BUNDLE.supports_feature("analytics_node") is True
    assert DMF87_BUNDLE.supports_feature("analytics_node") is False
    assert DMF86_BUNDLE.supports_feature("recorder_node") is False


def test_capacity_limit_checks_use_bundle_values() -> None:
    """Bundles should evaluate capacity checks against their own limits."""
    assert DMF88_BUNDLE.check_limit("max_policies", 1024) is True
    assert DMF88_BUNDLE.check_limit("max_policies", 1025) is False
    assert DMF86_BUNDLE.check_limit("max_switches", 64) is True
    assert DMF86_BUNDLE.check_limit("max_switches", 65) is False


def test_bundles_are_not_interchangeable() -> None:
    """Each version bundle should remain distinct."""
    registry = VersionRegistry()

    assert registry.supported_versions() == ["8.6", "8.7", "8.8"]
    assert registry.is_supported("8.8") is True
    assert registry.is_supported("8.5") is False
    assert DMF86_BUNDLE is not DMF87_BUNDLE
    assert DMF87_BUNDLE is not DMF88_BUNDLE


def _valid_fabric() -> Fabric:
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
            Interface(switch_name="leaf-1", name="ethernet1", role="filter"),
            Interface(switch_name="leaf-2", name="ethernet2", role="delivery"),
        ],
        groups=[
            InterfaceGroup(
                name="group-filter",
                role="filter",
                members=["leaf-1:ethernet1"],
            ),
            InterfaceGroup(
                name="group-delivery",
                role="delivery",
                members=["leaf-2:ethernet2"],
            ),
        ],
        policies=[
            Policy(
                name="policy-a",
                priority=100,
                source_interface="leaf-1:ethernet1",
                delivery_interface="leaf-2:ethernet2",
                action="forward",
            )
        ],
        service_nodes=[],
        analytics_nodes=[],
        recorder_nodes=[],
        fabric_settings=FabricSettings(fabric_name="fabric-a"),
        sites=[Site(name="site-a")],
    )


def test_semantic_linter_passes_valid_fabric() -> None:
    assert SemanticLinter(DMF88_BUNDLE).run(_valid_fabric()) == []


def test_semantic_linter_reports_role_incompatibility() -> None:
    fabric = _valid_fabric()
    fabric.interfaces[0].role = "delivery"

    findings = SemanticLinter(DMF88_BUNDLE).run(fabric)

    assert any(finding.code == "SEM001" for finding in findings)


def test_semantic_linter_reports_group_role_mismatch() -> None:
    fabric = _valid_fabric()
    fabric.groups[0].members.append("leaf-2:ethernet2")

    findings = SemanticLinter(DMF88_BUNDLE).run(fabric)

    assert any(finding.code == "SEM002" for finding in findings)


def test_semantic_linter_reports_conflicting_interface_roles() -> None:
    fabric = _valid_fabric()
    fabric.interfaces.append(
        Interface(switch_name="leaf-1", name="ethernet1", role="delivery")
    )

    findings = SemanticLinter(DMF88_BUNDLE).run(fabric)

    assert any(finding.code == "SEM003" for finding in findings)


def test_semantic_linter_reports_incomplete_ha_pair() -> None:
    fabric = _valid_fabric()
    fabric.controllers = fabric.controllers[:1]

    findings = SemanticLinter(DMF88_BUNDLE).run(fabric)

    assert any(finding.code == "SEM004" for finding in findings)


def test_semantic_linter_reports_capacity_limit_violation() -> None:
    fabric = _valid_fabric()
    fabric.policies = [
        Policy(name=f"policy-{index}", priority=index + 1, action="forward")
        for index in range(DMF86_BUNDLE.limits["max_policies"] + 1)
    ]

    findings = SemanticLinter(DMF86_BUNDLE).run(fabric)

    assert any(finding.code == "SEM005" for finding in findings)


def test_semantic_linter_reports_unsupported_feature() -> None:
    fabric = _valid_fabric()
    fabric.analytics_nodes.append(
        type("AnalyticsNodeShim", (), {"name": "shim"})()  # type: ignore[list-item]
    )

    findings = SemanticLinter(DMF87_BUNDLE).run(fabric)

    assert any(finding.code == "SEM006" for finding in findings)


def test_semantic_linter_loads_bundle_rules() -> None:
    findings = SemanticLinter(DMF88_BUNDLE).run(_valid_fabric())

    assert findings == []
