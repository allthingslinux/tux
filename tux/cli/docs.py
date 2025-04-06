"""Documentation commands for the Tux CLI."""

from tux.cli.core import command_registration_decorator, create_group

# Create the documentation command group
docs_group = create_group("docs", "Documentation tools and commands")


@command_registration_decorator(docs_group, name="serve")
def serve() -> int:
    """View documentation in browser."""

    from tux.cli.impl.dev import docs as run_docs

    return run_docs()


@command_registration_decorator(docs_group, name="build")
def build() -> int:
    """Build documentation."""

    from tux.cli.impl.dev import docs_build as run_docs_build

    return run_docs_build()
