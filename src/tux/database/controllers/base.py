from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from loguru import logger
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from tux.database.service import DatabaseService

ModelT = TypeVar("ModelT", bound=SQLModel)
R = TypeVar("R")


class BaseController[ModelT]:
    """Clean, type-safe base controller with direct CRUD operations.

    This controller provides:
    - Full type safety with generics
    - Direct SQLAlchemy operations (no mixin dependencies)
    - Session management
    - Clean, simple architecture

    For Sentry integration, use the @span decorator from tux.services.tracing
    on your business logic methods.
    """

    def __init__(self, model: type[ModelT], db: DatabaseService | None = None):
        self.model = model
        if db is None:
            error_msg = "DatabaseService must be provided. Use DI container to get the service."
            raise RuntimeError(error_msg)
        self.db = db

    # ------------------------------------------------------------------
    # Core CRUD Methods - Direct SQLAlchemy Implementation
    # ------------------------------------------------------------------

    async def create(self, **kwargs: Any) -> ModelT:
        """Create a new record."""
        async with self.db.session() as session:
            instance = self.model(**kwargs)
            session.add(instance)
            await session.flush()
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
            if filters is not None:
                stmt = stmt.where(filters)
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
        """Find all records."""
        async with self.db.session() as session:
            stmt = select(self.model)
            if filters is not None:
                stmt = stmt.where(filters)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
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

    async def update_by_id(self, record_id: Any, **values: Any) -> ModelT | None:
        """Update record by ID."""
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance is None:
                return None
            for key, value in values.items():
                setattr(instance, key, value)
            await session.flush()
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
            await session.flush()
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
            await session.flush()
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
            create_data.update(defaults)

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

    @staticmethod
    def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
        """Return getattr(obj, attr, default) - keeps old helper available."""
        return getattr(obj, attr, default)


# Example usage:
"""
# Clean, simple controller usage:
from tux.database.controllers.base import BaseController
from tux.database.models.moderation import Case
from tux.services.tracing import span

class CaseController(BaseController[Case]):
    def __init__(self):
        super().__init__(Case)

    # All CRUD methods are available with full type safety:
    # - create(**kwargs) -> Case
# - get_by_id(id) -> Case | None
# - get_or_create(defaults=None, **filters) -> tuple[Case, bool]
# - find_one(filters=None, order_by=None) -> Case | None
# - find_all(filters=None, order_by=None, limit=None, offset=None) -> list[Case]
# - count(filters=None) -> int
# - update_by_id(id, **values) -> Case | None
# - update_where(filters, values) -> int
# - delete_by_id(id) -> bool
# - delete_where(filters) -> int
# - upsert(match_filter, create_values, update_values) -> Case

    # Custom business logic methods with Sentry integration:
    @span(op="db.query", description="get_active_cases_for_user")
    async def get_active_cases_for_user(self, user_id: int) -> list[Case]:
        return await self.find_all(
            filters=(Case.case_target_id == user_id) & (Case.case_status == True)
        )

    @span(op="db.query", description="close_case")
    async def close_case(self, case_id: int) -> Case | None:
        return await self.update_by_id(case_id, case_status=False)

    # For complex operations, use with_session:
    async def bulk_update_cases(self, case_ids: list[int], **updates: Any) -> None:
        async def _bulk_op(session: AsyncSession) -> None:
            for case_id in case_ids:
                instance = await session.get(Case, case_id)
                if instance:
                    for key, value in updates.items():
                        setattr(instance, key, value)
            await session.flush()

        await self.with_session(_bulk_op)

# Usage:
# controller = CaseController()
# case = await controller.create(case_type="BAN", case_target_id=12345)
# cases = await controller.get_active_cases_for_user(12345)
"""
