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


async def show_database_info():
    """Show database information and maintenance status."""
    logger.info("📊 Showing database information...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        # Get database size
        async def _get_db_size(session: Any) -> str:
            from sqlalchemy import text  # noqa: PLC0415

            result = await session.execute(
                text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """),
            )
            return result.scalar()

        db_size = await service.execute_query(_get_db_size, "get_db_size")
        logger.info(f"📊 Database size: {db_size}")

        # Get table statistics
        async def _get_table_stats(session: Any) -> list[tuple[str, str, str, str, str, str, str]]:
            from sqlalchemy import text  # noqa: PLC0415

            result = await session.execute(
                text("""
                SELECT
                    schemaname,
                    relname as tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_dead_tup DESC
            """),
            )
            return result.fetchall()

        table_stats = await service.execute_query(_get_table_stats, "get_table_stats")

        if table_stats:
            logger.info("📋 Table statistics:")
            for stat in table_stats:
                _schema, table, inserts, updates, deletes, live_rows, dead_rows = stat
                logger.info(f"  📊 {table}:")
                logger.info(f"    Live rows: {live_rows}")
                logger.info(f"    Dead rows: {dead_rows}")
                logger.info(f"    Operations: {inserts} inserts, {updates} updates, {deletes} deletes")

        # Get database maintenance info
        async def _get_maintenance_info(session: Any) -> list[tuple[str, str, Any, Any, Any, Any]]:
            from sqlalchemy import text  # noqa: PLC0415

            result = await session.execute(
                text("""
                SELECT
                    schemaname,
                    relname as tablename,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY relname
            """),
            )
            return result.fetchall()

        maintenance_info = await service.execute_query(_get_maintenance_info, "get_maintenance_info")

        if maintenance_info:
            logger.info("🔧 Maintenance information:")
            for info in maintenance_info:
                _schema, table, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze = info
                logger.info(f"  📊 {table}:")
                logger.info(f"    Last vacuum: {last_vacuum or 'Never'}")
                logger.info(f"    Last autovacuum: {last_autovacuum or 'Never'}")
                logger.info(f"    Last analyze: {last_analyze or 'Never'}")
                logger.info(f"    Last autoanalyze: {last_autoanalyze or 'Never'}")

        logger.success("✅ Database information displayed successfully!")
        logger.info("💡 Note: VACUUM operations require special handling and are not included in this script.")

    except Exception as e:
        logger.error(f"❌ Failed to get database information: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(show_database_info())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
