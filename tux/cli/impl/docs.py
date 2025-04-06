"""Documentation command implementations."""

from tux.cli.impl.core import run_command


def docs_serve() -> int:
    """Serve documentation locally."""

    return run_command(["mkdocs", "serve", "-f", "docs/mkdocs.yml"])


def docs_build() -> int:
    """Build documentation site."""

    return run_command(["mkdocs", "build", "-f", "docs/mkdocs.yml"])
