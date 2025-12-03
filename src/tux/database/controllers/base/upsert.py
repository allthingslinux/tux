"""Upsert operations for database controllers."""

from typing import Any, TypeVar

from sqlmodel import SQLModel

from tux.database.service import DatabaseService

from .crud import CrudController
from .query import QueryController

ModelT = TypeVar("ModelT", bound=SQLModel)


class UpsertController[ModelT]:
    """Handles upsert and get-or-create operations."""

    def __init__(self, model: type[ModelT], db: DatabaseService) -> None:
        """Initialize the upsert controller.

        Parameters
        ----------
        model : type[ModelT]
            The SQLModel to perform upsert operations on.
        db : DatabaseService
            The database service instance.
        """
        self.model = model
        self.db = db

    async def upsert_by_field(
        self,
        field_name: str,
        field_value: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """
        Upsert a record by a specific field.

        Returns
        -------
        tuple[ModelT, bool]
            Tuple of (record, created) where created is True if new record was created.
        """
        query_controller = QueryController(self.model, self.db)

        # Try to find existing record
        filters = {field_name: field_value}
        existing = await query_controller.find_one(filters)

        if existing:
            # Update existing record
            update_data = {**kwargs}
            if defaults:
                update_data |= defaults

            async with self.db.session() as session:
                for key, value in update_data.items():
                    setattr(existing, key, value)
                await session.commit()
                await session.refresh(existing)
                return existing, False

        # Create new record
        create_data = {field_name: field_value, **kwargs}
        if defaults:
            create_data |= defaults

        crud_controller = CrudController(self.model, self.db)
        new_instance = await crud_controller.create(**create_data)
        return new_instance, True

    async def upsert_by_id(
        self,
        record_id: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """
        Upsert a record by ID.

        Returns
        -------
        tuple[ModelT, bool]
            Tuple of (record, created) where created is True if new record was created.

        Raises
        ------
        RuntimeError
            If updating an existing record fails.
        """
        crud_controller = CrudController(self.model, self.db)

        # Try to get existing record
        existing = await crud_controller.get_by_id(record_id)

        if existing:
            # Update existing record
            update_data = {**kwargs}
            if defaults:
                update_data |= defaults

            updated = await crud_controller.update_by_id(record_id, **update_data)
            if updated is None:
                msg = f"Failed to update record with ID {record_id}"
                raise RuntimeError(msg)
            return updated, False

        # Create new record
        create_data = {"id": record_id, **kwargs}
        if defaults:
            create_data |= defaults

        new_instance = await crud_controller.create(**create_data)
        return new_instance, True

    async def get_or_create_by_field(
        self,
        field_name: str,
        field_value: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """
        Get existing record or create new one by field.

        Returns
        -------
        tuple[ModelT, bool]
            Tuple of (record, created) where created is True if new record was created.
        """
        query_controller = QueryController(self.model, self.db)

        # Try to find existing record
        filters = {field_name: field_value}
        existing = await query_controller.find_one(filters)

        if existing:
            return existing, False

        # Create new record
        create_data = {field_name: field_value, **kwargs}
        if defaults:
            create_data |= defaults

        crud_controller = CrudController(self.model, self.db)
        new_instance = await crud_controller.create(**create_data)
        return new_instance, True

    async def get_or_create(
        self,
        defaults: dict[str, Any] | None = None,
        **filters: Any,
    ) -> tuple[ModelT, bool]:
        """
        Get existing record or create new one.

        Returns
        -------
        tuple[ModelT, bool]
            Tuple of (record, created) where created is True if new record was created.
        """
        query_controller = QueryController(self.model, self.db)

        # Try to find existing record
        existing = await query_controller.find_one(filters)

        if existing:
            return existing, False

        # Create new record
        create_data = {**filters}
        if defaults:
            create_data |= defaults

        crud_controller = CrudController(self.model, self.db)
        new_instance = await crud_controller.create(**create_data)
        return new_instance, True

    async def upsert(
        self,
        filters: dict[str, Any],
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """
        Upsert a record.

        Returns
        -------
        tuple[ModelT, bool]
            Tuple of (record, created) where created is True if new record was created.
        """
        query_controller = QueryController(self.model, self.db)

        # Try to find existing record
        existing = await query_controller.find_one(filters)

        if existing:
            # Update existing record
            update_data = {**kwargs}
            if defaults:
                update_data |= defaults

            async with self.db.session() as session:
                # Merge the detached instance into this session
                existing = await session.merge(existing)
                for key, value in update_data.items():
                    setattr(existing, key, value)
                await session.commit()
                await session.refresh(existing)
                # Expunge the instance so it can be used in other sessions
                session.expunge(existing)
                return existing, False

        # Create new record
        create_data = filters | kwargs
        if defaults:
            create_data |= defaults

        crud_controller = CrudController(self.model, self.db)
        new_instance = await crud_controller.create(**create_data)
        return new_instance, True
