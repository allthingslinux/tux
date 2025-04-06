"""Documentation commands for the Tux CLI."""

from tux.cli.core import command_registration_decorator, create_group

# Create the docs command group
docs_group = create_group("docs", "Documentation related commands")


@command_registration_decorator(docs_group, name="serve")
def docs_serve() -> int:
    """Serve documentation locally."""
    from tux.cli.impl.docs import docs_serve as run_docs_serve

    return run_docs_serve()


@command_registration_decorator(docs_group, name="build")
def docs_build() -> int:
    """Build documentation site."""
    from tux.cli.impl.docs import docs_build as run_docs_build

    return run_docs_build()
