"""Structural linter tests."""

from dmf_tool.core.linters.input import structural


def test_structural_module_has_docstring() -> None:
    """Keep the bootstrap scaffold importable under pytest."""
    assert structural.__doc__ == "Structural input linter."
