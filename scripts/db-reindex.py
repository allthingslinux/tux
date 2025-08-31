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


async def reindex_database_tables():
    """Reindex all database tables for performance optimization."""
    logger.info("🔄 Reindexing database tables...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        # Get list of tables to reindex
        async def _get_tables(session: Any) -> list[str]:
            from sqlalchemy import text  # noqa: PLC0415

            result = await session.execute(
                text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename != 'alembic_version'
                ORDER BY tablename
            """),
            )
            return [row[0] for row in result.fetchall()]

        tables = await service.execute_query(_get_tables, "get_tables")

        if not tables:
            logger.warning("⚠️  No tables found to reindex")
            return 0

        logger.info(f"📋 Found {len(tables)} tables to reindex:")

        for table_name in tables:
            logger.info(f"  🔄 Reindexing {table_name}...")

            try:
                # Reindex the table
                async def _reindex_table(session: Any, table: str = table_name) -> None:
                    from sqlalchemy import text  # noqa: PLC0415

                    await session.execute(text(f'REINDEX TABLE "{table}"'))

                await service.execute_query(_reindex_table, f"reindex_{table_name}")
                logger.success(f"    ✅ {table_name} reindexed successfully")

            except Exception as e:
                logger.error(f"    ❌ Failed to reindex {table_name}: {e}")

    except Exception as e:
        logger.error(f"❌ Failed to reindex tables: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(reindex_database_tables())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
