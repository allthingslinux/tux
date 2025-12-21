"""
Command: dev all.

Runs all development checks including linting, type checking, and documentation.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.dev.format import format_code
from scripts.dev.lint import lint
from scripts.dev.lint_docstring import lint_docstring
from scripts.dev.pre_commit import pre_commit
from scripts.dev.type_check import type_check
from scripts.ui import (
    create_progress_bar,
    print_error,
    print_section,
    print_success,
    print_table,
    rich_print,
)

app = create_app()


@dataclass
class Check:
    """Represents a single development check."""

    name: str
    func: Callable[[], None]


def run_check(check: Check) -> bool:
    """Run a single check, normalizing SystemExit/Exception to a bool result."""
    try:
        check.func()
    except SystemExit as e:
        return e.code == 0 if isinstance(e.code, int) else False
    except Exception as e:
        print_error(f"Unexpected error in {check.name}: {e}")
        return False
    else:
        return True


@app.command(name="all")
def run_all_checks(
    fix: Annotated[
        bool,
        Option("--fix", help="Automatically fix issues where possible"),
    ] = False,
) -> None:
    """Run all development checks including linting, type checking, and documentation."""
    print_section("Running All Development Checks", "blue")

    checks: list[Check] = [
        Check("Linting", lambda: lint(fix=fix)),
        Check("Code Formatting", format_code),
        Check("Type Checking", type_check),
        Check("Docstring Linting", lint_docstring),
        Check("Pre-commit Checks", pre_commit),
    ]

    results: list[tuple[str, bool]] = []

    with create_progress_bar(
        total=len(checks),
    ) as progress:
        task = progress.add_task("Running Development Checks", total=len(checks))

        for check in checks:
            progress.update(task, description=f"Running {check.name}...")
            success = run_check(check)
            results.append((check.name, success))
            progress.advance(task)

    # Summary
    print_section("Development Checks Summary", "blue")

    table_data: list[tuple[str, str]] = [
        (
            check_name,
            "[green]✓ PASSED[/green]" if success else "[red]✗ FAILED[/red]",
        )
        for check_name, success in results
    ]

    print_table(
        "",
        [("Check", "cyan"), ("Status", "white")],
        table_data,
    )

    passed_count = sum(1 for _, success in results if success)
    total_count = len(checks)

    if passed_count == total_count:
        print_success(f"\nAll {total_count} checks passed!")
    else:
        rich_print(f"\n[bold red]{passed_count}/{total_count} checks passed[/bold red]")
        raise Exit(1)


if __name__ == "__main__":
    app()
