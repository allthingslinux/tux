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


async def check_long_running_queries():
    """Check for long-running database queries."""
    logger.info("🔍 Checking for long-running database queries...")

    try:
        service = DatabaseService(echo=False)
        await service.connect()

        # Execute query to find long-running queries
        async def _get_long_queries(session: Any) -> list[tuple[Any, Any, str, str]]:
            from sqlalchemy import text  # noqa: PLC0415

            result = await session.execute(
                text("""
                SELECT
                    pid,
                    now() - pg_stat_activity.query_start AS duration,
                    query,
                    state
                FROM pg_stat_activity
                WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
                AND state != 'idle'
                ORDER BY duration DESC
            """),
            )
            return result.fetchall()

        long_queries = await service.execute_query(_get_long_queries, "check_long_queries")

        if not long_queries:
            logger.success("✅ No long-running queries found")
            return 0

        logger.warning(f"⚠️  Found {len(long_queries)} long-running queries:")

        for query_info in long_queries:
            pid, duration, query, state = query_info
            logger.warning(f"  🔴 PID {pid}: {state} for {duration}")
            logger.warning(f"     Query: {query[:100]}...")

    except Exception as e:
        logger.error(f"❌ Failed to check queries: {e}")
        return 1

    return 0


def main():
    """Main entry point."""
    exit_code = asyncio.run(check_long_running_queries())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
