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


async def analyze_table_statistics():
    """Analyze table statistics for performance optimization."""
    logger.info("📊 Analyzing table statistics...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        # Execute query to analyze table statistics
        async def _analyze_tables(session: Any) -> list[tuple[str, str, Any, Any, Any, Any, Any]]:
            from sqlalchemy import text  # noqa: PLC0415

            result = await session.execute(
                text("""
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation,
                    most_common_vals,
                    most_common_freqs
                FROM pg_stats
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
            """),
            )
            return result.fetchall()

        stats = await service.execute_query(_analyze_tables, "analyze_tables")

        if not stats:
            logger.warning("⚠️  No table statistics found")
            return 0

        logger.success(f"✅ Found statistics for {len(stats)} columns:")

        current_table: str | None = None
        for stat_info in stats:
            _schema, table, column, distinct, correlation, _common_vals, _common_freqs = stat_info

            if table != current_table:
                current_table = table
                logger.info(f"  📋 Table: {table}")

            logger.info(f"    Column: {column}")
            logger.info(f"      Distinct values: {distinct}")
            logger.info(f"      Correlation: {correlation:.3f}")

    except Exception as e:
        logger.error(f"❌ Failed to analyze tables: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(analyze_table_statistics())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
