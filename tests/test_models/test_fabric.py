"""Fabric model tests."""

from __future__ import annotations

from typing import Any, get_args, get_origin, get_type_hints

import pytest
from pydantic import SecretStr, ValidationError

from dmf_tool.core.models import fabric
from dmf_tool.core.models.fabric import (
    Controller,
    Fabric,
    FabricSettings,
    Switch,
)


def _contains_raw_type(annotation: Any) -> bool:
    """Return whether an annotation tree references a Raw* type."""
    if hasattr(annotation, "__name__") and str(annotation.__name__).startswith("Raw"):
        return True

    origin = get_origin(annotation)
    if origin is None:
        return False

    return any(_contains_raw_type(argument) for argument in get_args(annotation))


def test_fabric_rejects_invalid_canonical_data() -> None:
    """Canonical models should enforce strict typing."""
    with pytest.raises(ValidationError):
        Fabric.model_validate(
            {
                "dmf_version": "8.8",
                "controllers": [
                    {
                        "name": "controller-1",
                        "management_ip": "10.0.0.10",
                        "cluster_name": "cluster-a",
                        "role": "active",
                        "site_name": "site-a",
                    }
                ],
                "switches": [
                    {
                        "name": "leaf-01",
                        "management_ip": "10.0.0.20",
                        "role": "filter",
                        "site_name": "site-a",
                    }
                ],
                "interfaces": [
                    {
                        "switch_name": "leaf-01",
                        "name": "ethernet1",
                        "role": "filter",
                        "enabled": True,
                    }
                ],
                "policies": [
                    {
                        "name": "policy-1",
                        "priority": "high",
                        "action": "forward",
                        "match_rules": [{"sequence": 1}],
                    }
                ],
                "fabric_settings": {"fabric_name": "fabric-a"},
                "sites": [{"name": "site-a"}],
            }
        )


def test_fabric_fields_are_typed_and_required() -> None:
    """Required canonical fields should be non-optional and typed."""
    model_fields = Fabric.model_fields

    assert model_fields["dmf_version"].is_required() is True
    assert model_fields["fabric_settings"].is_required() is True
    assert model_fields["controllers"].annotation == list[Controller]
    assert model_fields["switches"].annotation == list[Switch]


def test_fabric_model_tree_does_not_reference_raw_types() -> None:
    """The normalized model must not depend on raw workbook types."""
    for model_name in [
        "Controller",
        "Switch",
        "Interface",
        "InterfaceGroup",
        "MatchRule",
        "Policy",
        "ServiceNode",
        "AnalyticsNode",
        "RecorderNode",
        "FabricSettings",
        "Site",
        "Fabric",
    ]:
        model_type = getattr(fabric, model_name)
        for annotation in get_type_hints(model_type, include_extras=True).values():
            assert _contains_raw_type(annotation) is False


def test_fabric_settings_secret_fields_are_wrapped() -> None:
    """Secret-bearing settings should use secret-aware types."""
    settings = FabricSettings.model_validate(
        {
            "fabric_name": "fabric-a",
            "snmp_community": "public",
            "enable_password": "generated-secret",
            "api_token": "generated-token",
        }
    )

    assert isinstance(settings.snmp_community, SecretStr)
    assert isinstance(settings.enable_password, SecretStr)
    assert isinstance(settings.api_token, SecretStr)
