"""Workbook model tests."""

from dmf_tool.core.models import workbook


def test_workbook_module_has_docstring() -> None:
    """Keep the bootstrap scaffold importable under pytest."""
    assert workbook.__doc__ == "Raw workbook models."
