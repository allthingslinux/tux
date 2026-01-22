"""
Command: db fix-sequences.

Fixes PostgreSQL sequence synchronization issues.

When sequences get out of sync (e.g., after manual data insertion or restoration),
this command resets all sequences to the maximum ID value in their respective tables.
"""

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typer import Exit, Option

from scripts.core import create_app
from scripts.ui import (
    print_error,
    print_section,
    print_success,
    rich_print,
)
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()

# SQL to find all sequences and their associated tables
FIND_SEQUENCES_SQL = """
SELECT
    t.table_name,
    c.column_name,
    pg_get_serial_sequence(t.table_schema || '.' || t.table_name, c.column_name) as sequence_name
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name AND t.table_schema = c.table_schema
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_default LIKE 'nextval%'
AND pg_get_serial_sequence(t.table_schema || '.' || t.table_name, c.column_name) IS NOT NULL
ORDER BY t.table_name, c.column_name
"""

# SQL to get max ID for a table (use parameterized query for safety)
# Note: We'll use text() with format for table/column names as they're identifiers, not values

# Discord snowflake IDs are very large (typically 17-19 digits)
# If max_id is >= this value, it's likely an externally-provided Discord ID
DISCORD_SNOWFLAKE_MIN = 1000000000000000  # 10^15 (smallest valid Discord snowflake)


async def _fix_sequences(dry_run: bool = False) -> None:  # noqa: PLR0912, PLR0915
    """Fix all sequence synchronization issues."""
    service = DatabaseService(echo=False)
    try:
        await service.connect(CONFIG.database_url)

        async def _get_sequences(session: AsyncSession) -> list[dict[str, Any]]:
            """Get all sequences and their associated tables."""
            result = await session.execute(text(FIND_SEQUENCES_SQL))
            rows = result.fetchall()
            sequences = []
            for row in rows:
                table_name = row[0]  # table_name
                column_name = row[1]  # column_name
                sequence_name = row[
                    2
                ]  # sequence_name (full path like "public.cases_id_seq")

                if sequence_name:
                    # Extract just the sequence name without schema
                    # "public.cases_id_seq" -> "cases_id_seq"
                    seq_name = (
                        sequence_name.split(".")[-1]
                        if "." in sequence_name
                        else sequence_name
                    )
                    sequences.append(
                        {
                            "sequence": seq_name,
                            "table": table_name,
                            "column": column_name,
                            "full_sequence": sequence_name,
                        },
                    )
            return sequences

        sequences = await service.execute_query(_get_sequences, "get_sequences")

        if not sequences:
            rich_print("[yellow]No sequences found to fix[/yellow]")
            return

        rich_print(f"[blue]Found {len(sequences)} sequence(s) to check:[/blue]")
        for seq_info in sequences:
            rich_print(
                f"  • {seq_info['table']}.{seq_info['column']} -> {seq_info['sequence']}",
            )

        fixes_applied = 0

        for seq_info in sequences:
            table = seq_info["table"]
            column = seq_info["column"]
            sequence = seq_info["sequence"]

            async def _check_and_fix_sequence(
                session: AsyncSession,
                table_name: str = table,
                column_name: str = column,
                sequence_name: str = sequence,
            ) -> dict[str, Any]:
                """Check current sequence value and fix if needed."""
                # Get current sequence value
                current_seq_result = await session.execute(
                    text(f"SELECT last_value, is_called FROM {sequence_name}"),
                )
                current_seq_row = current_seq_result.fetchone()
                current_seq_value = current_seq_row[0] if current_seq_row else 0
                is_called = current_seq_row[1] if current_seq_row else False

                # Get max ID from table (table and column are safe identifiers)
                max_id_result = await session.execute(
                    text(f"SELECT COALESCE(MAX({column_name}), 0) FROM {table_name}"),
                )
                max_id = max_id_result.scalar() or 0

                # Determine next value that would be generated
                next_value = current_seq_value + 1 if is_called else current_seq_value

                return {
                    "sequence": sequence_name,
                    "table": table_name,
                    "column": column_name,
                    "current_seq": current_seq_value,
                    "max_id": max_id,
                    "next_value": next_value,
                    "needs_fix": next_value <= max_id,
                }

            seq_status = await service.execute_query(
                _check_and_fix_sequence,
                "check_sequence",
            )

            # Discord snowflake IDs are very large (typically 17-19 digits)
            # If max_id is a Discord snowflake, this is an externally-provided ID
            # and the sequence shouldn't be reset
            is_discord_id = seq_status["max_id"] >= DISCORD_SNOWFLAKE_MIN

            if is_discord_id:
                rich_print(
                    f"[blue]i Skipping {seq_status['sequence']} - "
                    f"appears to be externally-provided Discord ID "
                    f"(max: {seq_status['max_id']})[/blue]",
                )
                continue

            if seq_status["needs_fix"]:
                new_value = max(seq_status["max_id"], 1)
                rich_print(
                    f"\n[yellow]⚠ Sequence {seq_status['sequence']} is out of sync:[/yellow]",
                )
                rich_print(f"  Current sequence value: {seq_status['current_seq']}")
                rich_print(f"  Max ID in {seq_status['table']}: {seq_status['max_id']}")
                rich_print(f"  Next value would be: {seq_status['next_value']}")
                rich_print(f"  [green]Will reset to: {new_value}[/green]")

                if not dry_run:

                    async def _reset_sequence(
                        session: AsyncSession,
                        sequence_name: str = sequence,
                        reset_value: int = new_value,
                    ) -> None:
                        """Reset the sequence to the correct value."""
                        await session.execute(
                            text(
                                f"SELECT setval('{sequence_name}', {reset_value}, true)",
                            ),
                        )
                        await session.commit()

                    await service.execute_query(_reset_sequence, "reset_sequence")
                    rich_print(f"  [green]✓ Fixed sequence {sequence}[/green]")
                    fixes_applied += 1
                else:
                    rich_print(
                        f"  [yellow][DRY RUN] Would reset to {new_value}[/yellow]",
                    )
            else:
                rich_print(
                    f"[green]✓ Sequence {seq_status['sequence']} is in sync "
                    f"(next: {seq_status['next_value']}, max: {seq_status['max_id']})[/green]",
                )

        if fixes_applied > 0:
            print_success(f"Fixed {fixes_applied} sequence(s)")
        elif dry_run:
            rich_print("[green]All sequences are in sync (dry run)[/green]")
        else:
            print_success("All sequences are already in sync")

    except Exception as e:
        print_error(f"Failed to fix sequences: {e}")
        raise Exit(1) from e
    finally:
        await service.disconnect()


@app.command(name="fix-sequences")
def fix_sequences(
    dry_run: bool = Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be fixed without making changes",
    ),
) -> None:
    """Fix PostgreSQL sequence synchronization issues.

    Resets all sequences to the maximum ID value in their respective tables.
    This fixes duplicate key violations caused by sequences being out of sync.
    """
    print_section("Fix Database Sequences", "yellow")

    if dry_run:
        rich_print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    rich_print(
        "[bold yellow]This will reset sequences to match the maximum ID in each table.[/bold yellow]",
    )
    rich_print(
        "[yellow]Useful for fixing duplicate key violations after data restoration.[/yellow]\n",
    )

    asyncio.run(_fix_sequences(dry_run=dry_run))


if __name__ == "__main__":
    app()
