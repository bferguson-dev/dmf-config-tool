"""Canonical fabric models."""

from __future__ import annotations

from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, SecretStr

InterfaceRole = Literal["filter", "delivery", "both"]


class Controller(BaseModel):
    """Canonical controller definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    management_ip: IPvAnyAddress
    cluster_name: str
    role: Literal["active", "standby", "single"]
    ha_peer: str | None = None
    site_name: str
    description: str | None = None


class Switch(BaseModel):
    """Canonical switch definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    management_ip: IPvAnyAddress
    role: InterfaceRole
    site_name: str
    model: str | None = None
    description: str | None = None


class Interface(BaseModel):
    """Canonical interface definition."""

    model_config = ConfigDict(extra="forbid")

    switch_name: str
    name: str
    role: InterfaceRole
    description: str | None = None
    speed: str | None = None
    vlan_id: int | None = None
    enabled: bool = True


class InterfaceGroup(BaseModel):
    """Canonical interface group definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    role: InterfaceRole
    members: list[str] = Field(min_length=1)
    description: str | None = None


class MatchRule(BaseModel):
    """Canonical policy match rule."""

    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1)
    source_ip: str | None = None
    destination_ip: str | None = None
    source_port: int | None = Field(default=None, ge=1, le=65535)
    destination_port: int | None = Field(default=None, ge=1, le=65535)
    vlan_id: int | None = Field(default=None, ge=1, le=4094)
    protocol: str | None = None


class Policy(BaseModel):
    """Canonical policy definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    priority: int = Field(ge=1, le=65535)
    source_interface: str | None = None
    source_group: str | None = None
    delivery_interface: str | None = None
    delivery_group: str | None = None
    action: str
    enabled: bool = True
    description: str | None = None
    match_rules: list[MatchRule] = Field(
        default_factory=lambda: cast(list[MatchRule], [])
    )


class ServiceNode(BaseModel):
    """Canonical service node definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    switch_name: str
    interface_name: str
    management_ip: IPvAnyAddress | None = None
    description: str | None = None


class AnalyticsNode(BaseModel):
    """Canonical analytics node definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    switch_name: str
    interface_name: str
    management_ip: IPvAnyAddress | None = None
    description: str | None = None


class RecorderNode(BaseModel):
    """Canonical recorder node definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    switch_name: str
    interface_name: str
    management_ip: IPvAnyAddress | None = None
    description: str | None = None


class FabricSettings(BaseModel):
    """Canonical fabric settings definition."""

    model_config = ConfigDict(extra="forbid")

    fabric_name: str
    syslog_server: IPvAnyAddress | None = None
    ntp_server: IPvAnyAddress | None = None
    snmp_community: SecretStr | None = None
    enable_password: SecretStr | None = None
    api_token: SecretStr | None = None


class Site(BaseModel):
    """Canonical site definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    location: str | None = None
    timezone: str | None = None
    description: str | None = None


class Fabric(BaseModel):
    """Normalized fabric model."""

    model_config = ConfigDict(extra="forbid")

    dmf_version: str
    controllers: list[Controller] = Field(
        default_factory=lambda: cast(list[Controller], [])
    )
    switches: list[Switch] = Field(default_factory=lambda: cast(list[Switch], []))
    interfaces: list[Interface] = Field(
        default_factory=lambda: cast(list[Interface], [])
    )
    groups: list[InterfaceGroup] = Field(
        default_factory=lambda: cast(list[InterfaceGroup], [])
    )
    policies: list[Policy] = Field(default_factory=lambda: cast(list[Policy], []))
    service_nodes: list[ServiceNode] = Field(
        default_factory=lambda: cast(list[ServiceNode], [])
    )
    analytics_nodes: list[AnalyticsNode] = Field(
        default_factory=lambda: cast(list[AnalyticsNode], [])
    )
    recorder_nodes: list[RecorderNode] = Field(
        default_factory=lambda: cast(list[RecorderNode], [])
    )
    fabric_settings: FabricSettings
    sites: list[Site] = Field(default_factory=lambda: cast(list[Site], []))
