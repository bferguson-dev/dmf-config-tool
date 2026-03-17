"""Semantic input linter."""

from __future__ import annotations

import importlib
from collections import Counter, defaultdict
from collections.abc import Callable

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity
from dmf_tool.core.models.fabric import Fabric
from dmf_tool.core.versions.base import VersionBundle


class SemanticLinter(BaseLinter):
    """Validate semantic DMF rules against the normalized fabric."""

    def __init__(self, version_bundle: VersionBundle) -> None:
        self._version_bundle = version_bundle

    def run(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        findings.extend(self._check_policy_roles(fabric))
        findings.extend(self._check_group_roles(fabric))
        findings.extend(self._check_conflicting_interface_roles(fabric))
        findings.extend(self._check_ha_completeness(fabric))
        findings.extend(self._check_capacity_limits(fabric))
        findings.extend(self._check_unsupported_features(fabric))

        for rule in self._load_bundle_rules():
            findings.extend(rule(fabric))

        return findings

    def _load_bundle_rules(self) -> tuple[Callable[[Fabric], list[LintResult]], ...]:
        rules_module = importlib.import_module(
            f"{self._version_bundle.__class__.__module__}.rules"
        )
        return rules_module.build_semantic_rules()

    def _check_policy_roles(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        interfaces = {
            f"{interface.switch_name}:{interface.name}": interface
            for interface in fabric.interfaces
        }
        groups = {group.name: group for group in fabric.groups}
        for policy in fabric.policies:
            if policy.source_interface:
                source = interfaces.get(policy.source_interface)
                if source is not None and source.role not in {"filter", "both"}:
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="SEM001",
                            location="policies",
                            field="source_interface",
                            value=policy.source_interface,
                            message="Policy source interface must be filter-capable.",
                            suggestion="Use a filter or both-role source interface.",
                        )
                    )
            if policy.delivery_interface:
                delivery = interfaces.get(policy.delivery_interface)
                if delivery is not None and delivery.role not in {"delivery", "both"}:
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="SEM001",
                            location="policies",
                            field="delivery_interface",
                            value=policy.delivery_interface,
                            message=(
                                "Policy delivery interface must be delivery-capable."
                            ),
                            suggestion=(
                                "Use a delivery or both-role delivery interface."
                            ),
                        )
                    )
            if policy.source_group:
                group = groups.get(policy.source_group)
                if group is not None and group.role not in {"filter", "both"}:
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="SEM001",
                            location="policies",
                            field="source_group",
                            value=policy.source_group,
                            message="Policy source group must be filter-capable.",
                            suggestion="Use a filter or both-role interface group.",
                        )
                    )
            if policy.delivery_group:
                group = groups.get(policy.delivery_group)
                if group is not None and group.role not in {"delivery", "both"}:
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="SEM001",
                            location="policies",
                            field="delivery_group",
                            value=policy.delivery_group,
                            message="Policy delivery group must be delivery-capable.",
                            suggestion="Use a delivery or both-role interface group.",
                        )
                    )
        return findings

    def _check_group_roles(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        interfaces = {
            f"{interface.switch_name}:{interface.name}": interface
            for interface in fabric.interfaces
        }
        for group in fabric.groups:
            member_roles = {
                interfaces[member].role
                for member in group.members
                if member in interfaces
            }
            if len(member_roles) > 1 or (
                member_roles and group.role not in member_roles and group.role != "both"
            ):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SEM002",
                        location="groups",
                        field="role",
                        value=group.name,
                        message="Interface group members must be role-homogeneous.",
                        suggestion=(
                            "Keep all group members on the same compatible role."
                        ),
                    )
                )
        return findings

    def _check_conflicting_interface_roles(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        roles_by_key: dict[str, set[str]] = defaultdict(set)
        for interface in fabric.interfaces:
            roles_by_key[f"{interface.switch_name}:{interface.name}"].add(
                interface.role
            )
        for interface_key, roles in roles_by_key.items():
            if len(roles) > 1:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SEM003",
                        location="interfaces",
                        field="role",
                        value=interface_key,
                        message="Physical interface has conflicting roles.",
                        suggestion="Define one role per physical interface.",
                    )
                )
        return findings

    def _check_ha_completeness(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        controllers = {controller.name: controller for controller in fabric.controllers}
        ha_controllers = [
            controller for controller in fabric.controllers if controller.ha_peer
        ]
        if ha_controllers and len(controllers) != 2:
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="SEM004",
                    location="controllers",
                    field="ha_peer",
                    value=str(len(controllers)),
                    message="HA controller definitions must be complete and symmetric.",
                    suggestion=(
                        "Define exactly two controllers that reference each other."
                    ),
                )
            )
            return findings

        for controller in ha_controllers:
            peer = controllers.get(controller.ha_peer or "")
            if peer is None or peer.ha_peer != controller.name:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SEM004",
                        location="controllers",
                        field="ha_peer",
                        value=controller.ha_peer,
                        message="HA controller definitions must be symmetric.",
                        suggestion=(
                            "Make each controller reference the other as its HA peer."
                        ),
                    )
                )
        return findings

    def _check_capacity_limits(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        counts = {
            "max_policies": len(fabric.policies),
            "max_groups": len(fabric.groups),
            "max_switches": len(fabric.switches),
        }
        interfaces_per_switch = Counter(
            interface.switch_name for interface in fabric.interfaces
        )
        for switch_name, count in interfaces_per_switch.items():
            if not self._version_bundle.check_limit("max_interfaces_per_switch", count):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SEM005",
                        location="interfaces",
                        field="switch_name",
                        value=switch_name,
                        message=(
                            "Switch exceeds the interface capacity "
                            "for this DMF version."
                        ),
                        suggestion=(
                            "Reduce interfaces or target a version with higher limits."
                        ),
                    )
                )
        for limit_name, count in counts.items():
            if not self._version_bundle.check_limit(limit_name, count):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SEM005",
                        location="fabric",
                        field=limit_name,
                        value=str(count),
                        message="Fabric exceeds a version-specific capacity limit.",
                        suggestion=(
                            "Reduce object count or target a version "
                            "with higher limits."
                        ),
                    )
                )
        return findings

    def _check_unsupported_features(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        feature_map = {
            "analytics_node": bool(fabric.analytics_nodes),
            "service_node": bool(fabric.service_nodes),
            "recorder_node": bool(fabric.recorder_nodes),
            "ha_controller": any(
                controller.ha_peer for controller in fabric.controllers
            ),
            "snmp": fabric.fabric_settings.snmp_community is not None,
            "ntp": fabric.fabric_settings.ntp_server is not None,
            "syslog": fabric.fabric_settings.syslog_server is not None,
        }
        for feature_name, in_use in feature_map.items():
            if in_use and not self._version_bundle.supports_feature(feature_name):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SEM006",
                        location="fabric",
                        field="feature",
                        value=feature_name,
                        message=(
                            "Fabric uses a feature unsupported by "
                            "the target DMF version."
                        ),
                        suggestion=(
                            "Remove the feature or target a version that supports it."
                        ),
                    )
                )
        return findings
