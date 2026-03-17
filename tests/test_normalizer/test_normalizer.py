"""Normalizer tests."""

from __future__ import annotations

from typing import Any, get_args, get_origin, get_type_hints

import pytest

from dmf_tool.core.models.fabric import Fabric
from dmf_tool.core.models.workbook import (
    RawFabricSettings,
    RawGroup,
    RawGroupMember,
    RawInterface,
    RawPolicy,
    RawSite,
    RawSwitch,
    RawWorkbook,
)
from dmf_tool.core.normalizer import NormalizationError, normalize_workbook


def _sample_workbook() -> RawWorkbook:
    return RawWorkbook(
        dmf_version=" 8.8 ",
        workbook_schema_version="1.0",
        controllers=[],
        switches=[
            RawSwitch(
                name=" Leaf-02 ",
                management_ip="10.0.0.2",
                role=" DELIVERY ",
                site_name=" Main ",
            ),
            RawSwitch(
                name=" leaf-01 ",
                management_ip="10.0.0.1",
                role=" filter ",
                site_name=" main ",
            ),
        ],
        interfaces=[
            RawInterface(
                switch_name=" leaf-01 ",
                name=" Ethernet2 ",
                role=" filter ",
                enabled=" yes ",
            ),
            RawInterface(
                switch_name=" leaf-01 ",
                name=" Ethernet1 ",
                role=" filter ",
            ),
        ],
        groups=[
            RawGroup(
                name=" Collectors ",
                role=" filter ",
                members=[
                    RawGroupMember(
                        switch_name=" leaf-01 ",
                        interface_name=" ethernet1 ",
                    )
                ],
            )
        ],
        policies=[
            RawPolicy(
                name=" Mirror ",
                priority=" 100 ",
                source_interface=" leaf-01:ethernet1 ",
                action=None,
                enabled=None,
            )
        ],
        service_nodes=[],
        analytics_nodes=[],
        recorder_nodes=[],
        fabric_settings=RawFabricSettings(fabric_name=None),
        sites=[RawSite(name=" Main ")],
    )


def _contains_raw_type(annotation: Any) -> bool:
    if hasattr(annotation, "__name__") and str(annotation.__name__).startswith("Raw"):
        return True

    origin = get_origin(annotation)
    if origin is None:
        return False

    return any(_contains_raw_type(argument) for argument in get_args(annotation))


def test_case_normalization_and_whitespace_trimming_are_consistent() -> None:
    """Identifiers and strings should be lowercased and trimmed consistently."""
    fabric = normalize_workbook(_sample_workbook())

    assert fabric.dmf_version == "8.8"
    assert fabric.switches[0].name == "leaf-01"
    assert fabric.switches[1].name == "leaf-02"
    assert fabric.groups[0].members == ["leaf-01:ethernet1"]


def test_reference_resolution_rejects_unknown_group_members() -> None:
    """Unknown references should produce a structured normalization error."""
    workbook = _sample_workbook()
    workbook.groups[0].members[0].interface_name = "missing"

    with pytest.raises(NormalizationError, match="unknown interface"):
        normalize_workbook(workbook)


def test_duplicate_detection_raises_normalization_error() -> None:
    """Duplicate canonical keys should raise the typed error."""
    workbook = _sample_workbook()
    workbook.switches.append(
        RawSwitch(
            name="LEAF-01",
            management_ip="10.0.0.10",
            role="filter",
            site_name="main",
        )
    )

    with pytest.raises(NormalizationError, match="Duplicate canonical key"):
        normalize_workbook(workbook)


def test_defaults_are_derived_explicitly() -> None:
    """Missing optional workbook values should normalize to explicit defaults."""
    fabric = normalize_workbook(_sample_workbook())

    assert fabric.policies[0].action == "forward"
    assert fabric.policies[0].enabled is True
    assert fabric.interfaces[0].enabled is True
    assert fabric.fabric_settings.fabric_name == "dmf-fabric"


def test_collections_are_sorted_deterministically() -> None:
    """Output collections should sort consistently by canonical key."""
    fabric = normalize_workbook(_sample_workbook())

    assert [switch.name for switch in fabric.switches] == ["leaf-01", "leaf-02"]
    assert [interface.name for interface in fabric.interfaces] == [
        "ethernet1",
        "ethernet2",
    ]


def test_no_raw_types_appear_in_fabric_output() -> None:
    """The normalized result should only contain canonical model types."""
    fabric = normalize_workbook(_sample_workbook())

    assert isinstance(fabric, Fabric)
    for annotation in get_type_hints(type(fabric), include_extras=True).values():
        assert _contains_raw_type(annotation) is False


def test_identical_input_produces_identical_output() -> None:
    """Normalization should be deterministic for identical inputs."""
    first = normalize_workbook(_sample_workbook())
    second = normalize_workbook(_sample_workbook())

    assert first.model_dump() == second.model_dump()
