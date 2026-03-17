"""Version bundle base types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class VersionBundle(ABC):
    """Abstract interface for DMF version-specific configuration data."""

    @property
    @abstractmethod
    def version_string(self) -> str:
        """Return the DMF version identifier."""

    @property
    @abstractmethod
    def supported_features(self) -> frozenset[str]:
        """Return the supported feature flags for this bundle."""

    @property
    @abstractmethod
    def limits(self) -> dict[str, int]:
        """Return conservative capacity limits for this DMF version."""

    @property
    @abstractmethod
    def template_dir(self) -> Path:
        """Return the template directory for this version bundle."""

    @property
    @abstractmethod
    def minimum_workbook_schema_version(self) -> str:
        """Return the oldest workbook schema this bundle supports."""

    def supports_feature(self, feature: str) -> bool:
        """Return whether the bundle advertises support for a feature."""
        return feature in self.supported_features

    def check_limit(self, limit_name: str, value: int) -> bool:
        """Return whether a value fits within the configured capacity."""
        return value <= self.limits.get(limit_name, 0)
