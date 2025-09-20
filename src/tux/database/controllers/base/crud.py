"""Core CRUD operations for database controllers."""

from typing import Any, TypeVar

from sqlmodel import SQLModel, select

from tux.database.service import DatabaseService

from .filters import build_filters_for_model

ModelT = TypeVar("ModelT", bound=SQLModel)


class CrudController[ModelT]:
    """Handles basic Create, Read, Update, Delete operations."""

    def __init__(self, model: type[ModelT], db: DatabaseService):
        self.model = model
        self.db = db

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

    async def update_by_id(self, record_id: Any, **values: Any) -> ModelT | None:
        """Update a record by ID."""
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance:
                for key, value in values.items():
                    setattr(instance, key, value)
                await session.commit()
                await session.refresh(instance)
            return instance

    async def delete_by_id(self, record_id: Any) -> bool:
        """Delete a record by ID."""
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance:
                await session.delete(instance)
                await session.commit()
                return True
            return False

    async def exists(self, filters: Any) -> bool:
        """Check if a record exists."""
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = build_filters_for_model(filters, self.model)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            result = await session.execute(stmt)
            return result.scalars().first() is not None
