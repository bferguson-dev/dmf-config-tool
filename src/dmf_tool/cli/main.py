"""CLI entry points."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from dmf_tool.core.generator import Generator
from dmf_tool.core.linters.base import LintResult, Severity
from dmf_tool.core.versions.registry import VersionRegistry

EXIT_SUCCESS = 0
EXIT_FINDINGS_ERROR = 1
EXIT_TOOL_ERROR = 2


def _console() -> Console:
    return Console(highlight=False)


def _counts(findings: list[LintResult]) -> tuple[int, int, int]:
    errors = sum(finding.severity is Severity.ERROR for finding in findings)
    warnings = sum(finding.severity is Severity.WARNING for finding in findings)
    infos = sum(finding.severity is Severity.INFO for finding in findings)
    return errors, warnings, infos


def _format_value(value: str | None) -> str:
    if value is None:
        return ""
    return f'"{value}"'


def _print_findings(console: Console, findings: list[LintResult]) -> None:
    for finding in findings:
        console.print(
            f"{finding.code}  {finding.severity.value.upper():<7}  {finding.location}"
        )
        if finding.field:
            console.print(f"        Field:   {finding.field}")
        if finding.value is not None:
            console.print(f"        Value:   {_format_value(finding.value)}")
        console.print(f"        Message: {finding.message}")
        if finding.suggestion:
            console.print(f"        Fix:     {finding.suggestion}")
        console.print()


def _print_summary(console: Console, findings: list[LintResult]) -> int:
    errors, warnings, infos = _counts(findings)
    console.print(f"Summary: {errors} error(s), {warnings} warning(s), {infos} info")
    return errors


def _relative_output_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


@click.group()
def cli() -> None:
    """Run the DMF tool command group."""


@cli.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--dmf-version", required=True)
def validate(input_path: Path, dmf_version: str) -> None:
    """Run input linting only. No generation. No output files written."""
    console = _console()
    console.print("Linting input...")
    try:
        evaluation = Generator().validate(input_path, dmf_version)
    except Exception as exc:  # pragma: no cover
        console.print(f"Tool error: {exc}")
        raise click.exceptions.Exit(EXIT_TOOL_ERROR) from exc

    if evaluation.findings:
        console.print()
        _print_findings(console, evaluation.findings)

    if _print_summary(console, evaluation.findings):
        console.print("Validation blocked. Fix errors and re-run.")
        raise click.exceptions.Exit(EXIT_FINDINGS_ERROR)

    console.print("Validation complete. No output files written.")
    raise click.exceptions.Exit(EXIT_SUCCESS)


@cli.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--dmf-version", required=True)
@click.option(
    "--output",
    default="./output",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
)
def generate(input_path: Path, dmf_version: str, output: Path) -> None:
    """Run full pipeline and write all artifacts."""
    console = _console()
    try:
        result = Generator().run(input_path, dmf_version, output)
    except Exception as exc:  # pragma: no cover
        console.print(f"Tool error: {exc}")
        raise click.exceptions.Exit(EXIT_TOOL_ERROR) from exc

    if not result.success:
        console.print("Linting input...")
        if result.findings:
            console.print()
            _print_findings(console, result.findings)
        _print_summary(console, result.findings)
        console.print("Generation blocked. Fix errors and re-run.")
        raise click.exceptions.Exit(EXIT_FINDINGS_ERROR)

    console.print(
        "Linting input...       "
        f"✓  {result.provenance.error_count} errors, "
        f"{result.provenance.warning_count} warnings"
    )
    console.print("Normalizing...         ✓")
    console.print("Rendering templates... ✓")
    console.print("Verifying output...    ✓")
    console.print()
    console.print(f"Output written to: {_relative_output_path(result.output_dir)}/")
    console.print()
    for artifact in result.diagnostic_artifacts:
        console.print(f"  {artifact.name}")
    for artifact in result.config_artifacts:
        label = " (SENSITIVE)" if artifact.name == "cli-config.txt" else ""
        console.print(f"  {artifact.name}{label}")

    if result.provenance.warning_count:
        console.print()
        console.print(
            f"{result.provenance.warning_count} warnings — review findings.txt "
            "before applying configuration."
        )

    raise click.exceptions.Exit(EXIT_SUCCESS)


@cli.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--dmf-version", required=True)
def check(input_path: Path, dmf_version: str) -> None:
    """Run full pipeline. Report findings. Write no files."""
    console = _console()
    try:
        evaluation = Generator().check(input_path, dmf_version)
    except Exception as exc:  # pragma: no cover
        console.print(f"Tool error: {exc}")
        raise click.exceptions.Exit(EXIT_TOOL_ERROR) from exc

    if evaluation.success:
        console.print(
            "Linting input...       "
            f"✓  {evaluation.provenance.error_count} errors, "
            f"{evaluation.provenance.warning_count} warnings"
        )
        console.print("Normalizing...         ✓")
        console.print("Rendering templates... ✓")
        console.print("Verifying output...    ✓")
        console.print("Check complete. No output files written.")
        raise click.exceptions.Exit(EXIT_SUCCESS)

    console.print("Linting input...")
    if evaluation.findings:
        console.print()
        _print_findings(console, evaluation.findings)
    _print_summary(console, evaluation.findings)
    console.print("Generation blocked. Fix errors and re-run.")
    raise click.exceptions.Exit(EXIT_FINDINGS_ERROR)


@cli.command()
def versions() -> None:
    """List all supported DMF versions."""
    registry = VersionRegistry()
    console = _console()
    console.print("Supported DMF versions:")
    for version in registry.supported_versions():
        console.print(f"- {version}")
    raise click.exceptions.Exit(EXIT_SUCCESS)
