from __future__ import annotations

from collections.abc import Awaitable, Callable
from math import ceil
from typing import Any, TypeVar

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import Table, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel, delete, select, update

from tux.database.service import DatabaseService

ModelT = TypeVar("ModelT", bound=SQLModel)
R = TypeVar("R")


class BaseController[ModelT]:
    def __init__(self, model: type[ModelT], db: DatabaseService | None = None):
        self.model = model
        if db is None:
            error_msg = "DatabaseService must be provided. Use DI container to get the service."
            raise RuntimeError(error_msg)
        self.db = db

    # Properties for test compatibility
    @property
    def db_service(self) -> DatabaseService:
        """Database service property for test compatibility."""
        return self.db

    @property
    def model_class(self) -> type[ModelT]:
        """Model class property for test compatibility."""
        return self.model

    # ------------------------------------------------------------------
    # Core CRUD Methods - Direct SQLAlchemy Implementation
    # ------------------------------------------------------------------

    async def create(self, **kwargs: Any) -> ModelT:
        """Create a new record."""
        async with self.db.session() as session:
            instance = self.model(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def get_by_id(self, record_id: Any) -> ModelT | None:
        """Get a record by ID."""
        async with self.db.session() as session:
            return await session.get(self.model, record_id)

    async def find_one(self, filters: Any | None = None, order_by: Any | None = None) -> ModelT | None:
        """Find one record."""
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self._build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def find_all(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelT]:
        """Find all records with performance optimizations."""
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = self._build_filters(filters)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def find_all_with_options(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
        load_relationships: list[str] | None = None,
    ) -> list[ModelT]:
        """Find all records with relationship loading options."""
        async with self.db.session() as session:
            stmt = select(self.model)
            if filters is not None:
                stmt = stmt.where(filters)
            if order_by is not None:
                stmt = stmt.order_by(order_by)

            # Optimized relationship loading
            if load_relationships:
                for relationship in load_relationships:
                    if hasattr(self.model, relationship):
                        stmt = stmt.options(selectinload(getattr(self.model, relationship)))

            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count(self, filters: Any | None = None) -> int:
        """Count records."""
        async with self.db.session() as session:
            stmt = select(func.count()).select_from(self.model)
            if filters is not None:
                stmt = stmt.where(filters)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    # Test compatibility methods
    async def get_all(self, filters: Any | None = None, order_by: Any | None = None) -> list[ModelT]:
        """Get all records. Alias for find_all for test compatibility."""
        return await self.find_all(filters=filters, order_by=order_by)

    async def exists(self, filters: Any) -> bool:
        """Check if any record exists matching the filters."""
        count = await self.count(filters=filters)
        return count > 0

    async def execute_query(self, query: Any) -> Any:
        """Execute an arbitrary query."""
        async with self.db.session() as session:
            return await session.execute(query)

    async def update(self, record_id: Any, **values: Any) -> ModelT | None:
        """Update a record. Alias for update_by_id for test compatibility."""
        return await self.update_by_id(record_id, **values)

    async def delete(self, record_id: Any) -> bool:
        """Delete a record. Alias for delete_by_id for test compatibility."""
        return await self.delete_by_id(record_id)

    # ------------------------------------------------------------------
    # Upsert Operations - Professional Patterns from SQLModel Examples
    # ------------------------------------------------------------------

    async def upsert_by_field(
        self,
        field_name: str,
        field_value: Any,
        **create_values: Any,
    ) -> tuple[ModelT, bool]:
        """
        Create or update a record by a specific field.

        Args:
            field_name: Name of the field to check for existing record
            field_value: Value of the field to check
            **create_values: Values to use when creating new record

        Returns:
            Tuple of (record, created) where created is True if new record was created

        Example:
            user, created = await controller.upsert_by_field(
                "email", "user@example.com",
                name="John Doe", email="user@example.com"
            )
        """
        async with self.db.session() as session:
            # Check if record exists
            existing = await session.execute(select(self.model).where(getattr(self.model, field_name) == field_value))
            existing_record = existing.scalars().first()

            if existing_record is not None:
                # Update existing record with new values
                for key, value in create_values.items():
                    setattr(existing_record, key, value)
                await session.commit()
                await session.refresh(existing_record)
                return existing_record, False
            # Create new record
            instance = self.model(**create_values)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance, True

    async def upsert_by_id(
        self,
        record_id: Any,
        **update_values: Any,
    ) -> tuple[ModelT, bool]:
        """
        Create or update a record by ID.

        Args:
            record_id: ID of the record to upsert
            **update_values: Values to set on the record

        Returns:
            Tuple of (record, created) where created is True if new record was created

        Note:
            This method requires the ID to be provided in update_values for creation.
        """
        async with self.db.session() as session:
            # Check if record exists
            existing_record = await session.get(self.model, record_id)

            if existing_record is not None:
                # Update existing record
                for key, value in update_values.items():
                    setattr(existing_record, key, value)
                await session.commit()
                await session.refresh(existing_record)
                return existing_record, False
            # Create new record - ID must be in update_values
            if "id" not in update_values and record_id is not None:
                update_values["id"] = record_id
            instance = self.model(**update_values)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance, True

    async def get_or_create_by_field(
        self,
        field_name: str,
        field_value: Any,
        **create_values: Any,
    ) -> tuple[ModelT, bool]:
        """
        Get existing record or create new one by field value.

        Args:
            field_name: Name of the field to check
            field_value: Value of the field to check
            **create_values: Values to use when creating new record

        Returns:
            Tuple of (record, created) where created is True if new record was created
        """
        async with self.db.session() as session:
            # Check if record exists
            existing = await session.execute(select(self.model).where(getattr(self.model, field_name) == field_value))
            existing_record = existing.scalars().first()

            if existing_record is not None:
                return existing_record, False
            # Create new record
            instance = self.model(**create_values)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance, True

    # ------------------------------------------------------------------
    # Pagination Support - Professional Patterns from SQLModel Examples
    # ------------------------------------------------------------------

    class Page(BaseModel):
        """
        Represents a page of data in a paginated result set.

        Attributes:
            data: List of items on the current page
            page: Current page number (1-based)
            page_size: Number of items per page
            total: Total number of items across all pages
            total_pages: Total number of pages
            has_previous: Whether there is a previous page
            has_next: Whether there is a next page
            previous_page: Previous page number (or None)
            next_page: Next page number (or None)
        """

        data: list[ModelT]
        page: int
        page_size: int
        total: int
        total_pages: int
        has_previous: bool
        has_next: bool
        previous_page: int | None
        next_page: int | None

        @classmethod
        def create(
            cls,
            data: list[ModelT],
            page: int,
            page_size: int,
            total: int,
        ) -> BaseController.Page[ModelT]:
            """Create a Page instance with calculated pagination information."""
            total_pages = ceil(total / page_size) if page_size > 0 else 0

            return cls(
                data=data,
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
                has_previous=page > 1,
                has_next=page < total_pages,
                previous_page=page - 1 if page > 1 else None,
                next_page=page + 1 if page < total_pages else None,
            )

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 25,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> Page[ModelT]:
        """
        Get a paginated list of records.

        Args:
            page: Page number (1-based, default: 1)
            page_size: Number of items per page (default: 25)
            filters: SQLAlchemy filters to apply
            order_by: SQLAlchemy order by clause

        Returns:
            Page object with data and pagination metadata

        Raises:
            ValueError: If page or page_size are invalid

        Example:
            page = await controller.paginate(page=2, page_size=10)
            print(f"Page {page.page} of {page.total_pages}")
            print(f"Showing {len(page.data)} items of {page.total}")
        """
        if page < 1:
            msg = "Page number must be >= 1"
            raise ValueError(msg)
        if page_size < 1:
            msg = "Page size must be >= 1"
            raise ValueError(msg)

        # Get total count
        total = await self.count(filters=filters)

        # Calculate offset
        offset = (page - 1) * page_size

        # Get paginated data
        data = await self.find_all(
            filters=filters,
            order_by=order_by,
            limit=page_size,
            offset=offset,
        )

        return self.Page.create(
            data=data,
            page=page,
            page_size=page_size,
            total=total,
        )

    async def find_paginated(
        self,
        page: int = 1,
        page_size: int = 25,
        **filters: Any,
    ) -> Page[ModelT]:
        """
        Convenience method for simple paginated queries with keyword filters.

        Args:
            page: Page number (1-based, default: 1)
            page_size: Number of items per page (default: 25)
            **filters: Keyword filters to apply

        Returns:
            Page object with data and pagination metadata

        Example:
            page = await controller.find_paginated(page=1, page_size=10, active=True)
        """
        # Convert keyword filters to SQLAlchemy expressions
        if filters:
            filter_expressions = [getattr(self.model, key) == value for key, value in filters.items()]
            combined_filters = filter_expressions[0] if len(filter_expressions) == 1 else filter_expressions
        else:
            combined_filters = None

        return await self.paginate(
            page=page,
            page_size=page_size,
            filters=combined_filters,
        )

    async def update_by_id(self, record_id: Any, **values: Any) -> ModelT | None:
        """Update record by ID."""
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance is None:
                return None
            for key, value in values.items():
                setattr(instance, key, value)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def update_where(self, filters: Any, values: dict[str, Any]) -> int:
        """Update records matching filters."""
        async with self.db.session() as session:
            stmt = update(self.model).where(filters).values(**values)
            result = await session.execute(stmt)
            return int(getattr(result, "rowcount", 0) or 0)

    async def delete_by_id(self, record_id: Any) -> bool:
        """Delete record by ID."""
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance is None:
                return False
            await session.delete(instance)
            await session.commit()
            return True

    async def delete_where(self, filters: Any) -> int:
        """Delete records matching filters."""
        async with self.db.session() as session:
            stmt = delete(self.model).where(filters)
            result = await session.execute(stmt)
            return int(getattr(result, "rowcount", 0) or 0)

    async def upsert(
        self,
        match_filter: Any,
        create_values: dict[str, Any],
        update_values: dict[str, Any],
    ) -> ModelT:
        """Upsert record."""
        async with self.db.session() as session:
            existing = await self.find_one(filters=match_filter)
            if existing is None:
                return await self.create(**create_values)
            for key, value in update_values.items():
                setattr(existing, key, value)
            await session.commit()
            await session.refresh(existing)
            return existing

    # ------------------------------------------------------------------
    # Session Management Helpers
    # ------------------------------------------------------------------

    async def with_session[R](self, operation: Callable[[AsyncSession], Awaitable[R]]) -> R:
        """Execute operation with automatic session management."""
        async with self.db.session() as session:
            return await operation(session)

    async def with_transaction[R](self, operation: Callable[[AsyncSession], Awaitable[R]]) -> R:
        """Execute operation within a transaction."""
        async with self.db.transaction() as session:
            return await operation(session)

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    def _build_filters(self, filters: Any) -> Any:
        """Convert dictionary filters to SQLAlchemy filter expressions."""
        if filters is None:
            return None

        if isinstance(filters, dict):
            filter_expressions: list[Any] = [getattr(self.model, key) == value for key, value in filters.items()]  # type: ignore[reportUnknownArgumentType]
            return and_(*filter_expressions) if filter_expressions else None  # type: ignore[arg-type]

        # If it's already a proper filter expression, return as-is
        return filters

    async def get_or_create(self, defaults: dict[str, Any] | None = None, **filters: Any) -> tuple[ModelT, bool]:
        """Get a record by filters, or create it if it doesn't exist.

        Parameters
        ----------
        defaults : dict[str, Any] | None, optional
            Default values to use when creating the record
        **filters : Any
            Filter criteria to find the existing record

        Returns
        -------
        tuple[ModelT, bool]
            A tuple containing the record and a boolean indicating if it was created
        """
        # Try to find existing record
        existing = await self.find_one(filters=filters)
        if existing is not None:
            return existing, False

        # Create new record with filters + defaults
        create_data = {**filters}
        if defaults:
            create_data |= defaults

        new_record = await self.create(**create_data)
        return new_record, True

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Execute callback inside a transaction."""
        try:
            async with self.db.transaction():
                return await callback()
        except Exception as exc:
            logger.exception(f"Transaction failed in {self.model.__name__}: {exc}")
            raise

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        """Create multiple records in a single transaction."""
        if not items:
            return []

        async with self.db.session() as session:
            instances: list[ModelT] = []
            for item_data in items:
                instance: ModelT = self.model(**item_data)
                session.add(instance)
                instances.append(instance)

            await session.commit()

            # Refresh all instances to get their IDs
            for instance in instances:
                await session.refresh(instance)

            return instances

    async def bulk_update(self, updates: list[tuple[Any, dict[str, Any]]]) -> int:
        """Update multiple records in a single transaction.

        Args:
            updates: List of tuples (record_id, update_data)
        """
        if not updates:
            return 0

        async with self.db.session() as session:
            total_updated = 0
            for record_id, update_data in updates:
                instance = await session.get(self.model, record_id)
                if instance:
                    for key, value in update_data.items():
                        setattr(instance, key, value)
                    total_updated += 1

            await session.commit()
            return total_updated

    async def bulk_delete(self, record_ids: list[Any]) -> int:
        """Delete multiple records in a single transaction."""
        if not record_ids:
            return 0

        async with self.db.session() as session:
            for record_id in record_ids:
                instance = await session.get(self.model, record_id)
                if instance:
                    await session.delete(instance)

            await session.commit()
            return len(record_ids)

    # ------------------------------------------------------------------
    # PostgreSQL-Specific Features - Based on py-pglite Examples
    # ------------------------------------------------------------------

    async def find_with_json_query(
        self,
        json_field: str,
        json_path: str,
        value: Any,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        """
        Query records using PostgreSQL JSON operators.

        Args:
            json_field: Name of the JSON field to query
            json_path: JSON path expression (e.g., "$.metadata.key")
            value: Value to match
            order_by: Optional ordering clause

        Example:
            guilds = await controller.find_with_json_query(
                "metadata", "$.settings.auto_mod", True
            )
        """
        async with self.db.session() as session:
            # Use PostgreSQL JSON path operators
            stmt = select(self.model).where(
                text(f"{json_field}::jsonb @> :value::jsonb"),
            )

            if order_by is not None:
                stmt = stmt.order_by(order_by)

            result = await session.execute(stmt, {"value": f'{{"{json_path.replace("$.", "")}": {value}}}'})
            return list(result.scalars().all())

    async def find_with_array_contains(
        self,
        array_field: str,
        value: str | list[str],
        order_by: Any | None = None,
    ) -> list[ModelT]:
        """
        Query records where array field contains specific value(s).

        Args:
            array_field: Name of the array field
            value: Single value or list of values to check for
            order_by: Optional ordering clause

        Example:
            guilds = await controller.find_with_array_contains("tags", "gaming")
        """
        async with self.db.session() as session:
            if isinstance(value, str):
                # Single value containment check
                stmt = select(self.model).where(
                    text(f":value = ANY({array_field})"),
                )
                params = {"value": value}
            else:
                # Multiple values overlap check
                stmt = select(self.model).where(
                    text(f"{array_field} && :values"),
                )
                params = {"values": value}

            if order_by is not None:
                stmt = stmt.order_by(order_by)

            result = await session.execute(stmt, params)
            return list(result.scalars().all())

    async def find_with_full_text_search(
        self,
        text_field: str,
        search_query: str,
        rank_order: bool = True,
    ) -> list[tuple[ModelT, float]]:
        """
        Perform full-text search using PostgreSQL's built-in capabilities.

        Args:
            text_field: Field to search in
            search_query: Search query
            rank_order: Whether to order by relevance rank

        Returns:
            List of tuples (model, rank) if rank_order=True, else just models
        """
        async with self.db.session() as session:
            if rank_order:
                stmt = (
                    select(
                        self.model,
                        func.ts_rank(
                            func.to_tsvector("english", getattr(self.model, text_field)),
                            func.plainto_tsquery("english", search_query),
                        ).label("rank"),
                    )
                    .where(
                        func.to_tsvector("english", getattr(self.model, text_field)).match(
                            func.plainto_tsquery("english", search_query),
                        ),
                    )
                    .order_by(text("rank DESC"))
                )

                result = await session.execute(stmt)
                return [(row[0], float(row[1])) for row in result.fetchall()]
            stmt = select(self.model).where(
                func.to_tsvector("english", getattr(self.model, text_field)).match(
                    func.plainto_tsquery("english", search_query),
                ),
            )
            result = await session.execute(stmt)
            return [(model, 0.0) for model in result.scalars().all()]

    async def bulk_upsert_with_conflict_resolution(
        self,
        records: list[dict[str, Any]],
        conflict_columns: list[str],
        update_columns: list[str] | None = None,
    ) -> int:
        """
        Bulk upsert using PostgreSQL's ON CONFLICT capabilities.

        Args:
            records: List of record dictionaries
            conflict_columns: Columns that define uniqueness
            update_columns: Columns to update on conflict (if None, updates all)

        Returns:
            Number of records processed
        """
        if not records:
            return 0

        async with self.db.session() as session:
            # Use PostgreSQL's INSERT ... ON CONFLICT for high-performance upserts
            table: Table = self.model.__table__  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType,reportUnknownVariableType]

            # Build the ON CONFLICT clause
            conflict_clause = ", ".join(conflict_columns)

            if update_columns is None:
                # Update all columns except the conflict columns
                update_columns = [col.name for col in table.columns if col.name not in conflict_columns]  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]

            update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])

            # Build the SQL statement
            columns = ", ".join(records[0].keys())
            placeholders = ", ".join([f":{key}" for key in records[0]])

            table_name_attr = getattr(table, "name", "unknown")  # pyright: ignore[reportUnknownArgumentType]
            sql = f"""
                INSERT INTO {table_name_attr} ({columns})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_clause})
                DO UPDATE SET {update_clause}
            """

            # Execute for all records
            await session.execute(text(sql), records)
            await session.commit()

            return len(records)

    async def get_table_statistics(self) -> dict[str, Any]:
        """
        Get PostgreSQL table statistics for this model.

        Based on py-pglite monitoring patterns.
        """
        async with self.db.session() as session:
            table_name: str = self.model.__tablename__  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType,reportUnknownVariableType]

            result = await session.execute(
                text("""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins as total_inserts,
                    n_tup_upd as total_updates,
                    n_tup_del as total_deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    seq_scan as sequential_scans,
                    seq_tup_read as sequential_tuples_read,
                    idx_scan as index_scans,
                    idx_tup_fetch as index_tuples_fetched,
                    n_tup_hot_upd as hot_updates,
                    n_tup_newpage_upd as newpage_updates
                FROM pg_stat_user_tables
                WHERE tablename = :table_name
            """),
                {"table_name": table_name},
            )

            stats = result.fetchone()
            return dict(stats._mapping) if stats else {}  # pyright: ignore[reportPrivateUsage]

    async def explain_query_performance(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> dict[str, Any]:
        """
        Analyze query performance using EXPLAIN ANALYZE.

        Development utility based on py-pglite optimization patterns.
        """
        async with self.db.session() as session:
            stmt = select(self.model)
            if filters is not None:
                stmt = stmt.where(filters)
            if order_by is not None:
                stmt = stmt.order_by(order_by)

            # Get the compiled SQL
            compiled = stmt.compile(compile_kwargs={"literal_binds": True})
            sql_query = str(compiled)

            # Analyze with EXPLAIN
            explain_stmt = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql_query}")
            result = await session.execute(explain_stmt)
            plan_data = result.scalar()

            return {
                "query": sql_query,
                "plan": plan_data[0] if plan_data else {},
                "model": self.model.__name__,
            }

    @staticmethod
    def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
        """Return getattr(obj, attr, default) - keeps old helper available."""
        return getattr(obj, attr, default)
