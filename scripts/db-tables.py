#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import and initialize the custom Tux logger
import logger_setup  # noqa: F401 # pyright: ignore[reportUnusedImport]
from loguru import logger

from tux.database.service import DatabaseService


async def list_tables():
    """List all database tables with their row counts."""
    logger.info("📋 Listing all database tables...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        # Use direct SQL query to get table information
        async def _get_tables(session: Any) -> list[tuple[str, int]]:
            from sqlalchemy import text  # noqa: PLC0415

            result = await session.execute(
                text("""
                SELECT
                    table_name,
                    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name != 'alembic_version'
                ORDER BY table_name
            """),
            )
            return result.fetchall()

        tables = await service.execute_query(_get_tables, "get_tables")

        if not tables:
            logger.warning("⚠️  No tables found in database")
            return 0

        logger.success(f"✅ Found {len(tables)} tables:")

        for table_info in tables:
            table_name, column_count = table_info
            logger.info(f"  📊 {table_name}: {column_count} columns")

    except Exception as e:
        logger.error(f"❌ Failed to list tables: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(list_tables())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
