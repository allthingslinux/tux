"""
Development Command Group.

Aggregates all code quality and development tools.
"""

from scripts.core import create_app
from scripts.dev import (
    all as all_checks,
)
from scripts.dev import (
    clean,
    docstring_coverage,
    lint,
    lint_docstring,
    lint_fix,
    pre_commit,
    type_check,
)
from scripts.dev import (
    format as format_code,
)

app = create_app(name="dev", help_text="Development tools")

app.add_typer(lint.app)
app.add_typer(lint_fix.app)
app.add_typer(format_code.app)
app.add_typer(type_check.app)
app.add_typer(lint_docstring.app)
app.add_typer(docstring_coverage.app)
app.add_typer(pre_commit.app)
app.add_typer(clean.app)
app.add_typer(all_checks.app)


def main() -> None:
    """Entry point for the dev command group."""
    app()
