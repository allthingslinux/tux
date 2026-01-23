"""
Command: db fix-sequences.

Fixes PostgreSQL sequence synchronization issues.

When sequences get out of sync (e.g., after manual data insertion or restoration),
this command resets all sequences to the maximum ID value in their respective tables.
"""

import asyncio
from dataclasses import dataclass
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


@dataclass
class SequenceFixPlan:
    """Plan for fixing a sequence that is out of sync."""

    sequence: str
    table: str
    column: str
    current_seq: int
    max_id: int
    next_value: int
    new_value: int


async def get_sequences(session: AsyncSession) -> list[dict[str, Any]]:
    """Get all sequences and their associated tables.

    Parameters
    ----------
    session : AsyncSession
        The database session.

    Returns
    -------
    list[dict[str, Any]]
        List of sequence information dictionaries.
    """
    result = await session.execute(text(FIND_SEQUENCES_SQL))
    rows = result.fetchall()
    sequences: list[dict[str, Any]] = []
    for row in rows:
        table_name = row[0]
        column_name = row[1]
        sequence_name = row[2]

        if not sequence_name:
            continue

        # Store schema-qualified sequence name to avoid search_path issues
        sequences.append(
            {
                "sequence": sequence_name,
                "table": table_name,
                "column": column_name,
            },
        )
    return sequences


async def get_sequence_status(
    session: AsyncSession,
    table_name: str,
    column_name: str,
    sequence_name: str,
) -> dict[str, Any]:
    """Get the current status of a sequence.

    Parameters
    ----------
    session : AsyncSession
        The database session.
    table_name : str
        The table name.
    column_name : str
        The column name.
    sequence_name : str
        The sequence name.

    Returns
    -------
    dict[str, Any]
        Dictionary containing sequence status information.
    """
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


async def reset_sequence(
    session: AsyncSession,
    sequence_name: str,
    reset_value: int,
) -> None:
    """Reset the sequence to the correct value.

    Parameters
    ----------
    session : AsyncSession
        The database session.
    sequence_name : str
        The sequence name.
    reset_value : int
        The value to reset the sequence to.
    """
    await session.execute(
        text(f"SELECT setval('{sequence_name}', {reset_value}, true)"),
    )
    await session.commit()


def plan_sequence_fix(status: dict[str, Any]) -> SequenceFixPlan | None:
    """Create a fix plan for a sequence if it needs fixing.

    Parameters
    ----------
    status : dict[str, Any]
        The sequence status dictionary from `get_sequence_status`.

    Returns
    -------
    SequenceFixPlan | None
        A fix plan if the sequence needs fixing, None otherwise.
    """
    # Skip Discord snowflake IDs (externally-provided)
    if status["max_id"] >= DISCORD_SNOWFLAKE_MIN:
        return None

    # Skip if sequence is already in sync
    if not status["needs_fix"]:
        return None

    new_value = max(status["max_id"], 1)
    return SequenceFixPlan(
        sequence=status["sequence"],
        table=status["table"],
        column=status["column"],
        current_seq=status["current_seq"],
        max_id=status["max_id"],
        next_value=status["next_value"],
        new_value=new_value,
    )


