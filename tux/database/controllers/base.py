"""Base controller module providing common database functionality."""

from collections.abc import Callable
from typing import Any, TypeVar

from loguru import logger
from sqlalchemy import delete as sa_delete
from sqlalchemy import func
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from tux.database.client import db
from tux.database.schemas import (
    AFKModel,
    Case,
    Guild,
    GuildConfig,
    Levels,
    Note,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
)

# Explicitly define ModelType to cover all potential models used by controllers
ModelType = TypeVar(
    "ModelType",
    AFKModel,
    Case,
    Guild,
    Note,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
    GuildConfig,
    Levels,
)

RelationType = TypeVar("RelationType")


class BaseController[
    ModelType: (
        Case,
        Guild,
        Note,
        Reminder,
        Snippet,
        Starboard,
        StarboardMessage,
        GuildConfig,
        AFKModel,
        Levels,
    ),
]:
    """Provides a base interface for database table controllers.

    This generic class offers common CRUD (Create, Read, Update, Delete)
    operations and utility methods for interacting with a specific SQLModel model
    table. It standardizes database interactions and error handling.

    Attributes
    ----------
    table : Any
        The SQLModel client's model instance for the specific table.
    table_name : str
        The name of the database table this controller manages.
    """

    def __init__(self, table: type[ModelType], session: AsyncSession | None = None) -> None:
        """Initializes the BaseController for a specific table.

        Parameters
        ----------
        session : AsyncSession, optional
            An optional SQLAlchemy AsyncSession instance. If not provided,
            the default session from the database client will be used.
        table_name : str
            The name of the table this controller will manage, used for logging and error messages.
        """
        self.session = session or db.get_session()
        self.table = table

    # --- Private Helper Methods ---

    def _add_include_arg_if_present(self, args: dict[str, Any], include: dict[str, bool] | None) -> None:
        """Adds the 'include' argument to a dictionary if it is not None."""
        if include:
            args["include"] = include

    def _build_find_args(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
        order: dict[str, str] | None = None,
        take: int | None = None,
        skip: int | None = None,
        cursor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Constructs the keyword arguments dictionary for SQLModel find operations."""
        args: dict[str, Any] = {"where": where}
        self._add_include_arg_if_present(args, include)
        if order:
            args["order"] = order
        if take is not None:
            args["take"] = take
        if skip is not None:
            args["skip"] = skip
        if cursor is not None:
            args["cursor"] = cursor
        return args

    def _build_simple_args(
        self,
        key_name: str,
        key_value: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs simple keyword arguments for SQLModel (e.g., create, delete)."""
        args = {key_name: key_value}
        self._add_include_arg_if_present(args, include)
        return args

    def _build_create_args(
        self,
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for SQLModel create operations."""
        return self._build_simple_args("data", data, include)

    def _build_update_args(
        self,
        where: dict[str, Any],
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for SQLModel update operations."""
        args = {"where": where, "data": data}
        self._add_include_arg_if_present(args, include)
        return args

    def _build_delete_args(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for SQLModel delete operations."""
        return self._build_simple_args("where", where, include)

    def _build_upsert_args(
        self,
        where: dict[str, Any],
        create: dict[str, Any],
        update: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for SQLModel upsert operations."""
        args = {
            "where": where,
            "data": {
                "create": create,
                "update": update,
            },
        }
        self._add_include_arg_if_present(args, include)
        return args

    # --- Public CRUD Methods ---

    async def find_one(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
        order: dict[str, str] | None = None,
    ) -> ModelType | None:
        """Find the first matching record using SQLModel select()."""
        stmt = select(self.table).filter_by(**where)
        if order:
            for field, direction in order.items():
                col = getattr(self.table, field)
                stmt = stmt.order_by(col.asc() if direction == "asc" else col.desc())
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_unique(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType | None:
        """Finds a single record by a unique constraint (e.g., ID).

        Parameters
        ----------
        where : dict[str, Any]
            Unique query conditions (e.g., {'id': 1}).
        include : dict[str, bool], optional
            Specifies relations to include in the result.

        Returns
        -------
        ModelType | None
            The found record or None if no match exists.
        """
        stmt = select(self.table).filter_by(**where)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_many(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
        order: dict[str, str] | None = None,
        take: int | None = None,
        skip: int | None = None,
        cursor: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """Finds multiple records matching specified criteria.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to match.
        include : dict[str, bool], optional
            Specifies relations to include in the results.
        order : dict[str, str], optional
            Specifies the field and direction for ordering.
        take : int, optional
            Maximum number of records to return.
        skip : int, optional
            Number of records to skip (for pagination).
        cursor : dict[str, Any], optional
            Cursor for pagination based on a unique field.

        Returns
        -------
        list[ModelType]
            A list of found records, potentially empty.
        """
        stmt = select(self.table).filter_by(**where)
        if order:
            for field, direction in order.items():
                col = getattr(self.table, field)
                stmt = stmt.order_by(col.asc() if direction == "asc" else col.desc())
        if skip:
            stmt = stmt.offset(skip)
        if take:
            stmt = stmt.limit(take)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        where: dict[str, Any],
    ) -> int:
        """Counts records matching the specified criteria.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to match.

        Returns
        -------
        int
            The total number of matching records.
        """
        stmt = select(func.count()).select_from(self.table).filter_by(**where)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(
        self,
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType:
        """Creates a new record in the table.

        Parameters
        ----------
        data : dict[str, Any]
            The data for the new record.
        include : dict[str, bool], optional
            Specifies relations to include in the returned record.

        Returns
        -------
        ModelType
            The newly created record.
        """
        instance = self.table(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(
        self,
        where: dict[str, Any],
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType | None:
        """Updates a single existing record matching the criteria.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to find the record to update.
        data : dict[str, Any]
            The data to update the record with.
        include : dict[str, bool], optional
            Specifies relations to include in the returned record.

        Returns
        -------
        ModelType | None
            The updated record, or None if no matching record was found.
        """
        instance = await self.find_unique(where)
        if not instance:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType | None:
        """Deletes a single record matching the criteria.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to find the record to delete.
        include : dict[str, bool], optional
            Specifies relations to include in the returned deleted record.

        Returns
        -------
        ModelType | None
            The deleted record, or None if no matching record was found.
        """
        instance = await self.find_unique(where)
        if not instance:
            return None
        await self.session.delete(instance)
        await self.session.commit()
        return instance

    async def upsert(
        self,
        where: dict[str, Any],
        create: dict[str, Any],
        update: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType:
        """Updates a record if it exists, otherwise creates it.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to find the existing record.
        create : dict[str, Any]
            Data to use if creating a new record.
        update : dict[str, Any]
            Data to use if updating an existing record.
        include : dict[str, bool], optional
            Specifies relations to include in the returned record.

        Returns
        -------
        ModelType
            The created or updated record.
        """
        instance = await self.find_unique(where)
        if instance:
            for key, value in update.items():
                setattr(instance, key, value)
        else:
            instance = self.table(**create)
            self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update_many(
        self,
        where: dict[str, Any],
        data: dict[str, Any],
    ) -> int:
        """Updates multiple records matching the criteria.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to find the records to update.
        data : dict[str, Any]
            The data to update the records with.

        Returns
        -------
        int
            The number of records updated.

        Raises
        ------
        ValueError
            If the database operation does not return a valid count.
        """
        stmt = sa_update(self.table).filter_by(**where).values(**data)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def delete_many(
        self,
        where: dict[str, Any],
    ) -> int:
        """Deletes multiple records matching the criteria.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to find the records to delete.

        Returns
        -------
        int
            The number of records deleted.

        Raises
        ------
        ValueError
            If the database operation does not return a valid count.
        """
        stmt = sa_delete(self.table).filter_by(**where)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    # --- Other Utility Methods ---

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Executes a series of database operations within a transaction.

        Ensures atomicity: all operations succeed or all fail and roll back.
        Note: Does not use _execute_query internally to preserve specific
              transaction context in error messages.

        Parameters
        ----------
        callback : Callable[[], Any]
            An async function containing the database operations to execute.

        Returns
        -------
        Any
            The result returned by the callback function.

        Raises
        ------
        Exception
            Re-raises any exception that occurs during the transaction.
        """
        try:
            async with self.session.begin():
                return await callback()
        except Exception as e:
            logger.exception(f"Transaction failed in {self.table}: {e}")
            raise

    @staticmethod
    def connect_or_create_relation(
        id_field: str,
        model_id: Any,
        create_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Builds a SQLModel 'connect_or_create' relation structure.

        Simplifies linking or creating related records during create/update operations.

        Parameters
        ----------
        id_field : str
            The name of the ID field used for connection (e.g., 'guild_id').
        model_id : Any
            The ID value of the record to connect to.
        create_data : dict[str, Any], optional
            Additional data required if creating the related record.
            Must include at least the `id_field` and `model_id`.

        Returns
        -------
        dict[str, Any]
            A dictionary formatted for SQLModel's connect_or_create.
        """
        where = {id_field: model_id}
        # Create data must contain the ID field for the new record
        create = {id_field: model_id}
        if create_data:
            create |= create_data

        return {
            "connect_or_create": {
                "where": where,
                "create": create,
            },
        }

    @staticmethod
    def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
        """Safely retrieves an attribute from an object, returning a default if absent.

        Parameters
        ----------
        obj : Any
            The object to retrieve the attribute from.
        attr : str
            The name of the attribute.
        default : Any, optional
            The value to return if the attribute is not found. Defaults to None.

        Returns
        -------
        Any
            The attribute's value or the default value.
        """
        return getattr(obj, attr, default)
