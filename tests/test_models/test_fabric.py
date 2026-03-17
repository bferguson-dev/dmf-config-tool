"""Fabric model tests."""

from dmf_tool.core.models import fabric


def test_fabric_module_has_docstring() -> None:
    """Keep the bootstrap scaffold importable under pytest."""
    assert fabric.__doc__ == "Canonical fabric models."
