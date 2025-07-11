"""Documentation commands for the Tux CLI."""

import pathlib

from loguru import logger

from cli.core import (
    command_registration_decorator,
    create_group,
    run_command,
)

# Create the docs command group
docs_group = create_group("docs", "Documentation related commands")


def find_mkdocs_config() -> str:
    """Find the mkdocs.yml configuration file.

    Returns
    -------
    str
        Path to the mkdocs.yml file
    """

    current_dir = pathlib.Path.cwd()

    # Check if we're in the docs directory
    if (current_dir / "mkdocs.yml").exists():
        return "mkdocs.yml"

    # Check if we're in the root repo with docs subdirectory
    if (current_dir / "docs" / "mkdocs.yml").exists():
        return "docs/mkdocs.yml"
    logger.error("Can't find mkdocs.yml file. Please run from the project root or docs directory.")

    return ""


@command_registration_decorator(docs_group, name="serve")
def docs_serve() -> int:
    """Serve documentation locally."""
    if mkdocs_path := find_mkdocs_config():
        return run_command(["mkdocs", "serve", "--dirty", "-f", mkdocs_path])
    return 1


@command_registration_decorator(docs_group, name="build")
def docs_build() -> int:
    """Build documentation site."""
    if mkdocs_path := find_mkdocs_config():
        return run_command(["mkdocs", "build", "-f", mkdocs_path])
    return 1
