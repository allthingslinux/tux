"""Base controller module providing common database functionality."""

from collections.abc import Callable
from typing import Any, TypeVar

import sentry_sdk
from database.client import db
from loguru import logger

from prisma.models import (
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
    operations and utility methods for interacting with a specific Prisma model
    table. It standardizes database interactions and error handling.

    Attributes
    ----------
    table : Any
        The Prisma client's model instance for the specific table.
    table_name : str
        The name of the database table this controller manages.
    """

    def __init__(self, table_name: str) -> None:
        """Initializes the BaseController for a specific table.

        Parameters
        ----------
        table_name : str
            The name of the Prisma model table (e.g., 'case', 'guild').
            This name must match an attribute on the Prisma client instance.
        """
        self.table: Any = getattr(db.client, table_name)
        self.table_name = table_name

    # --- Private Helper Methods ---

    async def _execute_query(
        self,
        operation: Callable[[], Any],
        error_msg: str,
    ) -> Any:
        """Executes a database query with standardized error logging.

        Wraps the Prisma client operation call in a try-except block,
        logging any exceptions with a contextual error message.

        Parameters
        ----------
        operation : Callable[[], Any]
            A zero-argument function (e.g., a lambda) that performs the database call.
        error_msg : str
            The base error message to log if an exception occurs.

        Returns
        -------
        Any
            The result of the database operation.

        Raises
        ------
        Exception
            Re-raises any exception caught during the database operation.
        """
        # Create a Sentry span to track database query performance
        if sentry_sdk.is_initialized():
            with sentry_sdk.start_span(op="db.query", description=f"Database query: {self.table_name}") as span:
                span.set_tag("db.table", self.table_name)
                try:
                    result = await operation()
                    span.set_status("ok")
                    return result  # noqa: TRY300
                except Exception as e:
                    span.set_status("internal_error")
                    span.set_data("error", str(e))
                    logger.error(f"{error_msg}: {e}")
                    raise
        else:
            try:
                return await operation()
            except Exception as e:
                logger.error(f"{error_msg}: {e}")
                raise

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
        """Constructs the keyword arguments dictionary for Prisma find operations."""
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
        """Constructs simple keyword arguments for Prisma (e.g., create, delete)."""
        args = {key_name: key_value}
        self._add_include_arg_if_present(args, include)
        return args

    def _build_create_args(
        self,
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for Prisma create operations."""
        return self._build_simple_args("data", data, include)

    def _build_update_args(
        self,
        where: dict[str, Any],
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for Prisma update operations."""
        args = {"where": where, "data": data}
        self._add_include_arg_if_present(args, include)
        return args

    def _build_delete_args(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for Prisma delete operations."""
        return self._build_simple_args("where", where, include)

    def _build_upsert_args(
        self,
        where: dict[str, Any],
        create: dict[str, Any],
        update: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Constructs keyword arguments for Prisma upsert operations."""
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
        """Finds the first record matching specified criteria.

        Parameters
        ----------
        where : dict[str, Any]
            Query conditions to match.
        include : dict[str, bool], optional
            Specifies relations to include in the result.
        order : dict[str, str], optional
            Specifies the field and direction for ordering.

        Returns
        -------
        ModelType | None
            The found record or None if no match exists.
        """
        find_args = self._build_find_args(where=where, include=include, order=order)
        return await self._execute_query(
            lambda: self.table.find_first(**find_args),
            f"Failed to find record in {self.table_name} with criteria {where}",
        )

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
        find_args = self._build_find_args(where=where, include=include)  # Order not applicable for find_unique
        return await self._execute_query(
            lambda: self.table.find_unique(**find_args),
            f"Failed to find unique record in {self.table_name} with criteria {where}",
        )

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
        find_args = self._build_find_args(
            where=where,
            include=include,
            order=order,
            take=take,
            skip=skip,
            cursor=cursor,
        )
        return await self._execute_query(
            lambda: self.table.find_many(**find_args),
            f"Failed to find records in {self.table_name} with criteria {where}",
        )

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
        return await self._execute_query(
            lambda: self.table.count(where=where),
            f"Failed to count records in {self.table_name} with criteria {where}",
        )

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
        create_args = self._build_create_args(data=data, include=include)
        return await self._execute_query(
            lambda: self.table.create(**create_args),
            f"Failed to create record in {self.table_name} with data {data}",
        )

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
        update_args = self._build_update_args(where=where, data=data, include=include)
        return await self._execute_query(
            lambda: self.table.update(**update_args),
            f"Failed to update record in {self.table_name} with criteria {where} and data {data}",
        )

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
        delete_args = self._build_delete_args(where=where, include=include)
        return await self._execute_query(
            lambda: self.table.delete(**delete_args),
            f"Failed to delete record in {self.table_name} with criteria {where}",
        )

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
        upsert_args = self._build_upsert_args(where=where, create=create, update=update, include=include)
        return await self._execute_query(
            lambda: self.table.upsert(**upsert_args),
            f"Failed to upsert record in {self.table_name} with where={where}, create={create}, update={update}",
        )

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
        result = await self._execute_query(
            lambda: self.table.update_many(where=where, data=data),
            f"Failed to update records in {self.table_name} with criteria {where} and data {data}",
        )
        # Validate and return count
        count_val = getattr(result, "count", None)
        if count_val is None or not isinstance(count_val, int):
            msg = f"Update operation for {self.table_name} did not return a valid count, got: {count_val}"
            raise ValueError(msg)
        return count_val

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
        result = await self._execute_query(
            lambda: self.table.delete_many(where=where),
            f"Failed to delete records in {self.table_name} with criteria {where}",
        )
        # Validate and return count
        count_val = getattr(result, "count", None)
        if count_val is None or not isinstance(count_val, int):
            msg = f"Delete operation for {self.table_name} did not return a valid count, got: {count_val}"
            raise ValueError(msg)
        return count_val

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
            async with db.transaction():
                return await callback()
        except Exception as e:
            logger.error(f"Transaction failed in {self.table_name}: {e}")
            raise

    @staticmethod
    def connect_or_create_relation(
        id_field: str,
        model_id: Any,
        create_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Builds a Prisma 'connect_or_create' relation structure.

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
            A dictionary formatted for Prisma's connect_or_create.
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
