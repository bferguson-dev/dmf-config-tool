"""DMF 8.7 version bundle."""

from __future__ import annotations

from pathlib import Path

from dmf_tool.core.versions.base import VersionBundle
from dmf_tool.core.versions.dmf_8_7.features import SUPPORTED_FEATURES
from dmf_tool.core.versions.dmf_8_7.limits import LIMITS


class DMF87Bundle(VersionBundle):
    """Version bundle for DMF 8.7."""

    @property
    def version_string(self) -> str:
        return "8.7"

    @property
    def supported_features(self) -> frozenset[str]:
        return SUPPORTED_FEATURES

    @property
    def limits(self) -> dict[str, int]:
        return LIMITS

    @property
    def template_dir(self) -> Path:
        # 8.7 currently reuses the 8.8 template set conservatively.
        return Path(__file__).resolve().parent.parent / "dmf_8_8" / "templates"

    @property
    def minimum_workbook_schema_version(self) -> str:
        return "1.0"


BUNDLE = DMF87Bundle()
