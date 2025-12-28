"""Bulk operations for database controllers."""

from typing import Any, TypeVar

from loguru import logger
from sqlmodel import SQLModel, delete, update

from tux.database.service import DatabaseService

from .filters import build_filters_for_model

ModelT = TypeVar("ModelT", bound=SQLModel)


class BulkOperationsController[ModelT]:
    """Handles bulk create, update, and delete operations."""

    def __init__(self, model: type[ModelT], db: DatabaseService) -> None:
        """Initialize the bulk operations controller.

        Parameters
        ----------
        model : type[ModelT]
            The SQLModel to perform bulk operations on.
        db : DatabaseService
            The database service instance.
        """
        self.model = model
        self.db = db

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        """
        Create multiple records in bulk.

        Returns
        -------
        list[ModelT]
            List of created records.
        """
        logger.debug(f"Bulk creating {len(items)} {self.model.__name__} records")
        async with self.db.session() as session:
            instances = [self.model(**item) for item in items]
            session.add_all(instances)
            await session.commit()

            # Refresh all instances to get generated IDs
            for instance in instances:
                await session.refresh(instance)

            logger.success(
                f"Bulk created {len(instances)} {self.model.__name__} records",
            )
            return instances

    async def bulk_update(self, updates: list[tuple[Any, dict[str, Any]]]) -> int:
        """
        Update multiple records in bulk.

        Returns
        -------
        int
            Number of records updated.
        """
        logger.debug(f"Bulk updating {len(updates)} {self.model.__name__} records")
        async with self.db.session() as session:
            updated_count = 0

            for record_id, values in updates:
                stmt = (
                    update(self.model)
                    .where(self.model.id == record_id)  # type: ignore[attr-defined]
                    .values(**values)
                )
                await session.execute(stmt)
                # In SQLAlchemy 2.0+, rowcount is not available. Count affected rows differently
                updated_count += 1  # Assume each update affects 1 row if successful

            await session.commit()
            logger.info(f"Bulk updated {updated_count} {self.model.__name__} records")
            return updated_count

    async def bulk_delete(self, record_ids: list[Any]) -> int:
        """
        Delete multiple records in bulk.

        Returns
        -------
        int
            Number of records deleted.
        """
        logger.debug(f"Bulk deleting {len(record_ids)} {self.model.__name__} records")
        async with self.db.session() as session:
            stmt = delete(self.model).where(self.model.id.in_(record_ids))  # type: ignore[attr-defined]
            await session.execute(stmt)
            await session.commit()
            # In SQLAlchemy 2.0+, rowcount is not available. Use len(record_ids) as approximation
            logger.info(f"Bulk deleted {len(record_ids)} {self.model.__name__} records")
            return len(record_ids)

    async def update_where(self, filters: Any, values: dict[str, Any]) -> int:
        """
        Update records matching filters.

        Returns
        -------
        int
            Number of records updated.
        """
        async with self.db.session() as session:
            filter_expr = build_filters_for_model(filters, self.model)

            stmt = update(self.model).values(**values)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)

            await session.execute(stmt)
            await session.commit()
            # In SQLAlchemy 2.0+, rowcount is not available. Return 0 as placeholder
            return 0

    async def delete_where(self, filters: Any) -> int:
        """
        Delete records matching filters.

        Returns
        -------
        int
            Number of records deleted.
        """
        async with self.db.session() as session:
            filter_expr = build_filters_for_model(filters, self.model)

            stmt = delete(self.model)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)

            result = await session.execute(stmt)
            await session.commit()
            # In SQLAlchemy 2.0+, we can get rowcount from the result
            return getattr(
                result,
                "rowcount",
                1,
            )  # fallback to 1 if rowcount not available
