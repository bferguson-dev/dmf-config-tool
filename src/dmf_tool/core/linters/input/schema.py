"""Schema input linter."""

from __future__ import annotations

import ipaddress
import re

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity
from dmf_tool.core.models.workbook import RawWorkbook

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
IP_PATTERN = re.compile(r"^[0-9A-Fa-f:.]+$")
SUPPORTED_SPEEDS = frozenset({"1g", "10g", "25g", "40g", "100g"})
SUPPORTED_ROLES = frozenset({"filter", "delivery", "both"})


def _has_text(value: str | None) -> bool:
    return value is not None and bool(value.strip())


class SchemaLinter(BaseLinter):
    """Validate raw field syntax and required values."""

    def run(self, workbook: RawWorkbook) -> list[LintResult]:
        findings: list[LintResult] = []

        for controller in workbook.controllers:
            for field_name in ("name", "management_ip", "cluster_name", "site_name"):
                value = getattr(controller, field_name)
                if not _has_text(value):
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="SCH007",
                            location="controllers tab",
                            field=field_name,
                            value=value,
                            message="Required field is blank.",
                            suggestion="Populate the required field with a value.",
                        )
                    )
            if _has_text(controller.management_ip):
                findings.extend(
                    self._validate_ip(
                        controller.management_ip,
                        "controllers tab",
                        "management_ip",
                    )
                )
            if _has_text(controller.name) and not IDENTIFIER_PATTERN.fullmatch(
                controller.name or ""
            ):
                findings.append(
                    self._identifier_finding(
                        "controllers tab",
                        "name",
                        controller.name,
                    )
                )

        for switch in workbook.switches:
            if _has_text(switch.management_ip):
                findings.extend(
                    self._validate_ip(
                        switch.management_ip,
                        "switches tab",
                        "management_ip",
                    )
                )
            if _has_text(switch.role) and (switch.role or "") not in SUPPORTED_ROLES:
                findings.append(self._role_finding("switches tab", "role", switch.role))

        for interface in workbook.interfaces:
            if not _has_text(interface.name):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SCH007",
                        location="interfaces tab",
                        field="name",
                        value=interface.name,
                        message="Required field is blank.",
                        suggestion="Populate the required field with a value.",
                    )
                )
            if _has_text(interface.name) and not IDENTIFIER_PATTERN.fullmatch(
                interface.name or ""
            ):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SCH002",
                        location="interfaces tab",
                        field="name",
                        value=interface.name,
                        message="Interface name contains unsupported characters.",
                        suggestion=(
                            "Use only letters, numbers, hyphens, and underscores."
                        ),
                    )
                )
            if (
                _has_text(interface.role)
                and (interface.role or "") not in SUPPORTED_ROLES
            ):
                findings.append(
                    self._role_finding("interfaces tab", "role", interface.role)
                )
            if _has_text(interface.vlan_id):
                findings.extend(
                    self._validate_vlan(interface.vlan_id, "interfaces tab", "vlan_id")
                )
            if (
                _has_text(interface.speed)
                and (interface.speed or "").lower() not in SUPPORTED_SPEEDS
            ):
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="SCH006",
                        location="interfaces tab",
                        field="speed",
                        value=interface.speed,
                        message="Interface speed is unsupported.",
                        suggestion="Use a documented supported speed value.",
                    )
                )

        for group in workbook.groups:
            if _has_text(group.role) and (group.role or "") not in SUPPORTED_ROLES:
                findings.append(self._role_finding("groups tab", "role", group.role))
            if _has_text(group.name) and not IDENTIFIER_PATTERN.fullmatch(
                group.name or ""
            ):
                findings.append(
                    self._identifier_finding("groups tab", "name", group.name)
                )

        for policy in workbook.policies:
            if _has_text(policy.priority):
                try:
                    priority = int(policy.priority or "")
                    if priority < 1 or priority > 65535:
                        raise ValueError
                except ValueError:
                    findings.append(
                        LintResult(
                            severity=Severity.ERROR,
                            code="SCH004",
                            location="policies tab",
                            field="priority",
                            value=policy.priority,
                            message=(
                                "Policy priority must be an integer from 1 to 65535."
                            ),
                            suggestion="Use a positive integer priority within range.",
                        )
                    )
            if _has_text(policy.name) and not IDENTIFIER_PATTERN.fullmatch(
                policy.name or ""
            ):
                findings.append(
                    self._identifier_finding("policies tab", "name", policy.name)
                )
            for match_rule in policy.match_rules:
                if _has_text(match_rule.vlan_id):
                    findings.extend(
                        self._validate_vlan(
                            match_rule.vlan_id,
                            "match_rules tab",
                            "vlan_id",
                        )
                    )

        for site in workbook.sites:
            if _has_text(site.name) and not IDENTIFIER_PATTERN.fullmatch(
                site.name or ""
            ):
                findings.append(
                    self._identifier_finding("sites tab", "name", site.name)
                )

        return findings

    def _validate_ip(
        self,
        value: str | None,
        location: str,
        field: str,
    ) -> list[LintResult]:
        if value is None or not IP_PATTERN.fullmatch(value):
            return [
                LintResult(
                    severity=Severity.ERROR,
                    code="SCH001",
                    location=location,
                    field=field,
                    value=value,
                    message="IP address has an invalid format.",
                    suggestion="Provide a valid IPv4 or IPv6 address.",
                )
            ]

        try:
            ipaddress.ip_address(value)
        except ValueError:
            return [
                LintResult(
                    severity=Severity.ERROR,
                    code="SCH001",
                    location=location,
                    field=field,
                    value=value,
                    message="IP address has an invalid format.",
                    suggestion="Provide a valid IPv4 or IPv6 address.",
                )
            ]
        return []

    def _validate_vlan(
        self,
        value: str | None,
        location: str,
        field: str,
    ) -> list[LintResult]:
        try:
            vlan_id = int(value or "")
        except ValueError:
            vlan_id = -1
        if vlan_id < 1 or vlan_id > 4094:
            return [
                LintResult(
                    severity=Severity.ERROR,
                    code="SCH005",
                    location=location,
                    field=field,
                    value=value,
                    message="VLAN ID must be between 1 and 4094.",
                    suggestion="Use a VLAN ID within the supported range.",
                )
            ]
        return []

    def _role_finding(self, location: str, field: str, value: str | None) -> LintResult:
        return LintResult(
            severity=Severity.ERROR,
            code="SCH003",
            location=location,
            field=field,
            value=value,
            message="Role value is unsupported.",
            suggestion="Use exactly one of: filter, delivery, both.",
        )

    def _identifier_finding(
        self,
        location: str,
        field: str,
        value: str | None,
    ) -> LintResult:
        return LintResult(
            severity=Severity.ERROR,
            code="SCH008",
            location=location,
            field=field,
            value=value,
            message="Identifier contains unsupported characters.",
            suggestion="Use only letters, numbers, hyphens, and underscores.",
        )
