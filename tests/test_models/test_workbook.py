"""Workbook model tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from dmf_tool.core.models.workbook import (
    RawGroup,
    RawGroupMember,
    RawPolicy,
    RawWorkbook,
)
from dmf_tool.core.parser import (
    MAX_WORKBOOK_BYTES,
    WorkbookAcceptanceError,
    parse_workbook,
    validate_workbook_path,
)
from tests.helpers.workbook_builder import WorkbookBuilder


def test_raw_workbook_accepts_sparse_string_data() -> None:
    """Raw workbook models should tolerate parser-shaped string data."""
    workbook = RawWorkbook(
        dmf_version="8.8",
        workbook_schema_version="1.0",
        groups=[
            RawGroup(
                name="Collectors",
                role="delivery",
                members=[
                    RawGroupMember(
                        interface_name="Ethernet1",
                        switch_name="leaf-1",
                    )
                ],
            )
        ],
        policies=[RawPolicy(name="Mirror traffic", priority="100", action="forward")],
    )

    assert workbook.groups[0].members[0].interface_name == "Ethernet1"
    assert workbook.policies[0].priority == "100"


def _inject_zip_member(path: Path, member_name: str, content: bytes) -> None:
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr(member_name, content)


def test_parser_converts_workbook_to_raw_models(tmp_path: Path) -> None:
    """A valid workbook should parse into the raw workbook model."""
    workbook_path = WorkbookBuilder().save(tmp_path / "valid.xlsx")

    workbook = parse_workbook(workbook_path)

    assert workbook.dmf_version == "8.8"
    assert workbook.workbook_schema_version == "1.0"
    assert workbook.groups[0].members[0].switch_name == "leaf-1"
    assert workbook.policies[0].match_rules[0].protocol == "tcp"


def test_rejects_non_xlsx_extension(tmp_path: Path) -> None:
    """Non-xlsx files should fail acceptance checks."""
    workbook_path = WorkbookBuilder().save(tmp_path / "invalid.txt")

    with pytest.raises(WorkbookAcceptanceError, match=".xlsx extension"):
        validate_workbook_path(workbook_path)


def test_rejects_xlsm_extension(tmp_path: Path) -> None:
    """Macro-enabled extensions should fail immediately."""
    workbook_path = WorkbookBuilder().save(tmp_path / "invalid.xlsm")

    with pytest.raises(WorkbookAcceptanceError, match=".xlsm"):
        validate_workbook_path(workbook_path)


def test_rejects_xls_extension(tmp_path: Path) -> None:
    """Legacy xls files are out of scope."""
    workbook_path = WorkbookBuilder().save(tmp_path / "invalid.xls")

    with pytest.raises(WorkbookAcceptanceError, match=".xls"):
        validate_workbook_path(workbook_path)


def test_rejects_macro_enabled_xlsx_even_with_xlsx_suffix(tmp_path: Path) -> None:
    """Embedded VBA should be rejected even when the filename is .xlsx."""
    workbook_path = WorkbookBuilder().save(tmp_path / "macro.xlsx")
    _inject_zip_member(workbook_path, "xl/vbaProject.bin", b"macro")

    with pytest.raises(WorkbookAcceptanceError, match="VBA macros"):
        validate_workbook_path(workbook_path)


def test_rejects_external_links(tmp_path: Path) -> None:
    """External workbook links should fail acceptance."""
    workbook_path = WorkbookBuilder().save(tmp_path / "linked.xlsx")
    _inject_zip_member(
        workbook_path,
        "xl/externalLinks/externalLink1.xml",
        b"<externalLink />",
    )

    with pytest.raises(WorkbookAcceptanceError, match="external links"):
        validate_workbook_path(workbook_path)


def test_rejects_corrupt_workbook(tmp_path: Path) -> None:
    """Unreadable zip structures should fail cleanly."""
    workbook_path = tmp_path / "corrupt.xlsx"
    workbook_path.write_bytes(b"not-a-valid-workbook")

    with pytest.raises(WorkbookAcceptanceError, match="corrupt or unreadable"):
        validate_workbook_path(workbook_path)


def test_rejects_oversized_workbook(tmp_path: Path) -> None:
    """Files over the size limit should fail before parsing."""
    workbook_path = WorkbookBuilder().save(tmp_path / "large.xlsx")
    with workbook_path.open("ab") as workbook_file:
        workbook_file.truncate(MAX_WORKBOOK_BYTES + 1)

    with pytest.raises(WorkbookAcceptanceError, match="10MB"):
        validate_workbook_path(workbook_path)


def test_rejects_formula_cells(tmp_path: Path) -> None:
    """Formula cells are out of scope for parser input."""
    workbook_path = (
        WorkbookBuilder()
        .with_formula("switches", 2, "B")
        .save(tmp_path / "formula.xlsx")
    )

    with pytest.raises(WorkbookAcceptanceError, match="formula"):
        parse_workbook(workbook_path)


def test_rejects_hidden_sheets(tmp_path: Path) -> None:
    """Hidden sheets should fail parsing."""
    builder = WorkbookBuilder()
    builder.build()["switches"].sheet_state = "hidden"
    workbook_path = builder.save(tmp_path / "hidden.xlsx")

    with pytest.raises(WorkbookAcceptanceError, match="hidden sheet"):
        parse_workbook(workbook_path)
