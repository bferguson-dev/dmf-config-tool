"""Shared Jinja rendering helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import FileSystemLoader, StrictUndefined
from jinja2.sandbox import SandboxedEnvironment
from pydantic import SecretStr

from dmf_tool.core.models.fabric import Fabric
from dmf_tool.core.versions.base import VersionBundle


def build_environment(template_dir: Path) -> SandboxedEnvironment:
    """Build the shared sandboxed Jinja environment."""
    environment = SandboxedEnvironment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    environment.filters["secret_value"] = secret_value
    return environment


def secret_value(value: object) -> object:
    """Unwrap secret values for sensitive config rendering."""
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    return value


def render_config(
    version_bundle: VersionBundle,
    fabric: Fabric,
    provenance: dict[str, Any],
) -> str:
    """Render the top-level config template for a fabric."""
    environment = build_environment(version_bundle.template_dir)
    template = environment.get_template("config.j2")
    return template.render(fabric=fabric, provenance=provenance)
