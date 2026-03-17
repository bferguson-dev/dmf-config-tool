"""Output completeness linter."""

from __future__ import annotations

import re

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity
from dmf_tool.core.models.fabric import Fabric


def _count_block_occurrences(rendered_text: str, prefix: str, name: str) -> int:
    pattern = re.compile(rf"^{re.escape(prefix)} {re.escape(name)}$", re.MULTILINE)
    return len(pattern.findall(rendered_text))


class CompletenessLinter(BaseLinter):
    """Verify expected output sections are present and ordered."""

    def run(self, fabric: Fabric, rendered_text: str) -> list[LintResult]:
        findings: list[LintResult] = []

        if fabric.switches and "! BEGIN SWITCHES" not in rendered_text:
            findings.append(self._missing_section("OUT003", "switches"))
        if fabric.interfaces and "! BEGIN INTERFACES" not in rendered_text:
            findings.append(self._missing_section("OUT004", "interfaces"))
        if fabric.policies and "! BEGIN POLICIES" not in rendered_text:
            findings.append(self._missing_section("OUT005", "policies"))
        if fabric.groups and "! BEGIN GROUPS" not in rendered_text:
            findings.append(self._missing_section("OUT006", "groups"))
        if fabric.service_nodes and "! BEGIN SERVICE NODES" not in rendered_text:
            findings.append(self._missing_section("OUT007", "service nodes"))
        if fabric.analytics_nodes and "! BEGIN ANALYTICS NODES" not in rendered_text:
            findings.append(self._missing_section("OUT008", "analytics nodes"))
        if fabric.recorder_nodes and "! BEGIN RECORDER NODES" not in rendered_text:
            findings.append(self._missing_section("OUT009", "recorder nodes"))

        findings.extend(self._check_switch_blocks(fabric, rendered_text))
        findings.extend(self._check_policy_blocks(fabric, rendered_text))
        findings.extend(self._check_duplicate_blocks(fabric, rendered_text))
        findings.extend(self._check_section_order(rendered_text))

        return findings

    def _missing_section(self, code: str, section_name: str) -> LintResult:
        return LintResult(
            severity=Severity.ERROR,
            code=code,
            location="rendered output",
            field="section",
            value=section_name,
            message="Rendered output is missing an expected section.",
            suggestion="Ensure the relevant template section is rendered.",
        )

    def _check_switch_blocks(
        self,
        fabric: Fabric,
        rendered_text: str,
    ) -> list[LintResult]:
        findings: list[LintResult] = []
        interface_switches = {interface.switch_name for interface in fabric.interfaces}
        for switch in fabric.switches:
            if (
                switch.name not in interface_switches
                and _count_block_occurrences(rendered_text, "switch", switch.name) >= 1
            ):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="OUT010",
                        location="rendered output",
                        field="switch",
                        value=switch.name,
                        message="Rendered output contains an empty switch block.",
                        suggestion=(
                            "Render switch blocks only when they have interfaces."
                        ),
                    )
                )
        return findings

    def _check_policy_blocks(
        self,
        fabric: Fabric,
        rendered_text: str,
    ) -> list[LintResult]:
        findings: list[LintResult] = []
        for policy in fabric.policies:
            if _count_block_occurrences(rendered_text, "policy", policy.name) == 0:
                findings.append(
                    self._missing_section("OUT005", f"policy {policy.name}")
                )
        return findings

    def _check_duplicate_blocks(
        self,
        fabric: Fabric,
        rendered_text: str,
    ) -> list[LintResult]:
        findings: list[LintResult] = []
        for switch in fabric.switches:
            if _count_block_occurrences(rendered_text, "switch", switch.name) > 1:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="OUT010",
                        location="rendered output",
                        field="switch",
                        value=switch.name,
                        message="Rendered output contains duplicate switch blocks.",
                        suggestion="Render each switch block exactly once.",
                    )
                )
        for policy in fabric.policies:
            if _count_block_occurrences(rendered_text, "policy", policy.name) > 1:
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="OUT010",
                        location="rendered output",
                        field="policy",
                        value=policy.name,
                        message="Rendered output contains duplicate policy blocks.",
                        suggestion="Render each policy block exactly once.",
                    )
                )
        return findings

    def _check_section_order(self, rendered_text: str) -> list[LintResult]:
        findings: list[LintResult] = []
        switches_index = rendered_text.find("! BEGIN SWITCHES")
        interfaces_index = rendered_text.find("! BEGIN INTERFACES")
        policies_index = rendered_text.find("! BEGIN POLICIES")
        if (
            switches_index != -1
            and interfaces_index != -1
            and interfaces_index < switches_index
        ):
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="OUT010",
                    location="rendered output",
                    field="section_order",
                    value="interfaces-before-switches",
                    message="Rendered output has interfaces before switches.",
                    suggestion="Render switches before interfaces.",
                )
            )
        if (
            interfaces_index != -1
            and policies_index != -1
            and policies_index < interfaces_index
        ):
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="OUT010",
                    location="rendered output",
                    field="section_order",
                    value="policies-before-interfaces",
                    message="Rendered output has policies before interfaces.",
                    suggestion="Render interfaces before policies.",
                )
            )
        return findings
