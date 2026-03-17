"""Generator pipeline."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, Field

from dmf_tool.core.linters.base import LintResult, Severity
from dmf_tool.core.linters.input.bestpractice import BestPracticeLinter
from dmf_tool.core.linters.input.relational import RelationalLinter
from dmf_tool.core.linters.input.schema import SchemaLinter
from dmf_tool.core.linters.input.semantic import SemanticLinter
from dmf_tool.core.linters.input.structural import StructuralLinter
from dmf_tool.core.linters.output.completeness import CompletenessLinter
from dmf_tool.core.linters.output.encoding import EncodingLinter
from dmf_tool.core.linters.output.markers import MarkerLinter
from dmf_tool.core.models.fabric import Fabric
from dmf_tool.core.normalizer import NormalizationError, normalize_workbook
from dmf_tool.core.parser import (
    WorkbookAcceptanceError,
    WorkbookParseError,
    parse_workbook,
)
from dmf_tool.core.rendering import render_config
from dmf_tool.core.versions.registry import VersionRegistry

SECRET_FIELDS = (
    "snmp_community",
    "enable_password",
    "auth_password",
    "priv_password",
    "api_key",
    "api_token",
)
TEXT_ENCODING = "utf-8"
TEXT_NEWLINE = "\n"


@dataclass(slots=True)
class EvaluatedPipeline:
    """In-memory result of evaluating the pipeline without file writes."""

    findings: list[LintResult]
    provenance: Provenance
    fabric: Fabric | None = None
    rendered: str | None = None

    @property
    def success(self) -> bool:
        """Return whether the evaluation completed without errors."""
        return not any(finding.severity is Severity.ERROR for finding in self.findings)


class Provenance(BaseModel):
    """Metadata attached to each generation run."""

    model_config = ConfigDict(extra="forbid")

    tool_version: str
    template_bundle_version: str
    workbook_schema_version: str
    dmf_version: str
    timestamp: str
    input_hash: str
    error_count: int
    warning_count: int


class GeneratorResult(BaseModel):
    """Result object for generator runs."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    success: bool
    run_id: str
    output_dir: Path
    diagnostic_artifacts: list[Path] = Field(
        default_factory=lambda: cast(list[Path], [])
    )
    config_artifacts: list[Path] = Field(default_factory=lambda: cast(list[Path], []))
    findings: list[LintResult] = Field(
        default_factory=lambda: cast(list[LintResult], [])
    )
    provenance: Provenance


