#!/usr/bin/env python3
"""
Unified CLI Entry Point for Documentation.

This module provides a unified entry point for all CLI commands to be used with mkdocs-typer.
It combines all CLI modules into a single Typer application for documentation generation.
"""

import sys
from pathlib import Path

from typer import Typer

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from scripts.db import DatabaseCLI
from scripts.dev import DevCLI
from scripts.docker_cli import DockerCLI
from scripts.docs import DocsCLI
from scripts.test import TestCLI
from scripts.tux import TuxCLI


def create_unified_cli() -> Typer:
    """Create a unified CLI application that combines all CLI modules."""
    # Create the main app
    cli = Typer(
        name="uv run",
        help="Tux - All Things Linux Discord Bot",
        rich_markup_mode="rich",
        no_args_is_help=True,
    )

    # Create sub-apps for each CLI module
    db_cli = DatabaseCLI()
    dev_cli = DevCLI()
    docker_cli = DockerCLI()
    docs_cli = DocsCLI()
    test_cli = TestCLI()
    tux_cli = TuxCLI()

    # Add each CLI as a subcommand group
    cli.add_typer(db_cli.app, name="db", help="Database operations and management")
    cli.add_typer(dev_cli.app, name="dev", help="Development tools and workflows")
    cli.add_typer(docker_cli.app, name="docker", help="Docker operations and management")
    cli.add_typer(docs_cli.app, name="docs", help="Documentation operations and management")
    cli.add_typer(test_cli.app, name="test", help="Testing operations and management")
    cli.add_typer(tux_cli.app, name="tux", help="Tux bot operations and management")

    return cli


# Create the unified CLI app for documentation
cli = create_unified_cli()


def main() -> None:
    """Entry point for the unified CLI."""
    cli()


if __name__ == "__main__":
    main()
