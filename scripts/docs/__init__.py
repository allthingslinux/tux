"""
Documentation Command Group.

Aggregates all Zensical and Wrangler documentation operations.
"""

from scripts.core import create_app
from scripts.docs import (
    build,
    lint,
    serve,
    wrangler_deploy,
    wrangler_deployments,
    wrangler_dev,
    wrangler_rollback,
    wrangler_tail,
    wrangler_versions,
)

app = create_app(name="docs", help_text="Documentation operations")

app.add_typer(serve.app)
app.add_typer(build.app)
app.add_typer(lint.app)
app.add_typer(wrangler_dev.app)
app.add_typer(wrangler_deploy.app)
app.add_typer(wrangler_deployments.app)
app.add_typer(wrangler_versions.app)
app.add_typer(wrangler_tail.app)
app.add_typer(wrangler_rollback.app)


def main() -> None:
    """Entry point for the docs command group."""
    app()