class Generator:
    """Execute the offline DMF generation pipeline."""

    def __init__(self, clock: Callable[[], str] | None = None) -> None:
        self._clock = clock or (
            lambda: datetime.now(tz=UTC).replace(microsecond=0).isoformat()
        )
        self._registry = VersionRegistry()

    def run(
        self,
        workbook_path: Path,
        dmf_version: str,
        output_base: Path,
    ) -> GeneratorResult:
        evaluation = self.check(workbook_path, dmf_version)
        run_id = self._filesystem_safe_timestamp(self._clock())
        output_dir = output_base / run_id
        if (
            not evaluation.success
            or evaluation.fabric is None
            or evaluation.rendered is None
        ):
            return self._write_failure(
                output_dir,
                evaluation.findings,
                evaluation.provenance,
            )

        return self._write_success(
            output_dir,
            evaluation.findings,
            evaluation.provenance,
            evaluation.fabric,
            evaluation.rendered,
        )

    def validate(self, workbook_path: Path, dmf_version: str) -> EvaluatedPipeline:
        """Run input parsing, normalization, and input linting without rendering."""
        return self._evaluate_pipeline(
            workbook_path=workbook_path,
            dmf_version=dmf_version,
            render_output=False,
        )

    def check(self, workbook_path: Path, dmf_version: str) -> EvaluatedPipeline:
        """Run the full pipeline without writing artifacts."""
        return self._evaluate_pipeline(
            workbook_path=workbook_path,
            dmf_version=dmf_version,
            render_output=True,
        )

    def _write_success(
        self,
        output_dir: Path,
        findings: list[LintResult],
        provenance: Provenance,
        fabric: Fabric,
        rendered: str,
    ) -> GeneratorResult:
        config_artifacts: list[Path] = []
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_dir.parent) as tmp_dir:
            tmp_path = Path(tmp_dir)
            diagnostic_artifacts = self._write_diagnostic_artifacts(
                tmp_path,
                findings,
                provenance,
            )

            config_path = tmp_path / "cli-config.txt"
            config_path.write_text(
                "! SENSITIVE\n" + rendered,
                encoding=TEXT_ENCODING,
                newline=TEXT_NEWLINE,
            )
            config_artifacts.append(output_dir / "cli-config.txt")

            redacted = self._redact_secrets(rendered)
            if redacted != rendered:
                redacted_path = tmp_path / "cli-config-redacted.txt"
                redacted_path.write_text(
                    redacted,
                    encoding=TEXT_ENCODING,
                    newline=TEXT_NEWLINE,
                )
                config_artifacts.append(output_dir / "cli-config-redacted.txt")

            summary_path = tmp_path / "summary.md"
            summary_path.write_text(
                self._build_summary(fabric, findings, provenance),
                encoding=TEXT_ENCODING,
                newline=TEXT_NEWLINE,
            )
            config_artifacts.append(output_dir / "summary.md")

            final_output = self._commit_output_dir(tmp_path, output_dir)

        diagnostic_paths = [
            final_output / artifact.name for artifact in diagnostic_artifacts
        ]
        return GeneratorResult(
            success=True,
            run_id=output_dir.name,
            output_dir=final_output,
            diagnostic_artifacts=diagnostic_paths,
            config_artifacts=config_artifacts,
            findings=findings,
            provenance=provenance,
        )

    def _write_failure(
        self,
        output_dir: Path,
        findings: list[LintResult],
        provenance: Provenance,
    ) -> GeneratorResult:
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_dir.parent) as tmp_dir:
            tmp_path = Path(tmp_dir)
            diagnostic_artifacts = self._write_diagnostic_artifacts(
                tmp_path,
                findings,
                provenance,
            )
            final_output = self._commit_output_dir(tmp_path, output_dir)

        diagnostic_paths = [
            final_output / artifact.name for artifact in diagnostic_artifacts
        ]
        return GeneratorResult(
            success=False,
            run_id=output_dir.name,
            output_dir=final_output,
            diagnostic_artifacts=diagnostic_paths,
            config_artifacts=[],
            findings=findings,
            provenance=provenance,
        )

    def _write_diagnostic_artifacts(
        self,
        output_dir: Path,
        findings: list[LintResult],
        provenance: Provenance,
    ) -> list[Path]:
        findings_json = output_dir / "findings.json"
        findings_txt = output_dir / "findings.txt"
        finding_payload = {
            "provenance": provenance.model_dump(mode="json"),
            "findings": [finding.model_dump(mode="json") for finding in findings],
        }
        findings_json.write_text(
            json.dumps(finding_payload, indent=2) + TEXT_NEWLINE,
            encoding=TEXT_ENCODING,
            newline=TEXT_NEWLINE,
        )
        findings_txt.write_text(
            self._format_findings(findings, provenance),
            encoding=TEXT_ENCODING,
            newline=TEXT_NEWLINE,
        )
        return [findings_json, findings_txt]

    def _format_findings(
        self,
        findings: list[LintResult],
        provenance: Provenance,
    ) -> str:
        lines = [
            "DMF Configuration Generator Findings",
            f"Tool Version: {provenance.tool_version}",
            f"Template Bundle: {provenance.template_bundle_version}",
            f"Workbook Schema: {provenance.workbook_schema_version}",
            f"Target DMF Version: {provenance.dmf_version}",
            f"Generated: {provenance.timestamp}",
            f"Input Hash: {provenance.input_hash}",
            (
                "Findings Summary: "
                f"{provenance.error_count} errors, {provenance.warning_count} warnings"
            ),
            "",
        ]
        for finding in findings:
            lines.append(
                f"{finding.code} {finding.severity.value.upper()} {finding.location}"
            )
            lines.append(f"  Message: {finding.message}")
            if finding.suggestion:
                lines.append(f"  Fix: {finding.suggestion}")
        return "\n".join(lines) + ("\n" if lines else "")

    def _build_summary(
        self,
        fabric: Fabric,
        findings: list[LintResult],
        provenance: Provenance,
    ) -> str:
        warnings = [
            finding for finding in findings if finding.severity is Severity.WARNING
        ]
        lines = [
            "# DMF Configuration Summary",
            "",
            "## Provenance",
            f"- Tool Version: {provenance.tool_version}",
            f"- Template Bundle: {provenance.template_bundle_version}",
            f"- Workbook Schema: {provenance.workbook_schema_version}",
            f"- Target DMF Version: {provenance.dmf_version}",
            f"- Generated: {provenance.timestamp}",
            f"- Input Hash: {provenance.input_hash}",
            (
                "- Findings Summary: "
                f"{provenance.error_count} errors, {provenance.warning_count} warnings"
            ),
            "",
            "## Controllers",
        ]
        lines.extend(
            f"- {controller.name} ({controller.role})"
            for controller in fabric.controllers
        )
        interface_lines = [
            f"- {interface.switch_name}:{interface.name} ({interface.role})"
            for interface in fabric.interfaces
        ]
        group_lines = [
            f"- group {group.name}: {len(group.members)} members"
            for group in fabric.groups
        ]
        policy_lines = [
            (
                f"| {policy.name} | {policy.priority} | "
                f"{policy.source_interface or policy.source_group or ''} | "
                f"{policy.delivery_interface or policy.delivery_group or ''} | "
                f"{policy.action} | {len(policy.match_rules)} |"
            )
            for policy in fabric.policies
        ]
        lines.extend(
            [
                "",
                "## Switches by Role",
                *[f"- {switch.name}: {switch.role}" for switch in fabric.switches],
                "",
                "## Interfaces and Groups",
                *interface_lines,
                *group_lines,
                "",
                "## Policies",
                "| Name | Priority | Filter | Delivery | Action | Match Rules |",
                "| --- | --- | --- | --- | --- | --- |",
                *policy_lines,
                "",
                "## Fabric Settings",
                f"- Fabric Name: {fabric.fabric_settings.fabric_name}",
                "",
                "## Operator Attention Required",
            ]
        )
        if warnings:
            lines.extend(f"- {warning.code}: {warning.message}" for warning in warnings)
        else:
            lines.append("- None")
        return "\n".join(lines) + "\n"

    def _redact_secrets(self, rendered: str) -> str:
        redacted = rendered
        replacements = {
            r"(snmp-community )(\S+)": r"\1<REDACTED-snmp_community>",
            r"(enable-password )(\S+)": r"\1<REDACTED-enable_password>",
            r"(api-token )(\S+)": r"\1<REDACTED-api_token>",
        }
        for pattern, replacement in replacements.items():
            redacted = re.sub(pattern, replacement, redacted)
        return redacted

    def _build_provenance(
        self,
        template_bundle_version: str,
        workbook_schema_version: str,
        dmf_version: str,
        input_hash: str,
        findings: list[LintResult],
    ) -> Provenance:
        return Provenance(
            tool_version="0.1.0",
            template_bundle_version=template_bundle_version,
            workbook_schema_version=workbook_schema_version,
            dmf_version=dmf_version,
            timestamp=self._clock(),
            input_hash=input_hash,
            error_count=sum(finding.severity is Severity.ERROR for finding in findings),
            warning_count=sum(
                finding.severity is Severity.WARNING for finding in findings
            ),
        )

    def _has_errors(self, findings: list[LintResult]) -> bool:
        return any(finding.severity is Severity.ERROR for finding in findings)

    def _tool_error_finding(self, message: str) -> LintResult:
        return LintResult(
            severity=Severity.ERROR,
            code="OUT010",
            location="generator",
            field=None,
            value=None,
            message=message,
            suggestion="Correct the workbook or file path and retry.",
        )

    def _filesystem_safe_timestamp(self, timestamp: str) -> str:
        return timestamp.replace(":", "-")

    def _commit_output_dir(self, tmp_path: Path, final_output_dir: Path) -> Path:
        final_output_dir.parent.mkdir(parents=True, exist_ok=True)
        if final_output_dir.exists():
            shutil.rmtree(final_output_dir)
        shutil.move(str(tmp_path), str(final_output_dir))
        return final_output_dir

    def _evaluate_pipeline(
        self,
        workbook_path: Path,
        dmf_version: str,
        render_output: bool,
    ) -> EvaluatedPipeline:
        findings: list[LintResult] = []
        template_bundle_version = ""
        workbook_schema_version = ""
        input_hash = ""

        try:
            bundle = self._registry.get(dmf_version)
        except ValueError as exc:
            findings.append(self._tool_error_finding(str(exc)))
            return EvaluatedPipeline(
                findings=findings,
                provenance=self._build_provenance(
                    template_bundle_version,
                    workbook_schema_version,
                    dmf_version,
                    input_hash,
                    findings,
                ),
            )

        template_bundle_version = bundle.version_string

        try:
            workbook_bytes = self._read_input_bytes(workbook_path)
        except OSError as exc:
            findings.append(self._tool_error_finding(str(exc)))
            return EvaluatedPipeline(
                findings=findings,
                provenance=self._build_provenance(
                    template_bundle_version,
                    workbook_schema_version,
                    dmf_version,
                    input_hash,
                    findings,
                ),
            )

        input_hash = hashlib.sha256(workbook_bytes).hexdigest()

        try:
            raw_workbook = parse_workbook(workbook_path)
        except (WorkbookAcceptanceError, WorkbookParseError) as exc:
            findings.append(self._tool_error_finding(str(exc)))
            return EvaluatedPipeline(
                findings=findings,
                provenance=self._build_provenance(
                    template_bundle_version,
                    workbook_schema_version,
                    dmf_version,
                    input_hash,
                    findings,
                ),
            )

        workbook_schema_version = raw_workbook.workbook_schema_version
        findings.extend(StructuralLinter().run(raw_workbook))
        if self._has_errors(findings):
            return EvaluatedPipeline(
                findings=findings,
                provenance=self._build_provenance(
                    template_bundle_version,
                    workbook_schema_version,
                    dmf_version,
                    input_hash,
                    findings,
                ),
            )

        try:
            fabric = normalize_workbook(raw_workbook)
        except NormalizationError as exc:
            findings.append(self._normalization_error_finding(str(exc)))
            return EvaluatedPipeline(
                findings=findings,
                provenance=self._build_provenance(
                    template_bundle_version,
                    workbook_schema_version,
                    dmf_version,
                    input_hash,
                    findings,
                ),
            )

        findings.extend(SchemaLinter().run(raw_workbook))
        findings.extend(RelationalLinter().run(raw_workbook))
        findings.extend(SemanticLinter(bundle).run(fabric))
        findings.extend(BestPracticeLinter().run(fabric))

        if self._has_errors(findings) or not render_output:
            return EvaluatedPipeline(
                findings=findings,
                provenance=self._build_provenance(
                    template_bundle_version,
                    workbook_schema_version,
                    dmf_version,
                    input_hash,
                    findings,
                ),
                fabric=fabric,
            )

        pre_render_provenance = self._build_provenance(
            template_bundle_version,
            workbook_schema_version,
            dmf_version,
            input_hash,
            findings,
        )
        rendered = render_config(bundle, fabric, pre_render_provenance.model_dump())

        findings.extend(MarkerLinter().run(rendered))
        findings.extend(EncodingLinter().run(rendered))
        findings.extend(CompletenessLinter().run(fabric, rendered))
        return EvaluatedPipeline(
            findings=findings,
            provenance=self._build_provenance(
                template_bundle_version,
                workbook_schema_version,
                dmf_version,
                input_hash,
                findings,
            ),
            fabric=fabric,
            rendered=rendered,
        )

    def _read_input_bytes(self, workbook_path: Path) -> bytes:
        if not workbook_path.exists():
            msg = f"Workbook does not exist: {workbook_path}"
            raise FileNotFoundError(msg)
        if not workbook_path.is_file():
            msg = f"Workbook path is not a file: {workbook_path}"
            raise OSError(msg)
        return workbook_path.read_bytes()

    def _normalization_error_finding(self, message: str) -> LintResult:
        return LintResult(
            severity=Severity.ERROR,
            code="SEM050",
            location="normalizer",
            field=None,
            value=None,
            message=message,
            suggestion="Fix duplicate or invalid canonicalized values and retry.",
        )
