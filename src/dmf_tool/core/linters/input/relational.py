"""Relational input linter."""

from __future__ import annotations

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity
from dmf_tool.core.models.workbook import RawWorkbook


def _interface_key(switch_name: str | None, interface_name: str | None) -> str:
    return f"{switch_name or ''}:{interface_name or ''}"


class RelationalLinter(BaseLinter):
    """Validate raw workbook cross-references."""

    def run(self, workbook: RawWorkbook) -> list[LintResult]:
        findings: list[LintResult] = []
        switch_names = {switch.name for switch in workbook.switches if switch.name}
        interface_keys = {
            _interface_key(interface.switch_name, interface.name)
            for interface in workbook.interfaces
            if interface.switch_name and interface.name
        }
        group_names = {group.name for group in workbook.groups if group.name}
        controller_names = {
            controller.name for controller in workbook.controllers if controller.name
        }

        for policy in workbook.policies:
            if (
                policy.source_interface
                and policy.source_interface not in interface_keys
            ):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="REL001",
                        location="policies tab",
                        field="source_interface",
                        value=policy.source_interface,
                        message="Policy references an interface that does not exist.",
                        suggestion=(
                            "Reference an interface defined in the interfaces tab."
                        ),
                    )
                )
            if (
                policy.delivery_interface
                and policy.delivery_interface not in interface_keys
            ):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="REL001",
                        location="policies tab",
                        field="delivery_interface",
                        value=policy.delivery_interface,
                        message="Policy references an interface that does not exist.",
                        suggestion=(
                            "Reference an interface defined in the interfaces tab."
                        ),
                    )
                )
            if policy.source_group and policy.source_group not in group_names:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="REL004",
                        location="policies tab",
                        field="source_group",
                        value=policy.source_group,
                        message="Policy references a group that does not exist.",
                        suggestion=(
                            "Reference an interface group defined in the groups tab."
                        ),
                    )
                )
            if policy.delivery_group and policy.delivery_group not in group_names:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="REL004",
                        location="policies tab",
                        field="delivery_group",
                        value=policy.delivery_group,
                        message="Policy references a group that does not exist.",
                        suggestion=(
                            "Reference an interface group defined in the groups tab."
                        ),
                    )
                )

        for group in workbook.groups:
            for member in group.members:
                member_key = _interface_key(member.switch_name, member.interface_name)
                if member_key not in interface_keys:
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="REL002",
                            location="group_members tab",
                            field="interface_name",
                            value=member_key,
                            message=(
                                "Group member references an interface "
                                "that does not exist."
                            ),
                            suggestion=(
                                "Reference an interface defined in the interfaces tab."
                            ),
                        )
                    )

        for interface in workbook.interfaces:
            if interface.switch_name and interface.switch_name not in switch_names:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="REL003",
                        location="interfaces tab",
                        field="switch_name",
                        value=interface.switch_name,
                        message="Interface references a switch that does not exist.",
                        suggestion="Reference a switch defined in the switches tab.",
                    )
                )

        for node_type, nodes in (
            ("service_nodes", workbook.service_nodes),
            ("analytics_nodes", workbook.analytics_nodes),
            ("recorder_nodes", workbook.recorder_nodes),
        ):
            for node in nodes:
                member_key = _interface_key(node.switch_name, node.interface_name)
                if (
                    node.switch_name not in switch_names
                    or member_key not in interface_keys
                ):
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="REL005",
                            location=f"{node_type} tab",
                            field="interface_name",
                            value=member_key,
                            message=(
                                "Node references a switch/interface pair "
                                "that does not exist."
                            ),
                            suggestion=(
                                "Reference a real switch and interface combination."
                            ),
                        )
                    )

        for controller in workbook.controllers:
            if controller.ha_peer and controller.ha_peer not in controller_names:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="REL006",
                        location="controllers tab",
                        field="ha_peer",
                        value=controller.ha_peer,
                        message="HA peer reference does not resolve to a controller.",
                        suggestion=(
                            "Reference another controller defined "
                            "in the controllers tab."
                        ),
                    )
                )

        return findings
