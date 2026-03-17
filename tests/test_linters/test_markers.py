"""Output markers tests."""

from dmf_tool.core.linters.output import markers


def test_markers_module_has_docstring() -> None:
    """Keep the bootstrap scaffold importable under pytest."""
    assert markers.__doc__ == "Output marker linter."
