"""Documentation commands for the Tux CLI."""

from tux.cli.core import (
    command_registration_decorator,
    create_group,
    run_command,
)

# Create the docs command group
docs_group = create_group("docs", "Documentation related commands")


@command_registration_decorator(docs_group, name="serve")
def docs_serve() -> int:
    """Serve documentation locally."""
    return run_command(["mkdocs", "serve", "-f", "docs/mkdocs.yml"])


@command_registration_decorator(docs_group, name="build")
def docs_build() -> int:
    """Build documentation site."""
    return run_command(["mkdocs", "build", "-f", "docs/mkdocs.yml"])
