"""DMF 8.6 feature definitions."""

# Conservative feature set used until exact 8.6 deltas are confirmed.
SUPPORTED_FEATURES = frozenset(
    {
        "basic_policy",
        "delivery_interface",
        "filter_interface",
        "interface_group",
        "match_rule_ip",
        "match_rule_port",
        "match_rule_vlan",
        "service_node",
        "snmp",
        "syslog",
    }
)
