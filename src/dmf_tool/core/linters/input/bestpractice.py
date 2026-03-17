"""Best-practice input linter."""

from __future__ import annotations

from collections import Counter

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity
from dmf_tool.core.models.fabric import Fabric


class BestPracticeLinter(BaseLinter):
    """Warn on risky but technically valid fabric patterns."""

    def run(self, fabric: Fabric) -> list[LintResult]:
        findings: list[LintResult] = []
        all_traffic_message = "Policy has no match rules and will forward all traffic."
        unused_switch_suggestion = (
            "Assign interfaces or remove the unused switch definition."
        )

        for policy in fabric.policies:
            if not policy.match_rules:
                findings.append(
                    LintResult(
                        severity=Severity.WARNING,
                        code="BPR001",
                        location="policies",
                        field="match_rules",
                        value=policy.name,
                        message=all_traffic_message,
                        suggestion="Add one or more match rules to scope traffic.",
                    )
                )

        for interface in fabric.interfaces:
            if not interface.description:
                findings.append(
                    LintResult(
                        severity=Severity.WARNING,
                        code="BPR002",
                        location="interfaces",
                        field="description",
                        value=interface.name,
                        message="Interface does not have a description.",
                        suggestion="Add a description to clarify interface purpose.",
                    )
                )

        switch_interface_counts = Counter(
            interface.switch_name for interface in fabric.interfaces
        )
        for switch in fabric.switches:
            if switch_interface_counts[switch.name] == 0:
                findings.append(
                    LintResult(
                        severity=Severity.WARNING,
                        code="BPR003",
                        location="switches",
                        field="name",
                        value=switch.name,
                        message="Switch has no assigned interfaces.",
                        suggestion=unused_switch_suggestion,
                    )
                )

        ip_counts = Counter(str(switch.management_ip) for switch in fabric.switches)
        for ip_address, count in ip_counts.items():
            if count > 1:
                findings.append(
                    LintResult(
                        severity=Severity.WARNING,
                        code="BPR004",
                        location="switches",
                        field="management_ip",
                        value=ip_address,
                        message="Duplicate management IP detected across switches.",
                        suggestion="Use a unique management IP per switch.",
                    )
                )

        if len(fabric.controllers) < 2 or not any(
            controller.ha_peer for controller in fabric.controllers
        ):
            findings.append(
                LintResult(
                    severity=Severity.WARNING,
                    code="BPR005",
                    location="controllers",
                    field="ha_peer",
                    value=str(len(fabric.controllers)),
                    message="HA controller configuration is missing.",
                    suggestion="Define an HA controller pair for higher availability.",
                )
            )

        if not any(
            interface.role in {"delivery", "both"} for interface in fabric.interfaces
        ):
            findings.append(
                LintResult(
                    severity=Severity.WARNING,
                    code="BPR006",
                    location="interfaces",
                    field="role",
                    value=None,
                    message="No delivery interfaces are defined.",
                    suggestion="Define one or more delivery-capable interfaces.",
                )
            )

        return findings
