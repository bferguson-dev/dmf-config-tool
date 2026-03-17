"""Structural linter tests."""

import pytest
from pydantic import ValidationError

from dmf_tool.core.linters.base import (
    FINDING_CODE_PREFIXES,
    BaseLinter,
    LintResult,
    Severity,
)


class DummyLinter(BaseLinter):
    """Concrete linter for abstract base testing."""

    def run(self) -> list[LintResult]:
        return [
            LintResult(
                severity=Severity.INFO,
                code="STR001",
                location="sheet1 row 2",
                message="example",
            )
        ]


@pytest.mark.parametrize(
    ("field", "value", "suggestion"),
    [
        ("hostname", "leaf-01", "Use a unique switch name."),
        ("hostname", None, "Populate the missing value."),
        (None, "leaf-01", None),
        (None, None, None),
    ],
)
def test_lint_result_supports_field_combinations(
    field: str | None,
    value: str | None,
    suggestion: str | None,
) -> None:
    """Lint results should support optional field/value/suggestion data."""
    result = LintResult(
        severity=Severity.WARNING,
        code="STR001",
        location="switches tab, row 4, column B",
        field=field,
        value=value,
        message="Example finding",
        suggestion=suggestion,
    )

    assert result.field == field
    assert result.value == value
    assert result.suggestion == suggestion


def test_severity_enum_values_are_stable() -> None:
    """Severity enum values must match the handoff contract."""
    assert Severity.ERROR.value == "error"
    assert Severity.WARNING.value == "warning"
    assert Severity.INFO.value == "info"


@pytest.mark.parametrize(
    "code",
    ["STR001", "SCH050", "REL020", "SEM050", "BPR006", "OUT010"],
)
def test_lint_result_accepts_registered_finding_codes(code: str) -> None:
    """Known finding prefixes should validate cleanly."""
    result = LintResult(
        severity=Severity.INFO,
        code=code,
        location="metadata tab",
        message="Known code",
    )

    assert result.code == code


@pytest.mark.parametrize("code", ["str001", "BAD001", "STR01", "STR1000", "STR-001"])
def test_lint_result_rejects_invalid_finding_codes(code: str) -> None:
    """Unknown or malformed finding codes should fail validation."""
    with pytest.raises(ValidationError):
        LintResult(
            severity=Severity.ERROR,
            code=code,
            location="metadata tab",
            message="Invalid code",
        )


def test_error_severity_is_pipeline_halting() -> None:
    """Only errors should halt pipeline execution."""
    error_result = LintResult(
        severity=Severity.ERROR,
        code="STR001",
        location="metadata tab",
        message="Hard failure",
    )
    warning_result = LintResult(
        severity=Severity.WARNING,
        code="STR002",
        location="metadata tab",
        message="Soft failure",
    )

    assert Severity.ERROR.halts_pipeline is True
    assert Severity.WARNING.halts_pipeline is False
    assert error_result.halts_pipeline is True
    assert warning_result.halts_pipeline is False


def test_base_linter_run_contract_returns_findings() -> None:
    """Concrete linters should return structured lint results."""
    findings = DummyLinter().run()

    assert len(findings) == 1
    assert findings[0].code == "STR001"
    assert FINDING_CODE_PREFIXES["STR"] == "Structural"
