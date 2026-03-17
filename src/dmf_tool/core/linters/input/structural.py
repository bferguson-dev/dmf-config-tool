"""Structural input linter."""

from __future__ import annotations

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity
from dmf_tool.core.models.workbook import RawWorkbook

SUPPORTED_WORKBOOK_SCHEMA_VERSIONS = frozenset({"1.0"})


class StructuralLinter(BaseLinter):
    """Validate workbook-level structural requirements expressible from RawWorkbook."""

    def run(self, workbook: RawWorkbook) -> list[LintResult]:
        findings: list[LintResult] = []

        if not workbook.switches:
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="STR001",
                    location="switches tab",
                    field="switches",
                    value=None,
                    message="At least one switch row is required.",
                    suggestion="Populate the switches tab with one or more switches.",
                )
            )

        if not workbook.interfaces:
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="STR002",
                    location="interfaces tab",
                    field="interfaces",
                    value=None,
                    message="At least one interface row is required.",
                    suggestion=(
                        "Populate the interfaces tab with one or more interfaces."
                    ),
                )
            )

        if not workbook.workbook_schema_version.strip():
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="STR003",
                    location="metadata tab",
                    field="workbook_schema_version",
                    value=workbook.workbook_schema_version,
                    message="Workbook schema version is missing.",
                    suggestion="Set workbook_schema_version in the metadata sheet.",
                )
            )
        elif workbook.workbook_schema_version not in SUPPORTED_WORKBOOK_SCHEMA_VERSIONS:
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="STR004",
                    location="metadata tab",
                    field="workbook_schema_version",
                    value=workbook.workbook_schema_version,
                    message="Workbook schema version is not recognized.",
                    suggestion="Use a supported workbook schema version.",
                )
            )

        if workbook.fabric_settings is None:
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="STR005",
                    location="fabric_settings tab",
                    field="fabric_settings",
                    value=None,
                    message="Fabric settings are required for generation.",
                    suggestion="Populate the fabric_settings tab with a settings row.",
                )
            )

        return findings
