"""Workbook normalizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from dmf_tool.core.models.fabric import (
    AnalyticsNode,
    Controller,
    Fabric,
    FabricSettings,
    Interface,
    InterfaceGroup,
    InterfaceRole,
    MatchRule,
    Policy,
    RecorderNode,
    ServiceNode,
    Site,
    Switch,
)
from dmf_tool.core.models.workbook import (
    RawAnalyticsNode,
    RawController,
    RawFabricSettings,
    RawGroup,
    RawInterface,
    RawPolicy,
    RawRecorderNode,
    RawServiceNode,
    RawSite,
    RawSwitch,
    RawWorkbook,
)


@dataclass(slots=True)
class NormalizationError(Exception):
    """Structured error raised when normalization cannot complete."""

    message: str

    def __str__(self) -> str:
        return self.message


def _normalize_string(value: str | None) -> str | None:
    """Normalize free-form text to a canonical string."""
    if value is None:
        return None

    normalized = value.strip().lower()
    return normalized or None


def _require(value: str | None, field_name: str) -> str:
    """Return a required normalized string or raise a structured error."""
    normalized = _normalize_string(value)
    if normalized is None:
        msg = f"Missing required value for {field_name}"
        raise NormalizationError(msg)
    return normalized


def _parse_bool(value: str | None, *, default: bool) -> bool:
    """Parse workbook booleans with explicit defaults."""
    normalized = _normalize_string(value)
    if normalized is None:
        return default
    if normalized in {"true", "yes", "1", "enabled"}:
        return True
    if normalized in {"false", "no", "0", "disabled"}:
        return False
    msg = f"Invalid boolean value: {value}"
    raise NormalizationError(msg)


def _parse_int(
    value: str | None,
    field_name: str,
    *,
    default: int | None = None,
) -> int:
    """Parse an integer value or raise a structured error."""
    normalized = _normalize_string(value)
    if normalized is None:
        if default is None:
            msg = f"Missing required integer value for {field_name}"
            raise NormalizationError(msg)
        return default
    try:
        return int(normalized)
    except ValueError as exc:
        msg = f"Invalid integer value for {field_name}: {value}"
        raise NormalizationError(msg) from exc


def _normalize_interface_role(value: str | None, field_name: str) -> InterfaceRole:
    """Normalize an interface-role-like value."""
    normalized = _require(value, field_name)
    if normalized not in {"filter", "delivery", "both"}:
        msg = f"Invalid role value for {field_name}: {value}"
        raise NormalizationError(msg)
    return cast(InterfaceRole, normalized)


def _normalize_controller_role(
    value: str | None,
    field_name: str,
) -> Literal["active", "standby", "single"]:
    """Normalize a controller role value."""
    normalized = _normalize_string(value) or "single"
    if normalized not in {"active", "standby", "single"}:
        msg = f"Invalid role value for {field_name}: {value}"
        raise NormalizationError(msg)
    return cast(Literal["active", "standby", "single"], normalized)


def _register_unique[T](
    registry: dict[str, T],
    key: str,
    item: T,
    collection_name: str,
) -> None:
    """Register a unique canonical object key."""
    if key in registry:
        msg = f"Duplicate canonical key in {collection_name}: {key}"
        raise NormalizationError(msg)
    registry[key] = item


def _normalize_controllers(raw_controllers: list[RawController]) -> list[Controller]:
    registry: dict[str, Controller] = {}
    for controller in raw_controllers:
        normalized = Controller.model_validate(
            {
                "name": _require(controller.name, "controller.name"),
                "management_ip": _require(
                    controller.management_ip,
                    "controller.management_ip",
                ),
                "cluster_name": _require(
                    controller.cluster_name, "controller.cluster_name"
                ),
                "role": _normalize_controller_role(controller.role, "controller.role"),
                "ha_peer": _normalize_string(controller.ha_peer),
                "site_name": _require(controller.site_name, "controller.site_name"),
                "description": _normalize_string(controller.description),
            }
        )
        _register_unique(registry, normalized.name, normalized, "controllers")
    return sorted(registry.values(), key=lambda controller: controller.name)


def _normalize_switches(raw_switches: list[RawSwitch]) -> list[Switch]:
    registry: dict[str, Switch] = {}
    for switch in raw_switches:
        normalized = Switch.model_validate(
            {
                "name": _require(switch.name, "switch.name"),
                "management_ip": _require(switch.management_ip, "switch.management_ip"),
                "role": _normalize_interface_role(switch.role, "switch.role"),
                "site_name": _require(switch.site_name, "switch.site_name"),
                "model": _normalize_string(switch.model),
                "description": _normalize_string(switch.description),
            }
        )
        _register_unique(registry, normalized.name, normalized, "switches")
    return sorted(registry.values(), key=lambda switch: switch.name)


def _normalize_interfaces(raw_interfaces: list[RawInterface]) -> list[Interface]:
    registry: dict[str, Interface] = {}
    for interface in raw_interfaces:
        switch_name = _require(interface.switch_name, "interface.switch_name")
        name = _require(interface.name, "interface.name")
        normalized = Interface.model_validate(
            {
                "switch_name": switch_name,
                "name": name,
                "role": _normalize_interface_role(interface.role, "interface.role"),
                "description": _normalize_string(interface.description),
                "speed": _normalize_string(interface.speed),
                "vlan_id": (
                    _parse_int(interface.vlan_id, "interface.vlan_id")
                    if _normalize_string(interface.vlan_id) is not None
                    else None
                ),
                "enabled": _parse_bool(interface.enabled, default=True),
            }
        )
        _register_unique(
            registry,
            f"{normalized.switch_name}:{normalized.name}",
            normalized,
            "interfaces",
        )
    return sorted(
        registry.values(),
        key=lambda interface: (interface.switch_name, interface.name),
    )


def _normalize_groups(
    raw_groups: list[RawGroup],
    interface_registry: set[str],
) -> list[InterfaceGroup]:
    registry: dict[str, InterfaceGroup] = {}
    for group in raw_groups:
        members = [
            f"{_require(member.switch_name, 'group_member.switch_name')}:"
            f"{_require(member.interface_name, 'group_member.interface_name')}"
            for member in group.members
        ]
        for member_key in members:
            if member_key not in interface_registry:
                msg = f"Group references unknown interface: {member_key}"
                raise NormalizationError(msg)
        normalized = InterfaceGroup.model_validate(
            {
                "name": _require(group.name, "group.name"),
                "role": _normalize_interface_role(group.role, "group.role"),
                "members": sorted(members),
                "description": _normalize_string(group.description),
            }
        )
        _register_unique(registry, normalized.name, normalized, "groups")
    return sorted(registry.values(), key=lambda group: group.name)


def _normalize_match_rules(raw_policy: RawPolicy) -> list[MatchRule]:
    return sorted(
        [
            MatchRule.model_validate(
                {
                    "sequence": _parse_int(rule.sequence, "match_rule.sequence"),
                    "source_ip": _normalize_string(rule.source_ip),
                    "destination_ip": _normalize_string(rule.destination_ip),
                    "source_port": (
                        _parse_int(rule.source_port, "match_rule.source_port")
                        if _normalize_string(rule.source_port) is not None
                        else None
                    ),
                    "destination_port": (
                        _parse_int(
                            rule.destination_port,
                            "match_rule.destination_port",
                        )
                        if _normalize_string(rule.destination_port) is not None
                        else None
                    ),
                    "vlan_id": (
                        _parse_int(rule.vlan_id, "match_rule.vlan_id")
                        if _normalize_string(rule.vlan_id) is not None
                        else None
                    ),
                    "protocol": _normalize_string(rule.protocol),
                }
            )
            for rule in raw_policy.match_rules
        ],
        key=lambda rule: rule.sequence,
    )


def _normalize_policies(
    raw_policies: list[RawPolicy],
    interface_registry: set[str],
    group_registry: set[str],
) -> list[Policy]:
    registry: dict[str, Policy] = {}
    for policy in raw_policies:
        source_interface = _normalize_string(policy.source_interface)
        delivery_interface = _normalize_string(policy.delivery_interface)
        source_group = _normalize_string(policy.source_group)
        delivery_group = _normalize_string(policy.delivery_group)
        if source_interface is not None and source_interface not in interface_registry:
            msg = f"Policy references unknown source interface: {source_interface}"
            raise NormalizationError(msg)
        if (
            delivery_interface is not None
            and delivery_interface not in interface_registry
        ):
            msg = f"Policy references unknown delivery interface: {delivery_interface}"
            raise NormalizationError(msg)
        if source_group is not None and source_group not in group_registry:
            msg = f"Policy references unknown source group: {source_group}"
            raise NormalizationError(msg)
        if delivery_group is not None and delivery_group not in group_registry:
            msg = f"Policy references unknown delivery group: {delivery_group}"
            raise NormalizationError(msg)
        normalized = Policy.model_validate(
            {
                "name": _require(policy.name, "policy.name"),
                "priority": _parse_int(policy.priority, "policy.priority"),
                "source_interface": source_interface,
                "source_group": source_group,
                "delivery_interface": delivery_interface,
                "delivery_group": delivery_group,
                "action": _normalize_string(policy.action) or "forward",
                "enabled": _parse_bool(policy.enabled, default=True),
                "description": _normalize_string(policy.description),
                "match_rules": _normalize_match_rules(policy),
            }
        )
        _register_unique(registry, normalized.name, normalized, "policies")
    return sorted(registry.values(), key=lambda policy: policy.name)


def _normalize_node(
    raw_node: RawServiceNode | RawAnalyticsNode | RawRecorderNode,
    *,
    field_prefix: str,
    interface_registry: set[str],
) -> tuple[str, str, str, str | None]:
    switch_name = _require(raw_node.switch_name, f"{field_prefix}.switch_name")
    interface_name = _require(raw_node.interface_name, f"{field_prefix}.interface_name")
    interface_key = f"{switch_name}:{interface_name}"
    if interface_key not in interface_registry:
        msg = f"{field_prefix} references unknown interface: {interface_key}"
        raise NormalizationError(msg)
    return (
        _require(raw_node.name, f"{field_prefix}.name"),
        switch_name,
        interface_name,
        _normalize_string(raw_node.description),
    )


def _normalize_service_nodes(
    raw_nodes: list[RawServiceNode],
    interface_registry: set[str],
) -> list[ServiceNode]:
    registry: dict[str, ServiceNode] = {}
    for raw_node in raw_nodes:
        name, switch_name, interface_name, description = _normalize_node(
            raw_node,
            field_prefix="service_node",
            interface_registry=interface_registry,
        )
        normalized = ServiceNode.model_validate(
            {
                "name": name,
                "switch_name": switch_name,
                "interface_name": interface_name,
                "management_ip": _normalize_string(raw_node.management_ip),
                "description": description,
            }
        )
        _register_unique(registry, normalized.name, normalized, "service_nodes")
    return sorted(registry.values(), key=lambda node: node.name)


def _normalize_analytics_nodes(
    raw_nodes: list[RawAnalyticsNode],
    interface_registry: set[str],
) -> list[AnalyticsNode]:
    registry: dict[str, AnalyticsNode] = {}
    for raw_node in raw_nodes:
        name, switch_name, interface_name, description = _normalize_node(
            raw_node,
            field_prefix="analytics_node",
            interface_registry=interface_registry,
        )
        normalized = AnalyticsNode.model_validate(
            {
                "name": name,
                "switch_name": switch_name,
                "interface_name": interface_name,
                "management_ip": _normalize_string(raw_node.management_ip),
                "description": description,
            }
        )
        _register_unique(registry, normalized.name, normalized, "analytics_nodes")
    return sorted(registry.values(), key=lambda node: node.name)


def _normalize_recorder_nodes(
    raw_nodes: list[RawRecorderNode],
    interface_registry: set[str],
) -> list[RecorderNode]:
    registry: dict[str, RecorderNode] = {}
    for raw_node in raw_nodes:
        name, switch_name, interface_name, description = _normalize_node(
            raw_node,
            field_prefix="recorder_node",
            interface_registry=interface_registry,
        )
        normalized = RecorderNode.model_validate(
            {
                "name": name,
                "switch_name": switch_name,
                "interface_name": interface_name,
                "management_ip": _normalize_string(raw_node.management_ip),
                "description": description,
            }
        )
        _register_unique(registry, normalized.name, normalized, "recorder_nodes")
    return sorted(registry.values(), key=lambda node: node.name)


def _normalize_fabric_settings(
    raw_settings: RawFabricSettings | None,
) -> FabricSettings:
    if raw_settings is None:
        return FabricSettings(fabric_name="dmf-fabric")

    return FabricSettings.model_validate(
        {
            "fabric_name": (
                _require(raw_settings.fabric_name, "fabric_settings.fabric_name")
                if raw_settings.fabric_name is not None
                else "dmf-fabric"
            ),
            "syslog_server": _normalize_string(raw_settings.syslog_server),
            "ntp_server": _normalize_string(raw_settings.ntp_server),
            "snmp_community": _normalize_string(raw_settings.snmp_community),
            "enable_password": _normalize_string(raw_settings.enable_password),
            "api_token": _normalize_string(raw_settings.api_token),
        }
    )


def _normalize_sites(raw_sites: list[RawSite]) -> list[Site]:
    registry: dict[str, Site] = {}
    for site in raw_sites:
        normalized = Site.model_validate(
            {
                "name": _require(site.name, "site.name"),
                "location": _normalize_string(site.location),
                "timezone": _normalize_string(site.timezone),
                "description": _normalize_string(site.description),
            }
        )
        _register_unique(registry, normalized.name, normalized, "sites")
    return sorted(registry.values(), key=lambda site: site.name)


def normalize_workbook(raw_workbook: RawWorkbook) -> Fabric:
    """Normalize a raw workbook into the canonical fabric model."""
    controllers = _normalize_controllers(raw_workbook.controllers)
    switches = _normalize_switches(raw_workbook.switches)
    interfaces = _normalize_interfaces(raw_workbook.interfaces)
    interface_registry = {
        f"{interface.switch_name}:{interface.name}" for interface in interfaces
    }
    groups = _normalize_groups(raw_workbook.groups, interface_registry)
    group_registry = {group.name for group in groups}
    policies = _normalize_policies(
        raw_workbook.policies,
        interface_registry,
        group_registry,
    )
    service_nodes = _normalize_service_nodes(
        raw_workbook.service_nodes,
        interface_registry,
    )
    analytics_nodes = _normalize_analytics_nodes(
        raw_workbook.analytics_nodes,
        interface_registry,
    )
    recorder_nodes = _normalize_recorder_nodes(
        raw_workbook.recorder_nodes,
        interface_registry,
    )
    sites = _normalize_sites(raw_workbook.sites)
    fabric_settings = _normalize_fabric_settings(raw_workbook.fabric_settings)

    return Fabric(
        dmf_version=_require(raw_workbook.dmf_version, "workbook.dmf_version"),
        controllers=controllers,
        switches=switches,
        interfaces=interfaces,
        groups=groups,
        policies=policies,
        service_nodes=service_nodes,
        analytics_nodes=analytics_nodes,
        recorder_nodes=recorder_nodes,
        fabric_settings=fabric_settings,
        sites=sites,
    )
