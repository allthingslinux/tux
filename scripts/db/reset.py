"""
Command: db reset.

Resets the database to a clean state via migrations.
"""

import os
import sys
from subprocess import CalledProcessError

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print
from tux.shared.config import CONFIG

app = create_app()


@app.command(name="reset")
def reset() -> None:
    """Reset database to clean state via migrations."""
    # Safety check: prevent running against development database in test mode
    # unless explicitly allowed via TEST_DATABASE_URL or ALLOW_TEST_RESET
    is_test = (
        os.getenv("PYTEST_CURRENT_TEST") is not None
        or os.getenv("PYTEST") is not None
        or "pytest" in sys.modules
    )
    if is_test:
        db_url = CONFIG.database_url
        test_db_url = os.getenv("TEST_DATABASE_URL")
        if test_db_url and db_url != test_db_url:
            if os.getenv("ALLOW_TEST_RESET") != "true":
                print_error(
                    "CRITICAL: Tests are trying to reset a database that doesn't match TEST_DATABASE_URL!",
                )
                rich_print(
                    f"[yellow]Current database URL: {db_url}[/yellow]",
                )
                rich_print(
                    f"[yellow]Expected test database URL: {test_db_url}[/yellow]",
                )
                rich_print(
                    "[yellow]If you are absolutely sure, set ALLOW_TEST_RESET=true environment variable.[/yellow]",
                )
                raise SystemExit(1)
            rich_print(
                "[yellow]ALLOW_TEST_RESET detected. Proceeding with reset in test mode...[/yellow]",
            )

    print_section("Reset Database", "yellow")
    rich_print("[bold yellow]This will reset your database![/bold yellow]")
    rich_print("[yellow]Downgrading to base and reapplying all migrations...[/yellow]")

    try:
        run_command(["uv", "run", "alembic", "downgrade", "base"])
    except CalledProcessError:
        print_error("Failed to downgrade database")
        raise

    try:
        run_command(["uv", "run", "alembic", "upgrade", "head"])
        print_success("Database reset and migrations reapplied!")
    except CalledProcessError:
        print_error("Failed to reapply migrations")
        print_error("WARNING: Database is at base state with no migrations!")
        raise


if __name__ == "__main__":
    app()
