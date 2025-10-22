"""Performance analysis for database controllers."""

from typing import Any, TypeVar

from loguru import logger
from sqlalchemy import text
from sqlmodel import SQLModel

from tux.database.service import DatabaseService

ModelT = TypeVar("ModelT", bound=SQLModel)


class PerformanceController[ModelT]:
    """Handles query analysis and performance statistics."""

    def __init__(self, model: type[ModelT], db: DatabaseService) -> None:
        """Initialize the performance controller.

        Parameters
        ----------
        model : type[ModelT]
            The SQLModel to analyze performance for.
        db : DatabaseService
            The database service instance.
        """
        self.model = model
        self.db = db

    async def get_table_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive table statistics.

        Returns
        -------
        dict[str, Any]
            Dictionary containing table statistics, column stats, and size info.
        """
        async with self.db.session() as session:
            table_name = getattr(self.model, "__tablename__", "unknown")

            # Get basic table stats
            stats_query = text("""
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE tablename = :table_name
            """)

            result = await session.execute(stats_query, {"table_name": table_name})
            stats = result.fetchall()

            # Get table size information
            size_query = text("""
                SELECT
                    pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                    pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                    pg_size_pretty(pg_indexes_size(:table_name)) as indexes_size
            """)

            size_result = await session.execute(size_query, {"table_name": table_name})
            size_info = size_result.fetchone()

            return {
                "table_name": table_name,
                "column_stats": [dict(row._mapping) for row in stats],  # type: ignore[attr-defined]
                "size_info": dict(size_info._mapping) if size_info else {},  # type: ignore[attr-defined]
            }

    async def explain_query_performance(
        self,
        query: Any,
        analyze: bool = False,
        buffers: bool = False,
    ) -> dict[str, Any]:
        """
        Explain query performance with optional analysis.

        Returns
        -------
        dict[str, Any]
            Dictionary containing query execution plan and statistics.
        """
        async with self.db.session() as session:
            try:
                # Build EXPLAIN options
                options = ["VERBOSE", "FORMAT JSON"]
                if analyze:
                    options.append("ANALYZE")
                if buffers:
                    options.append("BUFFERS")

                explain_options = ", ".join(options)
                explain_query = text(f"EXPLAIN ({explain_options}) {query}")

                result = await session.execute(explain_query)
                explanation = result.fetchone()

                return {
                    "query": str(query),
                    "explanation": explanation[0] if explanation else None,
                    "analyzed": analyze,
                    "buffers_included": buffers,
                }

            except Exception as e:
                logger.error(f"Error explaining query: {e}")
                return {
                    "query": str(query),
                    "error": str(e),
                    "explanation": None,
                }
