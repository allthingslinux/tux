"""Core CRUD operations for database controllers."""

from typing import Any, TypeVar

from loguru import logger
from sqlmodel import SQLModel, select

from tux.database.service import DatabaseService

from .filters import build_filters_for_model

ModelT = TypeVar("ModelT", bound=SQLModel)


class CrudController[ModelT]:
    """Handles basic Create, Read, Update, Delete operations."""

    def __init__(self, model: type[ModelT], db: DatabaseService) -> None:
        """Initialize the CRUD controller.

        Parameters
        ----------
        model : type[ModelT]
            The SQLModel to perform CRUD operations on.
        db : DatabaseService
            The database service instance.
        """
        self.model = model
        self.db = db

    async def create(self, **kwargs: Any) -> ModelT:
        """
        Create a new record.

        Returns
        -------
        ModelT
            The newly created record.
        """
        async with self.db.session() as session:
            instance = self.model(**kwargs)
            session.add(instance)
            await session.commit()
            # Only refresh if the commit was successful and we need to populate auto-generated fields
            try:
                await session.refresh(instance)
                logger.debug(
                    f"Refresh succeeded for {self.model.__name__} with id {getattr(instance, 'id', 'unknown')}",
                )
            except Exception as e:
                # If refresh fails (e.g., due to database-managed timestamp fields),
                # just continue - the instance is still valid for our purposes
                logger.warning(f"Refresh failed for {self.model.__name__}: {e}")
                logger.debug(f"Refresh error details: {e}", exc_info=True)
            # Expunge the instance so it can be used in other sessions
            session.expunge(instance)
            return instance

    async def get_by_id(self, record_id: Any) -> ModelT | None:
        """
        Get a record by ID.

        Returns
        -------
        ModelT | None
            The record if found, None otherwise.
        """
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance:
                # Expunge the instance so it can be used in other sessions
                session.expunge(instance)
            return instance

    async def update_by_id(self, record_id: Any, **values: Any) -> ModelT | None:
        """
        Update a record by ID.

        Returns
        -------
        ModelT | None
            The updated record, or None if not found.
        """
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance:
                for key, value in values.items():
                    setattr(instance, key, value)
                await session.commit()
                await session.refresh(instance)
                # Expunge the instance so it can be used in other sessions
                session.expunge(instance)
            return instance

    async def delete_by_id(self, record_id: Any) -> bool:
        """
        Delete a record by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        async with self.db.session() as session:
            instance = await session.get(self.model, record_id)
            if instance:
                await session.delete(instance)
                await session.commit()
                return True
            return False

    async def exists(self, filters: Any) -> bool:
        """
        Check if a record exists.

        Returns
        -------
        bool
            True if record exists, False otherwise.
        """
        async with self.db.session() as session:
            stmt = select(self.model)
            filter_expr = build_filters_for_model(filters, self.model)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)
            result = await session.execute(stmt)
            return result.scalars().first() is not None
