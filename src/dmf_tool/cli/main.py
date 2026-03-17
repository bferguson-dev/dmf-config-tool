"""CLI entry points."""

import click


@click.group()
def cli() -> None:
    """Run the DMF tool command group."""
