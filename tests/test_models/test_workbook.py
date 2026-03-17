"""Workbook model tests."""

from dmf_tool.core.models.workbook import (
    RawGroup,
    RawGroupMember,
    RawPolicy,
    RawWorkbook,
)


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
