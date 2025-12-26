"""
Command: db schema.

Validates that database schema matches model definitions.
"""

import asyncio

from typer import Exit

from scripts.core import create_app
from scripts.ui import (
    create_status,
    print_error,
    print_section,
    print_success,
    rich_print,
)
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


@app.command(name="schema")
def schema() -> None:
    """Validate that database schema matches model definitions."""
    print_section("Schema Validation", "blue")
    rich_print("[bold blue]Validating database schema against models...[/bold blue]")

    async def _schema_check() -> None:
        service = DatabaseService(echo=False)
        try:
            with create_status("Validating schema against models...") as status:
                await service.connect(CONFIG.database_url)
                schema_result = await service.validate_schema()
                status.update("[bold green]Validation complete![/bold green]")

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

                raise Exit(1)  # noqa: TRY301

            print_success("Schema validation completed")

        except Exception as e:
            if not isinstance(e, Exit):
                print_error(f"Failed to validate database schema: {e}")
                raise Exit(1) from e
            raise
        finally:
            await service.disconnect()

    asyncio.run(_schema_check())


if __name__ == "__main__":
    app()