async def _plan_sequence_fixes(
    service: DatabaseService,
    sequences: list[dict[str, Any]],
) -> list[SequenceFixPlan]:
    """Plan fixes for all sequences that need them.

    Parameters
    ----------
    service : DatabaseService
        The database service instance.
    sequences : list[dict[str, Any]]
        List of sequence information dictionaries.

    Returns
    -------
    list[SequenceFixPlan]
        List of fix plans for sequences that need fixing.
    """
    plans: list[SequenceFixPlan] = []

    for seq_info in sequences:
        table = seq_info["table"]
        column = seq_info["column"]
        sequence = seq_info["sequence"]

        # Get sequence status
        seq_status = await service.execute_query(
            lambda s, t=table, c=column, q=sequence: get_sequence_status(
                s,
                t,
                c,
                q,
            ),
            "check_sequence",
        )

        # Check if this is a Discord snowflake ID (externally-provided)
        if seq_status["max_id"] >= DISCORD_SNOWFLAKE_MIN:
            rich_print(
                f"[blue]i Skipping {seq_status['sequence']} - "
                f"appears to be externally-provided Discord ID "
                f"(max: {seq_status['max_id']})[/blue]",
            )
            continue

        # Check if sequence is in sync
        if not seq_status["needs_fix"]:
            rich_print(
                f"[green]✓ Sequence {seq_status['sequence']} is in sync "
                f"(next: {seq_status['next_value']}, max: {seq_status['max_id']})[/green]",
            )
            continue

        if plan := plan_sequence_fix(seq_status):
            plans.append(plan)
            rich_print(
                f"\n[yellow]⚠ Sequence {plan.sequence} is out of sync:[/yellow]",
            )
            rich_print(f"  Current sequence value: {plan.current_seq}")
            rich_print(f"  Max ID in {plan.table}: {plan.max_id}")
            rich_print(f"  Next value would be: {plan.next_value}")
            rich_print(f"  [green]Will reset to: {plan.new_value}[/green]")

    return plans


async def _apply_sequence_fixes(
    service: DatabaseService,
    plans: list[SequenceFixPlan],
    dry_run: bool,
) -> int:
    """Apply sequence fixes or show dry-run messages.

    Parameters
    ----------
    service : DatabaseService
        The database service instance.
    plans : list[SequenceFixPlan]
        List of fix plans to apply.
    dry_run : bool
        If True, only show what would be fixed without making changes.

    Returns
    -------
    int
        Number of fixes applied (0 if dry_run).
    """
    fixes_applied = 0
    for plan in plans:
        if dry_run:
            rich_print(
                f"  [yellow][DRY RUN] Would reset to {plan.new_value}[/yellow]",
            )
        else:
            await service.execute_query(
                lambda s, q=plan.sequence, v=plan.new_value: reset_sequence(
                    s,
                    q,
                    v,
                ),
                "reset_sequence",
            )
            rich_print(f"  [green]✓ Fixed sequence {plan.sequence}[/green]")
            fixes_applied += 1

    return fixes_applied


def _print_summary(
    plans: list[SequenceFixPlan],
    fixes_applied: int,
    dry_run: bool,
) -> None:
    """Print summary of sequence fix operation.

    Parameters
    ----------
    plans : list[SequenceFixPlan]
        List of fix plans.
    fixes_applied : int
        Number of fixes actually applied.
    dry_run : bool
        Whether this was a dry run.
    """
    if fixes_applied > 0:
        print_success(f"Fixed {fixes_applied} sequence(s)")
    elif dry_run:
        if plans:
            rich_print(
                f"[green]Would fix {len(plans)} sequence(s) (dry run)[/green]",
            )
        else:
            rich_print("[green]All sequences are in sync (dry run)[/green]")
    else:
        print_success("All sequences are already in sync")


async def _fix_sequences(dry_run: bool = False) -> None:
    """Fix all sequence synchronization issues.

    Parameters
    ----------
    dry_run : bool, optional
        If True, only show what would be fixed without making changes, by default False.
    """
    service = DatabaseService(echo=False)
    try:
        await service.connect(CONFIG.database_url)

        # Get all sequences
        sequences = await service.execute_query(get_sequences, "get_sequences")

        if not sequences:
            rich_print("[yellow]No sequences found to fix[/yellow]")
            return

        rich_print(f"[blue]Found {len(sequences)} sequence(s) to check:[/blue]")
        for seq_info in sequences:
            rich_print(
                f"  • {seq_info['table']}.{seq_info['column']} -> {seq_info['sequence']}",
            )

        # Planning phase: collect all fix plans
        plans = await _plan_sequence_fixes(service, sequences)

        # Apply phase: execute fixes or show dry-run messages
        fixes_applied = await _apply_sequence_fixes(service, plans, dry_run)

        # Summary
        _print_summary(plans, fixes_applied, dry_run)

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
