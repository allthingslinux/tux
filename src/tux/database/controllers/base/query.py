"""Query operations for database controllers."""

from typing import Any, TypeVar

from loguru import logger
from sqlalchemy import UnaryExpression, func
from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel, select

from tux.database.service import DatabaseService

from .filters import build_filters_for_model

ModelT = TypeVar("ModelT", bound=SQLModel)

# Type alias for order_by parameter - accepts column expressions from .asc()/.desc()
OrderByType = UnaryExpression[Any] | tuple[UnaryExpression[Any], ...] | list[UnaryExpression[Any]]


class QueryController[ModelT]:
    """Handles query building, filtering, and advanced searches."""

    def __init__(self, model: type[ModelT], db: DatabaseService) -> None:
        """Initialize the query controller.

        Parameters
        ----------
        model : type[ModelT]
            The SQLModel to query.
        db : DatabaseService
            The database service instance.
        """
        self.model = model
        self.db = db

    def build_filters(self, filters: Any) -> Any:
        """Build filter expressions from various input types."""
        return build_filters_for_model(filters, self.model)

    async def find_one(
        self,
        filters: Any | None = None,
        order_by: OrderByType | None = None,
    ) -> ModelT | None:
        """Find one record."""
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                # Unpack tuple/list for multiple order_by columns
                stmt = stmt.order_by(*order_by) if isinstance(order_by, (tuple, list)) else stmt.order_by(order_by)
            result = await session.execute(stmt)
            instance = result.scalars().first()
            if instance:
                # Expunge the instance so it can be used in other sessions
                session.expunge(instance)
            return instance

    async def find_all(
        self,
        filters: Any | None = None,
        order_by: OrderByType | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelT]:
        """Find all records with performance optimizations."""
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                # Unpack tuple/list for multiple order_by columns
                stmt = stmt.order_by(*order_by) if isinstance(order_by, (tuple, list)) else stmt.order_by(order_by)
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)

            logger.debug(
                f"Executing find_all query on {self.model.__name__} (limit={limit}, has_filters={filters is not None})",
            )
            result = await session.execute(stmt)
            instances = list(result.scalars().all())
            # Expunge all instances so they can be used in other sessions
            for instance in instances:
                session.expunge(instance)
            return instances

    async def find_all_with_options(
        self,
        filters: Any | None = None,
        order_by: OrderByType | None = None,
        limit: int | None = None,
        offset: int | None = None,
        load_relationships: list[str] | None = None,
    ) -> list[ModelT]:
        """Find all records with relationship loading options."""
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                # Unpack tuple/list for multiple order_by columns
                stmt = stmt.order_by(*order_by) if isinstance(order_by, (tuple, list)) else stmt.order_by(order_by)
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
            if load_relationships:
                for relationship in load_relationships:
                    stmt = stmt.options(selectinload(getattr(self.model, relationship)))
            result = await session.execute(stmt)
            instances = list(result.scalars().all())
            # Expunge all instances so they can be used in other sessions
            for instance in instances:
                session.expunge(instance)
            return instances

    async def count(self, filters: Any | None = None) -> int:
        """Count records."""
        async with self.db.session() as session:
            stmt = select(func.count()).select_from(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            result = await session.execute(stmt)
            count = result.scalar() or 0
            logger.debug(f"Count query on {self.model.__name__}: {count} records (has_filters={filters is not None})")
            return count

    async def get_all(self, filters: Any | None = None, order_by: Any | None = None) -> list[ModelT]:
        """Get all records (alias for find_all without pagination)."""
        return await self.find_all(filters=filters, order_by=order_by)

    async def execute_query(self, query: Any) -> Any:
        """Execute a custom query."""
        async with self.db.session() as session:
            return await session.execute(query)

    async def find_with_json_query(
        self,
        json_column: str,
        json_path: str,
        value: Any,
        filters: Any | None = None,
    ) -> list[ModelT]:
        """Find records using JSON column queries."""
        async with self.db.session() as session:
            json_col = getattr(self.model, json_column)
            stmt = select(self.model).where(json_col[json_path].as_string() == str(value))

            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def find_with_array_contains(
        self,
        array_column: str,
        value: Any,
        filters: Any | None = None,
    ) -> list[ModelT]:
        """Find records where array column contains value."""
        async with self.db.session() as session:
            array_col = getattr(self.model, array_column)
            stmt = select(self.model).where(array_col.contains([value]))

            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def find_with_full_text_search(
        self,
        search_columns: list[str],
        search_term: str,
        filters: Any | None = None,
    ) -> list[ModelT]:
        """Find records using full-text search."""
        async with self.db.session() as session:
            search_vector = func.to_tsvector(
                "english",
                func.concat(*[getattr(self.model, col) for col in search_columns]),
            )
            search_query = func.plainto_tsquery("english", search_term)

            stmt = select(self.model).where(search_vector.match(search_query))

            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)

            result = await session.execute(stmt)
            return list(result.scalars().all())
