"""Raw workbook models."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel, ConfigDict, Field


class RawController(BaseModel):
    """Raw controller row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    management_ip: str | None = None
    cluster_name: str | None = None
    role: str | None = None
    ha_peer: str | None = None
    site_name: str | None = None
    description: str | None = None


class RawSwitch(BaseModel):
    """Raw switch row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    management_ip: str | None = None
    role: str | None = None
    site_name: str | None = None
    model: str | None = None
    description: str | None = None


class RawInterface(BaseModel):
    """Raw interface row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    switch_name: str | None = None
    name: str | None = None
    role: str | None = None
    description: str | None = None
    speed: str | None = None
    vlan_id: str | None = None
    enabled: str | None = None


class RawGroupMember(BaseModel):
    """Raw interface group membership row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    interface_name: str | None = None
    switch_name: str | None = None


class RawGroup(BaseModel):
    """Raw interface group row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    role: str | None = None
    description: str | None = None
    members: list[RawGroupMember] = Field(
        default_factory=lambda: cast(list[RawGroupMember], [])
    )


class RawMatchRule(BaseModel):
    """Raw match rule row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    sequence: str | None = None
    source_ip: str | None = None
    destination_ip: str | None = None
    source_port: str | None = None
    destination_port: str | None = None
    vlan_id: str | None = None
    protocol: str | None = None


class RawPolicy(BaseModel):
    """Raw policy row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    priority: str | None = None
    source_interface: str | None = None
    source_group: str | None = None
    delivery_interface: str | None = None
    delivery_group: str | None = None
    action: str | None = None
    enabled: str | None = None
    description: str | None = None
    match_rules: list[RawMatchRule] = Field(
        default_factory=lambda: cast(list[RawMatchRule], [])
    )


class RawServiceNode(BaseModel):
    """Raw service node row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    switch_name: str | None = None
    interface_name: str | None = None
    management_ip: str | None = None
    description: str | None = None


class RawAnalyticsNode(BaseModel):
    """Raw analytics node row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    switch_name: str | None = None
    interface_name: str | None = None
    management_ip: str | None = None
    description: str | None = None


class RawRecorderNode(BaseModel):
    """Raw recorder node row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    switch_name: str | None = None
    interface_name: str | None = None
    management_ip: str | None = None
    description: str | None = None


class RawFabricSettings(BaseModel):
    """Raw fabric settings tab from the workbook."""

    model_config = ConfigDict(extra="forbid")

    fabric_name: str | None = None
    syslog_server: str | None = None
    ntp_server: str | None = None
    snmp_community: str | None = None
    enable_password: str | None = None
    api_token: str | None = None


class RawSite(BaseModel):
    """Raw site row from the workbook."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    location: str | None = None
    timezone: str | None = None
    description: str | None = None


class RawWorkbook(BaseModel):
    """Root raw workbook model."""

    model_config = ConfigDict(extra="forbid")

    dmf_version: str
    workbook_schema_version: str
    controllers: list[RawController] = Field(
        default_factory=lambda: cast(list[RawController], [])
    )
    switches: list[RawSwitch] = Field(default_factory=lambda: cast(list[RawSwitch], []))
    interfaces: list[RawInterface] = Field(
        default_factory=lambda: cast(list[RawInterface], [])
    )
    groups: list[RawGroup] = Field(default_factory=lambda: cast(list[RawGroup], []))
    policies: list[RawPolicy] = Field(default_factory=lambda: cast(list[RawPolicy], []))
    service_nodes: list[RawServiceNode] = Field(
        default_factory=lambda: cast(list[RawServiceNode], [])
    )
    analytics_nodes: list[RawAnalyticsNode] = Field(
        default_factory=lambda: cast(list[RawAnalyticsNode], [])
    )
    recorder_nodes: list[RawRecorderNode] = Field(
        default_factory=lambda: cast(list[RawRecorderNode], [])
    )
    fabric_settings: RawFabricSettings | None = None
    sites: list[RawSite] = Field(default_factory=lambda: cast(list[RawSite], []))
