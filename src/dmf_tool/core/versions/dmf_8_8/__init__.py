"""DMF 8.8 version bundle."""

from __future__ import annotations

from pathlib import Path

from dmf_tool.core.versions.base import VersionBundle
from dmf_tool.core.versions.dmf_8_8.features import SUPPORTED_FEATURES
from dmf_tool.core.versions.dmf_8_8.limits import LIMITS


class DMF88Bundle(VersionBundle):
    """Version bundle for DMF 8.8."""

    @property
    def version_string(self) -> str:
        return "8.8"

    @property
    def supported_features(self) -> frozenset[str]:
        return SUPPORTED_FEATURES

    @property
    def limits(self) -> dict[str, int]:
        return LIMITS

    @property
    def template_dir(self) -> Path:
        return Path(__file__).resolve().parent / "templates"

    @property
    def minimum_workbook_schema_version(self) -> str:
        return "1.0"


BUNDLE = DMF88Bundle()
