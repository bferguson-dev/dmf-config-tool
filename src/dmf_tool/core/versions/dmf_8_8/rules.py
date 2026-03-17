"""DMF 8.8 semantic rules."""

from collections.abc import Callable

from dmf_tool.core.linters.base import LintResult
from dmf_tool.core.models.fabric import Fabric


def _noop_rule(_fabric: Fabric) -> list[LintResult]:
    """Return no findings for the bootstrap semantic ruleset."""
    return []


def build_semantic_rules() -> tuple[Callable[[Fabric], list[LintResult]], ...]:
    """Return the semantic rule callables for DMF 8.8."""
    return (_noop_rule,)
