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
OrderByType = (
    UnaryExpression[Any] | tuple[UnaryExpression[Any], ...] | list[UnaryExpression[Any]]
)


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
        """
        Build filter expressions from various input types.

        Returns
        -------
        Any
            Combined filter expression, or None if no filters.
        """
        return build_filters_for_model(filters, self.model)

    async def find_one(
        self,
        filters: Any | None = None,
        order_by: OrderByType | None = None,
    ) -> ModelT | None:
        """
        Find one record.

        Returns
        -------
        ModelT | None
            The found record, or None if not found.
        """
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                # Unpack tuple/list for multiple order_by columns
                stmt = (
                    stmt.order_by(*order_by)
                    if isinstance(order_by, (tuple, list))
                    else stmt.order_by(order_by)
                )
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
        """
        Find all records with performance optimizations.

        Returns
        -------
        list[ModelT]
            List of found records.
        """
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                # Unpack tuple/list for multiple order_by columns
                stmt = (
                    stmt.order_by(*order_by)
                    if isinstance(order_by, (tuple, list))
                    else stmt.order_by(order_by)
                )
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
        """
        Find all records with relationship loading options.

        Returns
        -------
        list[ModelT]
            List of found records with loaded relationships.
        """
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                # Unpack tuple/list for multiple order_by columns
                stmt = (
                    stmt.order_by(*order_by)
                    if isinstance(order_by, (tuple, list))
                    else stmt.order_by(order_by)
                )
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
        """
        Count records.

        Returns
        -------
        int
            The count of matching records.
        """
        async with self.db.session() as session:
            stmt = select(func.count()).select_from(self.model)
            filter_expr = self.build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            result = await session.execute(stmt)
            count = result.scalar() or 0
            logger.debug(
                f"Count query on {self.model.__name__}: {count} records (has_filters={filters is not None})",
            )
            return count

    async def get_all(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        """
        Get all records (alias for find_all without pagination).

        Returns
        -------
        list[ModelT]
            List of all matching records.
        """
        return await self.find_all(filters=filters, order_by=order_by)

    async def execute_query(self, query: Any) -> Any:
        """
        Execute a custom query.

        Returns
        -------
        Any
            The query result.
        """
        async with self.db.session() as session:
            return await session.execute(query)
