"""DMF 8.6 capacity limits."""

# Conservative limits used until exact 8.6 deltas are confirmed.
LIMITS: dict[str, int] = {
    "max_policies": 512,
    "max_interfaces_per_switch": 192,
    "max_groups": 256,
    "max_tunnels": 64,
    "max_switches": 64,
}
