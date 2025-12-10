"""Main BaseController that composes all specialized controllers with lazy initialization."""

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from sqlmodel import SQLModel

from tux.database.service import DatabaseService

from .bulk import BulkOperationsController
from .crud import CrudController
from .query import QueryController
from .transaction import TransactionController
from .upsert import UpsertController

ModelT = TypeVar("ModelT", bound=SQLModel)
R = TypeVar("R")


class BaseController[ModelT]:
    """
    Composed database controller with lazy-loaded specialized operations.

    This controller delegates operations to specialized controllers for clean
    separation of concerns. Core CRUD and Query controllers are eagerly
    initialized, while specialized controllers (bulk, transaction, upsert) use
    lazy initialization to reduce overhead for simple use cases.
    """

    def __init__(self, model: type[ModelT], db: DatabaseService | None = None) -> None:
        """Initialize the base controller with lazy-loaded specialized controllers.

        Parameters
        ----------
        model : type[ModelT]
            The SQLModel class to perform operations on.
        db : DatabaseService | None
            The database service instance. Must be provided.

        Raises
        ------
        RuntimeError
            If db is None, as database service is required.
        """
        if db is None:
            error_msg = (
                "DatabaseService must be provided. Use DI container to get the service."
            )
            raise RuntimeError(error_msg)

        self.model = model
        self.db = db

        # Core controllers - eagerly initialized (most commonly used)
        self._crud = CrudController(model, db)
        self._query = QueryController(model, db)

        # Specialized controllers - lazy initialization (reduces overhead)
        self._bulk: BulkOperationsController[ModelT] | None = None
        self._transaction: TransactionController[ModelT] | None = None
        self._upsert: UpsertController[ModelT] | None = None

    # Properties for test compatibility
    @property
    def db_service(self) -> DatabaseService:
        """
        Database service property for test compatibility.

        Returns
        -------
        DatabaseService
            The database service instance.
        """
        return self.db

    @property
    def model_class(self) -> type[ModelT]:
        """
        Model class property for test compatibility.

        Returns
        -------
        type[ModelT]
            The SQLModel class.
        """
        return self.model

    # Lazy initialization helpers
    def _get_bulk(self) -> BulkOperationsController[ModelT]:
        """
        Get or create bulk operations controller.

        Returns
        -------
        BulkOperationsController[ModelT]
            The bulk operations controller instance.
        """
        if self._bulk is None:
            self._bulk = BulkOperationsController(self.model, self.db)
        return self._bulk

    def _get_transaction(self) -> TransactionController[ModelT]:
        """
        Get or create transaction controller.

        Returns
        -------
        TransactionController[ModelT]
            The transaction controller instance.
        """
        if self._transaction is None:
            self._transaction = TransactionController(self.model, self.db)
        return self._transaction

    def _get_upsert(self) -> UpsertController[ModelT]:
        """
        Get or create upsert controller.

        Returns
        -------
        UpsertController[ModelT]
            The upsert controller instance.
        """
        if self._upsert is None:
            self._upsert = UpsertController(self.model, self.db)
        return self._upsert

    # ------------------------------------------------------------------
    # Core CRUD Methods - Delegated to CrudController
    # ------------------------------------------------------------------

    async def create(self, **kwargs: Any) -> ModelT:
        """
        Create a new record.

        Returns
        -------
        ModelT
            The newly created record.
        """
        return await self._crud.create(**kwargs)

    async def get_by_id(self, record_id: Any) -> ModelT | None:
        """
        Get a record by ID.

        Returns
        -------
        ModelT | None
            The record if found, None otherwise.
        """
        return await self._crud.get_by_id(record_id)

    async def update_by_id(self, record_id: Any, **values: Any) -> ModelT | None:
        """
        Update a record by ID.

        Returns
        -------
        ModelT | None
            The updated record, or None if not found.
        """
        return await self._crud.update_by_id(record_id, **values)

    async def delete_by_id(self, record_id: Any) -> bool:
        """
        Delete a record by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self._crud.delete_by_id(record_id)

    async def exists(self, filters: Any) -> bool:
        """
        Check if a record exists.

        Returns
        -------
        bool
            True if record exists, False otherwise.
        """
        return await self._crud.exists(filters)

    # ------------------------------------------------------------------
    # Query Methods - Delegated to QueryController
    # ------------------------------------------------------------------

    async def find_one(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> ModelT | None:
        """
        Find one record.

        Returns
        -------
        ModelT | None
            The found record, or None if not found.
        """
        return await self._query.find_one(filters, order_by)

    async def find_all(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelT]:
        """
        Find all records with performance optimizations.

        Returns
        -------
        list[ModelT]
            List of found records.
        """
        return await self._query.find_all(filters, order_by, limit, offset)

    async def find_all_with_options(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
        load_relationships: list[str] | None = None,
    ) -> list[ModelT]:
        """
        Find all records with relationship loading options.

        Returns
        -------
        list[ModelT]
            List of found records with loaded relationships.
        """
        return await self._query.find_all_with_options(
            filters,
            order_by,
            limit,
            offset,
            load_relationships,
        )

    async def count(self, filters: Any | None = None) -> int:
        """
        Count records.

        Returns
        -------
        int
            The count of matching records.
        """
        return await self._query.count(filters)

    async def get_all(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        """
        Get all records (alias for find_all without pagination).

        Returns
        -------
        list[ModelT]
            List of all matching records.
        """
        return await self._query.get_all(filters, order_by)

    async def execute_query(self, query: Any) -> Any:
        """
        Execute a custom query.

        Returns
        -------
        Any
            The query result.
        """
        return await self._query.execute_query(query)

    # ------------------------------------------------------------------
    # Bulk Operations - Lazy-loaded
    # ------------------------------------------------------------------

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        """
        Create multiple records in bulk.

        Returns
        -------
        list[ModelT]
            List of created records.
        """
        return await self._get_bulk().bulk_create(items)

    async def bulk_update(self, updates: list[tuple[Any, dict[str, Any]]]) -> int:
        """
        Update multiple records in bulk.

        Returns
        -------
        int
            Number of records updated.
        """
        return await self._get_bulk().bulk_update(updates)

    async def bulk_delete(self, record_ids: list[Any]) -> int:
        """
        Delete multiple records in bulk.

        Returns
        -------
        int
            Number of records deleted.
        """
        return await self._get_bulk().bulk_delete(record_ids)

    async def update_where(self, filters: Any, values: dict[str, Any]) -> int:
        """
        Update records matching filters.

        Returns
        -------
        int
            Number of records updated.
        """
        return await self._get_bulk().update_where(filters, values)

    async def delete_where(self, filters: Any) -> int:
        """
        Delete records matching filters.

        Returns
        -------
        int
            Number of records deleted.
        """
        return await self._get_bulk().delete_where(filters)

    # ------------------------------------------------------------------
    # Transaction Methods - Lazy-loaded
    # ------------------------------------------------------------------

    async def with_session[R](self, operation: Callable[[Any], Awaitable[R]]) -> R:
        """
        Execute operation within a session context.

        Returns
        -------
        R
            The result of the operation.
        """
        return await self._get_transaction().with_session(operation)

    async def with_transaction[R](self, operation: Callable[[Any], Awaitable[R]]) -> R:
        """
        Execute operation within a transaction context.

        Returns
        -------
        R
            The result of the operation.
        """
        return await self._get_transaction().with_transaction(operation)

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """
        Execute a callback within a transaction.

        Returns
        -------
        Any
            The result of the callback.
        """
        return await self._get_transaction().execute_transaction(callback)

    # ------------------------------------------------------------------
    # Upsert Methods - Lazy-loaded
    # ------------------------------------------------------------------

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
        return await self._get_upsert().upsert_by_field(
            field_name,
            field_value,
            defaults,
            **kwargs,
        )

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
        """
        return await self._get_upsert().upsert_by_id(record_id, defaults, **kwargs)

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
        return await self._get_upsert().get_or_create_by_field(
            field_name,
            field_value,
            defaults,
            **kwargs,
        )

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
        return await self._get_upsert().get_or_create(defaults, **filters)

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
        return await self._get_upsert().upsert(filters, defaults, **kwargs)
