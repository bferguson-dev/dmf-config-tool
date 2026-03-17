"""Base linter definitions."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

FINDING_CODE_PATTERN = re.compile(r"^(STR|SCH|REL|SEM|BPR|OUT)\d{3}$")
FINDING_CODE_PREFIXES: dict[str, str] = {
    "STR": "Structural",
    "SCH": "Schema",
    "REL": "Relational",
    "SEM": "Semantic",
    "BPR": "Best Practice",
    "OUT": "Output Verification",
}


class Severity(StrEnum):
    """Supported lint severities."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def halts_pipeline(self) -> bool:
        """Return whether a finding at this severity should stop execution."""
        return self is Severity.ERROR


class LintResult(BaseModel):
    """A structured lint finding."""

    model_config = ConfigDict(str_strip_whitespace=False)

    severity: Severity
    code: str = Field(description="Finding code, such as STR001.")
    location: str
    field: str | None = None
    value: str | None = None
    message: str
    suggestion: str | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """Ensure the finding code matches a known category prefix."""
        if not FINDING_CODE_PATTERN.fullmatch(value):
            raise ValueError(
                "Finding code must match <prefix><3 digits> using a registered prefix."
            )
        return value

    @property
    def halts_pipeline(self) -> bool:
        """Return whether this finding should stop the pipeline."""
        return self.severity.halts_pipeline


class BaseLinter(ABC):
    """Base class for lint passes."""

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> list[LintResult]:
        """Execute the linter and return findings."""
        raise NotImplementedError
