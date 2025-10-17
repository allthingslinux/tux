"""Bulk operations for database controllers."""

from typing import Any, TypeVar

from sqlmodel import SQLModel, delete, select, update

from tux.database.service import DatabaseService

from .filters import build_filters_for_model

ModelT = TypeVar("ModelT", bound=SQLModel)


class BulkOperationsController[ModelT]:
    """Handles bulk create, update, and delete operations."""

    def __init__(self, model: type[ModelT], db: DatabaseService):
        self.model = model
        self.db = db

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        """Create multiple records in bulk."""
        async with self.db.session() as session:
            instances = [self.model(**item) for item in items]
            session.add_all(instances)
            await session.commit()

            # Refresh all instances to get generated IDs
            for instance in instances:
                await session.refresh(instance)

            return instances

    async def bulk_update(self, updates: list[tuple[Any, dict[str, Any]]]) -> int:
        """Update multiple records in bulk."""
        async with self.db.session() as session:
            updated_count = 0

            for record_id, values in updates:
                stmt = update(self.model).where(self.model.id == record_id).values(**values)  # type: ignore[attr-defined]
                await session.execute(stmt)
                # In SQLAlchemy 2.0+, rowcount is not available. Count affected rows differently
                updated_count += 1  # Assume each update affects 1 row if successful

            await session.commit()
            return updated_count

    async def bulk_delete(self, record_ids: list[Any]) -> int:
        """Delete multiple records in bulk."""
        async with self.db.session() as session:
            stmt = delete(self.model).where(self.model.id.in_(record_ids))  # type: ignore[attr-defined]
            await session.execute(stmt)
            await session.commit()
            # In SQLAlchemy 2.0+, rowcount is not available. Use len(record_ids) as approximation
            return len(record_ids)

    async def update_where(self, filters: Any, values: dict[str, Any]) -> int:
        """Update records matching filters."""
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
        """Delete records matching filters."""
        async with self.db.session() as session:
            filter_expr = build_filters_for_model(filters, self.model)

            stmt = delete(self.model)
            if filter_expr is not None:
                stmt = stmt.where(filter_expr)

            result = await session.execute(stmt)
            await session.commit()
            # In SQLAlchemy 2.0+, we can get rowcount from the result
            return getattr(result, "rowcount", 1)  # fallback to 1 if rowcount not available

    async def bulk_upsert_with_conflict_resolution(
        self,
        items: list[dict[str, Any]],
        conflict_columns: list[str],
        update_columns: list[str] | None = None,
    ) -> list[ModelT]:
        """Bulk upsert with conflict resolution."""
        async with self.db.session() as session:
            instances: list[ModelT] = []

            for item in items:
                # Try to find existing record using direct query
                filters = {col: item[col] for col in conflict_columns if col in item}
                filter_expr = build_filters_for_model(filters, self.model)

                stmt = select(self.model)
                if filter_expr is not None:
                    stmt = stmt.where(filter_expr)

                result = await session.execute(stmt)
                existing = result.scalars().first()

                if existing:
                    # Update existing record
                    if update_columns:
                        for col in update_columns:
                            if col in item:
                                setattr(existing, col, item[col])
                    else:
                        for key, value in item.items():
                            if key not in conflict_columns:
                                setattr(existing, key, value)
                    instances.append(existing)
                else:
                    # Create new record
                    instance = self.model(**item)
                    session.add(instance)
                    instances.append(instance)

            await session.commit()

            # Refresh all instances
            for instance in instances:
                await session.refresh(instance)

            return instances
