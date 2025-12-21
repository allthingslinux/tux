"""
Command: dev all.

Runs all development checks including linting, type checking, and documentation.
"""

from collections.abc import Callable
from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.dev.format import format_code
from scripts.dev.lint import lint
from scripts.dev.lint_docstring import lint_docstring
from scripts.dev.lint_fix import lint_fix
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


@app.command(name="all")
def run_all_checks(
    fix: Annotated[
        bool,
        Option("--fix", help="Automatically fix issues where possible"),
    ] = False,
) -> None:
    """Run all development checks including linting, type checking, and documentation."""
    print_section("Running All Development Checks", "blue")

    checks: list[tuple[str, Callable[[], None]]] = [
        ("Linting", lint_fix if fix else lint),
        ("Code Formatting", format_code),
        ("Type Checking", type_check),
        ("Docstring Linting", lint_docstring),
        ("Pre-commit Checks", pre_commit),
    ]

    results: list[tuple[str, bool]] = []

    with create_progress_bar("Running Development Checks", len(checks)) as progress:
        task = progress.add_task("Running Development Checks", total=len(checks))

        for check_name, check_func in checks:
            progress.update(task, description=f"Running {check_name}...")
            progress.refresh()

            try:
                # Note: These functions call sys.exit(1) on failure.
                # In a combined run, we might want them to raise an exception instead.
                # For now, we'll try to catch exceptions if any, but they might still exit.
                check_func()
                results.append((check_name, True))
            except SystemExit as e:
                if e.code == 0:
                    results.append((check_name, True))
                else:
                    results.append((check_name, False))
            except Exception:
                results.append((check_name, False))

            progress.advance(task)
            progress.refresh()

    rich_print("")
    print_section("Development Checks Summary", "blue")

    passed = sum(bool(success) for _, success in results)
    total = len(results)

    table_data: list[tuple[str, str, str]] = [
        (
            check_name,
            "PASSED" if success else "FAILED",
            "Completed" if success else "Failed",
        )
        for check_name, success in results
    ]

    print_table(
        "",
        [("Check", "cyan"), ("Status", "green"), ("Details", "white")],
        table_data,
    )

    rich_print("")
    if passed == total:
        print_success(f"All {total} checks passed!")
    else:
        print_error(f"{passed}/{total} checks passed")
        raise Exit(1)


if __name__ == "__main__":
    app()
