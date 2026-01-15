"""
Testing Command Group.

Aggregates all testing operations.
"""

from typer import Context

from scripts.core import create_app
from scripts.test import (
    all as all_tests,
)
from scripts.test import (
    benchmark,
    coverage,
    fast,
    file,
    html,
    last_failed,
    parallel,
    plain,
    quick,
)
from scripts.test.quick import quick_tests

app = create_app(name="test", help_text="Testing operations", no_args_is_help=False)

app.add_typer(all_tests.app)
app.add_typer(quick.app)
app.add_typer(plain.app)
app.add_typer(parallel.app)
app.add_typer(file.app)
app.add_typer(html.app)
app.add_typer(coverage.app)
app.add_typer(benchmark.app)
app.add_typer(last_failed.app)
app.add_typer(fast.app)


@app.callback(invoke_without_command=True)
def default_callback(ctx: Context) -> None:
    """Run quick tests if no command specified."""
    if ctx.invoked_subcommand is None:
        quick_tests()


def main() -> None:
    """Entry point for the test command group."""
    app()
