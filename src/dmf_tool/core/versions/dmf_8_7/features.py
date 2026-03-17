"""DMF 8.7 feature definitions."""

# Conservative feature set until version-specific deltas are validated.
SUPPORTED_FEATURES = frozenset(
    {
        "basic_policy",
        "delivery_interface",
        "filter_interface",
        "interface_group",
        "match_rule_ip",
        "match_rule_port",
        "match_rule_protocol",
        "match_rule_vlan",
        "ntp",
        "service_node",
        "snmp",
        "syslog",
    }
)
