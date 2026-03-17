"""Version registry."""

from __future__ import annotations

from dmf_tool.core.versions.base import VersionBundle
from dmf_tool.core.versions.dmf_8_6 import BUNDLE as DMF86_BUNDLE
from dmf_tool.core.versions.dmf_8_7 import BUNDLE as DMF87_BUNDLE
from dmf_tool.core.versions.dmf_8_8 import BUNDLE as DMF88_BUNDLE


class VersionRegistry:
    """Registry of supported DMF version bundles."""

    def __init__(self) -> None:
        self._bundles: dict[str, VersionBundle] = {
            DMF86_BUNDLE.version_string: DMF86_BUNDLE,
            DMF87_BUNDLE.version_string: DMF87_BUNDLE,
            DMF88_BUNDLE.version_string: DMF88_BUNDLE,
        }

    def get(self, version_string: str) -> VersionBundle:
        """Return the bundle for a known version string."""
        if version_string not in self._bundles:
            msg = f"Unsupported DMF version: {version_string}"
            raise ValueError(msg)
        return self._bundles[version_string]

    def supported_versions(self) -> list[str]:
        """Return the list of supported versions in ascending order."""
        return sorted(self._bundles)

    def is_supported(self, version_string: str) -> bool:
        """Return whether a version string is available."""
        return version_string in self._bundles
