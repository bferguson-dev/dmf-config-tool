"""Output encoding linter."""

from __future__ import annotations

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity


class EncodingLinter(BaseLinter):
    """Verify rendered output contains only ASCII characters."""

    def run(self, rendered_text: str) -> list[LintResult]:
        findings: list[LintResult] = []
        for line_number, line in enumerate(rendered_text.splitlines(), start=1):
            for character in line:
                if ord(character) < 128:
                    continue
                findings.append(
                    LintResult(
                        severity=Severity.ERROR,
                        code="OUT002",
                        location=f"rendered output, line {line_number}",
                        field=None,
                        value=character,
                        message="Rendered output contains a non-ASCII character.",
                        suggestion="Restrict output to ASCII-safe template content.",
                    )
                )
        return findings
