"""Base controller module providing common database functionality."""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from loguru import logger

from tux.database.client import db

ModelType = TypeVar("ModelType")
RelationType = TypeVar("RelationType")


class BaseController(Generic[ModelType]):
    """Base controller class providing common database functionality.

    This class serves as a foundation for all database controllers,
    providing shared functionality and standardized error handling.

    Attributes
    ----------
    table : Any
        The Prisma model table this controller operates on
    """

    def __init__(self, table_name: str) -> None:
        """Initialize the controller with a specific table.

        Parameters
        ----------
        table_name : str
            The name of the Prisma model table to use
        """
        self.table: Any = getattr(db.client, table_name)
        self.table_name = table_name

    async def find_one(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
        order: dict[str, str] | None = None,
    ) -> ModelType | None:
        """Find a single record matching the given criteria.

        Parameters
        ----------
        where : dict[str, Any]
            The search criteria
        include : dict[str, bool] | None
            Optional relations to include
        order : dict[str, str] | None
            Optional ordering criteria

        Returns
        -------
        ModelType | None
            The found record or None if not found
        """
        try:
            find_args: dict[str, Any] = {"where": where}
            if include:
                find_args["include"] = include
            if order:
                find_args["order"] = order
            return await self.table.find_first(**find_args)
        except Exception as e:
            logger.error(f"Failed to find record in {self.table_name} with criteria {where}: {e}")
            raise

    async def find_unique(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType | None:
        """Find a single record by unique constraint.

        This method is optimized for looking up records by unique fields
        like primary keys or unique indexes.

        Parameters
        ----------
        where : dict[str, Any]
            The unique search criteria
        include : dict[str, bool] | None
            Optional relations to include

        Returns
        -------
        ModelType | None
            The found record or None if not found
        """
        try:
            find_args: dict[str, Any] = {"where": where}
            if include:
                find_args["include"] = include
            return await self.table.find_unique(**find_args)
        except Exception as e:
            logger.error(f"Failed to find unique record in {self.table_name} with criteria {where}: {e}")
            raise

    async def find_many(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
        order: dict[str, str] | None = None,
        take: int | None = None,
        skip: int | None = None,
        cursor: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """Find multiple records matching the given criteria.

        Parameters
        ----------
        where : dict[str, Any]
            The search criteria
        include : dict[str, bool] | None
            Optional relations to include
        order : dict[str, str] | None
            Optional ordering criteria
        take : int | None
            Optional limit on number of records to return
        skip : int | None
            Optional number of records to skip
        cursor : dict[str, Any] | None
            Optional cursor for pagination

        Returns
        -------
        list[ModelType]
            List of found records
        """
        try:
            find_args: dict[str, Any] = {"where": where}
            if include:
                find_args["include"] = include
            if order:
                find_args["order"] = order
            if take is not None:
                find_args["take"] = take
            if skip is not None:
                find_args["skip"] = skip
            if cursor is not None:
                find_args["cursor"] = cursor
            return await self.table.find_many(**find_args)
        except Exception as e:
            logger.error(f"Failed to find records in {self.table_name} with criteria {where}: {e}")
            raise

    async def count(
        self,
        where: dict[str, Any],
    ) -> int:
        """Count records matching the given criteria.

        Parameters
        ----------
        where : dict[str, Any]
            The search criteria

        Returns
        -------
        int
            The number of matching records
        """
        try:
            return await self.table.count(where=where)
        except Exception as e:
            logger.error(f"Failed to count records in {self.table_name} with criteria {where}: {e}")
            raise

    async def create(
        self,
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType:
        """Create a new record.

        Parameters
        ----------
        data : dict[str, Any]
            The data to create the record with
        include : dict[str, bool] | None
            Optional relations to include in the response

        Returns
        -------
        ModelType
            The created record
        """
        try:
            create_args: dict[str, Any] = {"data": data}
            if include:
                create_args["include"] = include
            return await self.table.create(**create_args)
        except Exception as e:
            logger.error(f"Failed to create record in {self.table_name} with data {data}: {e}")
            raise

    async def update(
        self,
        where: dict[str, Any],
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType | None:
        """Update an existing record.

        Parameters
        ----------
        where : dict[str, Any]
            The criteria to find the record to update
        data : dict[str, Any]
            The data to update the record with
        include : dict[str, bool] | None
            Optional relations to include in the response

        Returns
        -------
        ModelType | None
            The updated record or None if not found
        """
        try:
            update_args: dict[str, Any] = {"where": where, "data": data}
            if include:
                update_args["include"] = include
            return await self.table.update(**update_args)
        except Exception as e:
            logger.error(f"Failed to update record in {self.table_name} with criteria {where} and data {data}: {e}")
            raise

    async def delete(
        self,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType | None:
        """Delete a record matching the given criteria.

        Parameters
        ----------
        where : dict[str, Any]
            The criteria to find the record to delete
        include : dict[str, bool] | None
            Optional relations to include in the response

        Returns
        -------
        ModelType | None
            The deleted record or None if not found
        """
        try:
            delete_args: dict[str, Any] = {"where": where}
            if include:
                delete_args["include"] = include
            return await self.table.delete(**delete_args)
        except Exception as e:
            logger.error(f"Failed to delete record in {self.table_name} with criteria {where}: {e}")
            raise

    async def upsert(
        self,
        where: dict[str, Any],
        create: dict[str, Any],
        update: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelType:
        """Create or update a record.

        Parameters
        ----------
        where : dict[str, Any]
            The criteria to find an existing record
        create : dict[str, Any]
            The data to create a new record with if none exists
        update : dict[str, Any]
            The data to update an existing record with
        include : dict[str, bool] | None
            Optional relations to include in the response

        Returns
        -------
        ModelType
            The created or updated record
        """
        try:
            upsert_args: dict[str, Any] = {
                "where": where,
                "data": {
                    "create": create,
                    "update": update,
                },
            }
            if include:
                upsert_args["include"] = include
            return await self.table.upsert(**upsert_args)
        except Exception as e:
            logger.error(
                f"Failed to upsert record in {self.table_name} with where={where}, create={create}, update={update}: {e}",
            )
            raise

    async def update_many(
        self,
        where: dict[str, Any],
        data: dict[str, Any],
    ) -> int:
        """Update multiple records.

        Parameters
        ----------
        where : dict[str, Any]
            The criteria to find records to update
        data : dict[str, Any]
            The data to update the records with

        Returns
        -------
        int
            The number of records updated
        """
        try:
            result = await self.table.update_many(where=where, data=data)
            return result.count if hasattr(result, "count") else 0
        except Exception as e:
            logger.error(f"Failed to update records in {self.table_name} with criteria {where} and data {data}: {e}")
            raise

    async def delete_many(
        self,
        where: dict[str, Any],
    ) -> int:
        """Delete multiple records.

        Parameters
        ----------
        where : dict[str, Any]
            The criteria to find records to delete

        Returns
        -------
        int
            The number of records deleted
        """
        try:
            result = await self.table.delete_many(where=where)
            return result.count if hasattr(result, "count") else 0
        except Exception as e:
            logger.error(f"Failed to delete records in {self.table_name} with criteria {where}: {e}")
            raise

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Execute operations in a transaction.

        This ensures all database operations in the callback are atomic.
        If any operation fails, all changes are rolled back.

        Parameters
        ----------
        callback : Callable[[], Any]
            The function containing database operations to execute

        Returns
        -------
        Any
            The result of the callback function
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
        """Create a connect_or_create relation object.

        This is a utility method to simplify creating connect_or_create relations.

        Parameters
        ----------
        id_field : str
            The name of the ID field to use in the where clause
        model_id : Any
            The ID value to connect to
        create_data : dict[str, Any] | None
            Additional data to include when creating a new record

        Returns
        -------
        dict[str, Any]
            A connect_or_create relation object
        """
        where = {id_field: model_id}
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
        """Safely get an attribute from an object.

        Parameters
        ----------
        obj : Any
            The object to get the attribute from
        attr : str
            The name of the attribute to get
        default : Any
            The default value to return if the attribute doesn't exist

        Returns
        -------
        Any
            The attribute value or default
        """
        return getattr(obj, attr, default)
