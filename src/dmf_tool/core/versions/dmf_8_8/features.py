"""DMF 8.8 feature definitions."""

SUPPORTED_FEATURES = frozenset(
    {
        "analytics_node",
        "basic_policy",
        "delivery_interface",
        "filter_interface",
        "ha_controller",
        "interface_group",
        "match_rule_ip",
        "match_rule_port",
        "match_rule_protocol",
        "match_rule_vlan",
        "ntp",
        "recorder_node",
        "service_node",
        "snmp",
        "syslog",
    }
)
