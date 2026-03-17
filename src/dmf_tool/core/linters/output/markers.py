"""Output marker linter."""

from __future__ import annotations

import re

from dmf_tool.core.linters.base import BaseLinter, LintResult, Severity

MARKER_PATTERN = re.compile(r"(\{\{|\}\}|\{%|%})")


class MarkerLinter(BaseLinter):
    """Detect unresolved Jinja markers in rendered output."""

    def run(self, rendered_text: str) -> list[LintResult]:
        findings: list[LintResult] = []
        for line_number, line in enumerate(rendered_text.splitlines(), start=1):
            match = MARKER_PATTERN.search(line)
            if match is None:
                continue
            findings.append(
                LintResult(
                    severity=Severity.ERROR,
                    code="OUT001",
                    location=f"rendered output, line {line_number}",
                    field=None,
                    value=match.group(1),
                    message="Rendered output contains an unresolved template marker.",
                    suggestion=(
                        "Fix the template or context so all Jinja markers resolve."
                    ),
                )
            )
        return findings
