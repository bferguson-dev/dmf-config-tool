"""DMF 8.7 capacity limits."""

# Conservative limits used until exact 8.7 deltas are confirmed.
LIMITS: dict[str, int] = {
    "max_policies": 768,
    "max_interfaces_per_switch": 256,
    "max_groups": 384,
    "max_tunnels": 96,
    "max_switches": 96,
}
