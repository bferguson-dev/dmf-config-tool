"""Semantic linter tests."""

from pathlib import Path

import pytest

from dmf_tool.core.versions.base import VersionBundle
from dmf_tool.core.versions.dmf_8_6 import BUNDLE as DMF86_BUNDLE
from dmf_tool.core.versions.dmf_8_7 import BUNDLE as DMF87_BUNDLE
from dmf_tool.core.versions.dmf_8_8 import BUNDLE as DMF88_BUNDLE
from dmf_tool.core.versions.registry import VersionRegistry


def test_registry_returns_expected_bundle() -> None:
    """Known DMF versions should resolve to their bundle."""
    registry = VersionRegistry()

    assert registry.get("8.8") is DMF88_BUNDLE
    assert registry.get("8.7") is DMF87_BUNDLE
    assert registry.get("8.6") is DMF86_BUNDLE


def test_registry_raises_for_unknown_versions() -> None:
    """Unknown versions should fail fast."""
    registry = VersionRegistry()

    with pytest.raises(ValueError, match="Unsupported DMF version"):
        registry.get("9.0")


@pytest.mark.parametrize("bundle", [DMF86_BUNDLE, DMF87_BUNDLE, DMF88_BUNDLE])
def test_each_bundle_exposes_the_expected_interface(bundle: VersionBundle) -> None:
    """Every bundle should satisfy the abstract interface contract."""
    assert bundle.version_string in {"8.6", "8.7", "8.8"}
    assert isinstance(bundle.supported_features, frozenset)
    assert isinstance(bundle.limits, dict)
    assert bundle.minimum_workbook_schema_version == "1.0"
    assert bundle.template_dir == Path(bundle.template_dir)


def test_feature_matrix_lookups_are_version_specific() -> None:
    """Feature support should vary by version where expected."""
    assert DMF88_BUNDLE.supports_feature("analytics_node") is True
    assert DMF87_BUNDLE.supports_feature("analytics_node") is False
    assert DMF86_BUNDLE.supports_feature("recorder_node") is False


def test_capacity_limit_checks_use_bundle_values() -> None:
    """Bundles should evaluate capacity checks against their own limits."""
    assert DMF88_BUNDLE.check_limit("max_policies", 1024) is True
    assert DMF88_BUNDLE.check_limit("max_policies", 1025) is False
    assert DMF86_BUNDLE.check_limit("max_switches", 64) is True
    assert DMF86_BUNDLE.check_limit("max_switches", 65) is False


def test_bundles_are_not_interchangeable() -> None:
    """Each version bundle should remain distinct."""
    registry = VersionRegistry()

    assert registry.supported_versions() == ["8.6", "8.7", "8.8"]
    assert registry.is_supported("8.8") is True
    assert registry.is_supported("8.5") is False
    assert DMF86_BUNDLE is not DMF87_BUNDLE
    assert DMF87_BUNDLE is not DMF88_BUNDLE
