"""Main BaseController that composes all specialized controllers with lazy initialization."""

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from sqlmodel import SQLModel

from tux.database.service import DatabaseService

from .bulk import BulkOperationsController
from .crud import CrudController
from .pagination import PaginationController, PaginationResult
from .performance import PerformanceController
from .query import QueryController
from .transaction import TransactionController
from .upsert import UpsertController

ModelT = TypeVar("ModelT", bound=SQLModel)
R = TypeVar("R")


class BaseController[ModelT]:
    """
    Composed database controller with lazy-loaded specialized operations.

    This controller delegates operations to specialized controllers while
    maintaining backward compatibility with the original BaseController API.
    Core CRUD and Query controllers are eagerly initialized, while specialized
    controllers (pagination, bulk, transaction, performance, upsert) use lazy
    initialization to reduce overhead for simple use cases.
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
            error_msg = "DatabaseService must be provided. Use DI container to get the service."
            raise RuntimeError(error_msg)

        self.model = model
        self.db = db

        # Core controllers - eagerly initialized (most commonly used)
        self._crud = CrudController(model, db)
        self._query = QueryController(model, db)

        # Specialized controllers - lazy initialization (reduces overhead)
        self._pagination: PaginationController[ModelT] | None = None
        self._bulk: BulkOperationsController[ModelT] | None = None
        self._transaction: TransactionController[ModelT] | None = None
        self._performance: PerformanceController[ModelT] | None = None
        self._upsert: UpsertController[ModelT] | None = None

    # Properties for test compatibility
    @property
    def db_service(self) -> DatabaseService:
        """Database service property for test compatibility."""
        return self.db

    @property
    def model_class(self) -> type[ModelT]:
        """Model class property for test compatibility."""
        return self.model

    # Lazy initialization helpers
    def _get_pagination(self) -> PaginationController[ModelT]:
        """Get or create pagination controller."""
        if self._pagination is None:
            self._pagination = PaginationController(self.model, self.db)
        return self._pagination

    def _get_bulk(self) -> BulkOperationsController[ModelT]:
        """Get or create bulk operations controller."""
        if self._bulk is None:
            self._bulk = BulkOperationsController(self.model, self.db)
        return self._bulk

    def _get_transaction(self) -> TransactionController[ModelT]:
        """Get or create transaction controller."""
        if self._transaction is None:
            self._transaction = TransactionController(self.model, self.db)
        return self._transaction

    def _get_performance(self) -> PerformanceController[ModelT]:
        """Get or create performance controller."""
        if self._performance is None:
            self._performance = PerformanceController(self.model, self.db)
        return self._performance

    def _get_upsert(self) -> UpsertController[ModelT]:
        """Get or create upsert controller."""
        if self._upsert is None:
            self._upsert = UpsertController(self.model, self.db)
        return self._upsert

    # ------------------------------------------------------------------
    # Core CRUD Methods - Delegated to CrudController
    # ------------------------------------------------------------------

    async def create(self, **kwargs: Any) -> ModelT:
        """Create a new record."""
        return await self._crud.create(**kwargs)

    async def get_by_id(self, record_id: Any) -> ModelT | None:
        """Get a record by ID."""
        return await self._crud.get_by_id(record_id)

    async def update_by_id(self, record_id: Any, **values: Any) -> ModelT | None:
        """Update a record by ID."""
        return await self._crud.update_by_id(record_id, **values)

    async def delete_by_id(self, record_id: Any) -> bool:
        """Delete a record by ID."""
        return await self._crud.delete_by_id(record_id)

    async def exists(self, filters: Any) -> bool:
        """Check if a record exists."""
        return await self._crud.exists(filters)

    # ------------------------------------------------------------------
    # Query Methods - Delegated to QueryController
    # ------------------------------------------------------------------

    async def find_one(self, filters: Any | None = None, order_by: Any | None = None) -> ModelT | None:
        """Find one record."""
        return await self._query.find_one(filters, order_by)

    async def find_all(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelT]:
        """Find all records with performance optimizations."""
        return await self._query.find_all(filters, order_by, limit, offset)

    async def find_all_with_options(
        self,
        filters: Any | None = None,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
        load_relationships: list[str] | None = None,
    ) -> list[ModelT]:
        """Find all records with relationship loading options."""
        return await self._query.find_all_with_options(filters, order_by, limit, offset, load_relationships)

    async def count(self, filters: Any | None = None) -> int:
        """Count records."""
        return await self._query.count(filters)

    async def get_all(self, filters: Any | None = None, order_by: Any | None = None) -> list[ModelT]:
        """Get all records (alias for find_all without pagination)."""
        return await self._query.get_all(filters, order_by)

    async def execute_query(self, query: Any) -> Any:
        """Execute a custom query."""
        return await self._query.execute_query(query)

    async def find_with_json_query(
        self,
        json_column: str,
        json_path: str,
        value: Any,
        filters: Any | None = None,
    ) -> list[ModelT]:
        """Find records using JSON column queries."""
        return await self._query.find_with_json_query(json_column, json_path, value, filters)

    async def find_with_array_contains(
        self,
        array_column: str,
        value: Any,
        filters: Any | None = None,
    ) -> list[ModelT]:
        """Find records where array column contains value."""
        return await self._query.find_with_array_contains(array_column, value, filters)

    async def find_with_full_text_search(
        self,
        search_columns: list[str],
        search_term: str,
        filters: Any | None = None,
    ) -> list[ModelT]:
        """Find records using full-text search."""
        return await self._query.find_with_full_text_search(search_columns, search_term, filters)

    # ------------------------------------------------------------------
    # Pagination Methods - Lazy-loaded
    # ------------------------------------------------------------------

    async def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> PaginationResult[ModelT]:
        """Paginate records with metadata."""
        return await self._get_pagination().paginate(page, per_page, filters, order_by)

    async def find_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Any | None = None,
        order_by: Any | None = None,
        load_relationships: list[str] | None = None,
    ) -> PaginationResult[ModelT]:
        """Find paginated records with relationship loading."""
        return await self._get_pagination().find_paginated(page, per_page, filters, order_by, load_relationships)

    # ------------------------------------------------------------------
    # Bulk Operations - Lazy-loaded
    # ------------------------------------------------------------------

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        """Create multiple records in bulk."""
        return await self._get_bulk().bulk_create(items)

    async def bulk_update(self, updates: list[tuple[Any, dict[str, Any]]]) -> int:
        """Update multiple records in bulk."""
        return await self._get_bulk().bulk_update(updates)

    async def bulk_delete(self, record_ids: list[Any]) -> int:
        """Delete multiple records in bulk."""
        return await self._get_bulk().bulk_delete(record_ids)

    async def update_where(self, filters: Any, values: dict[str, Any]) -> int:
        """Update records matching filters."""
        return await self._get_bulk().update_where(filters, values)

    async def delete_where(self, filters: Any) -> int:
        """Delete records matching filters."""
        return await self._get_bulk().delete_where(filters)

    async def bulk_upsert_with_conflict_resolution(
        self,
        items: list[dict[str, Any]],
        conflict_columns: list[str],
        update_columns: list[str] | None = None,
    ) -> list[ModelT]:
        """Bulk upsert with conflict resolution."""
        return await self._get_bulk().bulk_upsert_with_conflict_resolution(items, conflict_columns, update_columns)

    # ------------------------------------------------------------------
    # Transaction Methods - Lazy-loaded
    # ------------------------------------------------------------------

    async def with_session[R](self, operation: Callable[[Any], Awaitable[R]]) -> R:
        """Execute operation within a session context."""
        return await self._get_transaction().with_session(operation)

    async def with_transaction[R](self, operation: Callable[[Any], Awaitable[R]]) -> R:
        """Execute operation within a transaction context."""
        return await self._get_transaction().with_transaction(operation)

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Execute a callback within a transaction."""
        return await self._get_transaction().execute_transaction(callback)

    # ------------------------------------------------------------------
    # Performance Methods - Lazy-loaded
    # ------------------------------------------------------------------

    async def get_table_statistics(self) -> dict[str, Any]:
        """Get comprehensive table statistics."""
        return await self._get_performance().get_table_statistics()

    async def explain_query_performance(
        self,
        query: Any,
        analyze: bool = False,
        buffers: bool = False,
    ) -> dict[str, Any]:
        """Explain query performance with optional analysis."""
        return await self._get_performance().explain_query_performance(query, analyze, buffers)

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
        """Upsert a record by a specific field."""
        return await self._get_upsert().upsert_by_field(field_name, field_value, defaults, **kwargs)

    async def upsert_by_id(
        self,
        record_id: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """Upsert a record by ID."""
        return await self._get_upsert().upsert_by_id(record_id, defaults, **kwargs)

    async def get_or_create_by_field(
        self,
        field_name: str,
        field_value: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """Get existing record or create new one by field."""
        return await self._get_upsert().get_or_create_by_field(field_name, field_value, defaults, **kwargs)

    async def get_or_create(self, defaults: dict[str, Any] | None = None, **filters: Any) -> tuple[ModelT, bool]:
        """Get existing record or create new one."""
        return await self._get_upsert().get_or_create(defaults, **filters)

    async def upsert(
        self,
        filters: dict[str, Any],
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """Upsert a record."""
        return await self._get_upsert().upsert(filters, defaults, **kwargs)
