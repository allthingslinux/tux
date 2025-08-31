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


async def _get_postgres_settings(session: Any) -> list[tuple[str, str, str, str, str]]:
    """Get PostgreSQL settings for optimization analysis."""
    from sqlalchemy import text  # noqa: PLC0415

    result = await session.execute(
        text("""
        SELECT name, setting, unit, context, category
        FROM pg_settings
        WHERE name IN (
            'shared_buffers', 'effective_cache_size', 'work_mem',
            'maintenance_work_mem', 'checkpoint_completion_target',
            'wal_buffers', 'default_statistics_target', 'random_page_cost',
            'effective_io_concurrency', 'max_connections', 'autovacuum_vacuum_scale_factor',
            'autovacuum_analyze_scale_factor', 'log_min_duration_statement',
            'synchronous_commit', 'fsync', 'wal_sync_method'
        )
        ORDER BY category, name
    """),
    )
    return result.fetchall()


async def _get_table_statistics(session: Any) -> list[tuple[str, str, str, str, str, str, str, Any, Any]]:
    """Get table statistics for maintenance analysis."""
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
            n_dead_tup as dead_rows,
            last_vacuum,
            last_analyze
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_dead_tup DESC
    """),
    )
    return result.fetchall()


async def _get_index_usage_stats(session: Any) -> list[tuple[str, str, str, str, str, str]]:
    """Get index usage statistics."""
    from sqlalchemy import text  # noqa: PLC0415

    result = await session.execute(
        text("""
        SELECT
            schemaname,
            relname as tablename,
            indexrelname as indexname,
            idx_scan as scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY idx_scan DESC
    """),
    )
    return result.fetchall()


def _analyze_postgres_settings(settings: list[tuple[str, str, str, str, str]]) -> None:
    """Analyze and display PostgreSQL settings."""
    logger.info("📊 PostgreSQL Settings Analysis:")
    logger.info("=" * 50)

    # Group settings by category
    categories: dict[str, list[tuple[str, str, str, str]]] = {}
    for name, setting, unit, context, category in settings:
        if category not in categories:
            categories[category] = []
        categories[category].append((name, setting, unit, context))

    for category, cat_settings in categories.items():
        logger.info(f"\n🔹 {category.upper()}:")
        for name, setting, unit, _context in cat_settings:
            unit_str = f" {unit}" if unit else ""
            logger.info(f"  {name:35} = {setting:15}{unit_str}")


def _analyze_table_maintenance(table_stats: list[tuple[str, str, str, str, str, str, str, Any, Any]]) -> None:
    """Analyze and display table maintenance information."""
    logger.info("\n📋 Table Maintenance Analysis:")
    logger.info("=" * 50)

    if table_stats:
        for stat in table_stats:
            _schema, table, inserts, updates, deletes, live_rows, dead_rows, last_vacuum, last_analyze = stat
            logger.info(f"\n📊 {table}:")
            logger.info(f"  Live rows: {live_rows}")
            logger.info(f"  Dead rows: {dead_rows}")
            logger.info(f"  Operations: {inserts} inserts, {updates} updates, {deletes} deletes")
            logger.info(f"  Last vacuum: {last_vacuum or 'Never'}")
            logger.info(f"  Last analyze: {last_analyze or 'Never'}")

            # Suggest maintenance if needed
            if dead_rows and int(dead_rows) > 0:
                logger.warning(f"    ⚠️  Table has {dead_rows} dead rows - consider VACUUM")
            if not last_analyze:
                logger.warning("    ⚠️  Table has never been analyzed - consider ANALYZE")


def _analyze_index_usage(index_usage: list[tuple[str, str, str, str, str, str]]) -> None:
    """Analyze and display index usage information."""
    logger.info("\n🔍 Index Usage Analysis:")
    logger.info("=" * 50)

    if index_usage:
        for stat in index_usage:
            _schema, table, index, scans, tuples_read, tuples_fetched = stat
            logger.info(f"\n📊 {table}.{index}:")
            logger.info(f"  Scans: {scans}")
            logger.info(f"  Tuples read: {tuples_read}")
            logger.info(f"  Tuples fetched: {tuples_fetched}")

            # Suggest index optimization
            if int(scans) == 0:
                logger.warning("    ⚠️  Index never used - consider removing if not needed")
            elif int(tuples_read) > 0 and int(tuples_fetched) == 0:
                logger.warning("    ⚠️  Index reads tuples but fetches none - check selectivity")


def _provide_optimization_recommendations() -> None:
    """Provide optimization recommendations."""
    logger.info("\n💡 Optimization Recommendations:")
    logger.info("=" * 50)

    logger.info("🔧 IMMEDIATE ACTIONS:")
    logger.info("  1. Run ANALYZE on all tables: make db-analyze")
    logger.info("  2. Check for tables needing VACUUM: make db-vacuum")
    logger.info("  3. Monitor index usage: make db-queries")

    logger.info("\n⚙️  CONFIGURATION OPTIMIZATIONS:")
    logger.info("  1. shared_buffers: Set to 25% of RAM for dedicated DB")
    logger.info("  2. effective_cache_size: Set to 75% of RAM")
    logger.info("  3. work_mem: Increase for complex queries")
    logger.info("  4. maintenance_work_mem: Increase for faster maintenance")

    logger.info("\n🔄 MAINTENANCE SCHEDULE:")
    logger.info("  1. Daily: Check for long-running queries")
    logger.info("  2. Weekly: Run ANALYZE on active tables")
    logger.info("  3. Monthly: Check index usage and remove unused indexes")
    logger.info("  4. As needed: VACUUM tables with high dead row counts")


async def analyze_database_optimization():
    """Analyze database settings and suggest optimizations for self-hosters."""
    logger.info("🔧 Analyzing database optimization opportunities...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        # Get all required data
        settings = await service.execute_query(_get_postgres_settings, "get_settings")
        table_stats = await service.execute_query(_get_table_statistics, "get_table_stats")
        index_usage = await service.execute_query(_get_index_usage_stats, "get_index_usage")

        # Analyze and display results
        _analyze_postgres_settings(settings)
        _analyze_table_maintenance(table_stats)
        _analyze_index_usage(index_usage)
        _provide_optimization_recommendations()

        logger.success("✅ Database optimization analysis completed!")

    except Exception as e:
        logger.error(f"❌ Failed to analyze database optimization: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(analyze_database_optimization())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
