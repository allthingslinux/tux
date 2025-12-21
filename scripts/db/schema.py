"""
Command: db schema.

Validates that database schema matches model definitions.
"""

import asyncio

from typer import Exit

from scripts.core import create_app
from scripts.ui import (
    create_progress_bar,
    print_error,
    print_section,
    print_success,
    rich_print,
)
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


def _fail():
    """Raise Exit(1) to satisfy Ruff's TRY301 rule."""
    raise Exit(1)


@app.command(name="schema")
def schema() -> None:
    """Validate that database schema matches model definitions."""
    print_section("Schema Validation", "blue")
    rich_print("[bold blue]Validating database schema against models...[/bold blue]")

    async def _schema_check():
        try:
            with create_progress_bar("Validating schema...") as progress:
                progress.add_task("Validating schema against models...", total=None)
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)
                schema_result = await service.validate_schema()
                await service.disconnect()

            if schema_result["status"] == "valid":
                rich_print("[green]Database schema validation passed![/green]")
                rich_print(
                    "[green]All tables and columns match model definitions.[/green]",
                )
            else:
                error_msg = schema_result.get(
                    "error",
                    "Unknown schema validation error",
                )
                rich_print("[red]Database schema validation failed![/red]")
                rich_print(f"[red]Error: {error_msg}[/red]\n")
                rich_print("[yellow]Suggested fixes:[/yellow]")
                rich_print("  • Run 'uv run db reset' to reset and reapply migrations")
                rich_print(
                    "  • Run 'uv run db nuke --force' for complete database reset",
                )
                rich_print(
                    "  • Check that your models match the latest migration files",
                )

                _fail()

            print_success("Schema validation completed")

        except Exception as e:
            if not isinstance(e, Exit):
                print_error(f"Failed to validate database schema: {e}")
                raise Exit(1) from e
            raise

    asyncio.run(_schema_check())


if __name__ == "__main__":
    app()
