"""Main BaseController that composes all specialized controllers."""

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
    Composed database controller that provides all database operations.

    This controller delegates operations to specialized controllers while
    maintaining backward compatibility with the original BaseController API.
    """

    def __init__(self, model: type[ModelT], db: DatabaseService | None = None) -> None:
        """Initialize the base controller with all specialized controllers.

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

        # Initialize specialized controllers
        self._crud = CrudController(model, db)
        self._query = QueryController(model, db)
        self._pagination = PaginationController(model, db)
        self._bulk = BulkOperationsController(model, db)
        self._transaction = TransactionController(model, db)
        self._performance = PerformanceController(model, db)
        self._upsert = UpsertController(model, db)

    # Properties for test compatibility
    @property
    def db_service(self) -> DatabaseService:
        """Database service property for test compatibility."""
        return self.db

    @property
    def model_class(self) -> type[ModelT]:
        """Model class property for test compatibility."""
        return self.model

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

    # ------------------------------------------------------------------
    # Advanced Query Methods - Delegated to QueryController
    # ------------------------------------------------------------------

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
    # Pagination Methods - Delegated to PaginationController
    # ------------------------------------------------------------------

    async def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> PaginationResult[ModelT]:
        """Paginate records with metadata."""
        return await self._pagination.paginate(page, per_page, filters, order_by)

    async def find_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Any | None = None,
        order_by: Any | None = None,
        load_relationships: list[str] | None = None,
    ) -> PaginationResult[ModelT]:
        """Find paginated records with relationship loading."""
        return await self._pagination.find_paginated(page, per_page, filters, order_by, load_relationships)

    # ------------------------------------------------------------------
    # Bulk Operations - Delegated to BulkOperationsController
    # ------------------------------------------------------------------

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        """Create multiple records in bulk."""
        return await self._bulk.bulk_create(items)

    async def bulk_update(self, updates: list[tuple[Any, dict[str, Any]]]) -> int:
        """Update multiple records in bulk."""
        return await self._bulk.bulk_update(updates)

    async def bulk_delete(self, record_ids: list[Any]) -> int:
        """Delete multiple records in bulk."""
        return await self._bulk.bulk_delete(record_ids)

    async def update_where(self, filters: Any, values: dict[str, Any]) -> int:
        """Update records matching filters."""
        return await self._bulk.update_where(filters, values)

    async def delete_where(self, filters: Any) -> int:
        """Delete records matching filters."""
        return await self._bulk.delete_where(filters)

    async def bulk_upsert_with_conflict_resolution(
        self,
        items: list[dict[str, Any]],
        conflict_columns: list[str],
        update_columns: list[str] | None = None,
    ) -> list[ModelT]:
        """Bulk upsert with conflict resolution."""
        return await self._bulk.bulk_upsert_with_conflict_resolution(items, conflict_columns, update_columns)

    # ------------------------------------------------------------------
    # Transaction Methods - Delegated to TransactionController
    # ------------------------------------------------------------------

    async def with_session[R](self, operation: Callable[[Any], Awaitable[R]]) -> R:
        """Execute operation within a session context."""
        return await self._transaction.with_session(operation)

    async def with_transaction[R](self, operation: Callable[[Any], Awaitable[R]]) -> R:
        """Execute operation within a transaction context."""
        return await self._transaction.with_transaction(operation)

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Execute a callback within a transaction."""
        return await self._transaction.execute_transaction(callback)

    # ------------------------------------------------------------------
    # Performance Methods - Delegated to PerformanceController
    # ------------------------------------------------------------------

    async def get_table_statistics(self) -> dict[str, Any]:
        """Get comprehensive table statistics."""
        return await self._performance.get_table_statistics()

    async def explain_query_performance(
        self,
        query: Any,
        analyze: bool = False,
        buffers: bool = False,
    ) -> dict[str, Any]:
        """Explain query performance with optional analysis."""
        return await self._performance.explain_query_performance(query, analyze, buffers)

    # ------------------------------------------------------------------
    # Upsert Methods - Delegated to UpsertController
    # ------------------------------------------------------------------

    async def upsert_by_field(
        self,
        field_name: str,
        field_value: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """Upsert a record by a specific field."""
        return await self._upsert.upsert_by_field(field_name, field_value, defaults, **kwargs)

    async def upsert_by_id(
        self,
        record_id: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """Upsert a record by ID."""
        return await self._upsert.upsert_by_id(record_id, defaults, **kwargs)

    async def get_or_create_by_field(
        self,
        field_name: str,
        field_value: Any,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """Get existing record or create new one by field."""
        return await self._upsert.get_or_create_by_field(field_name, field_value, defaults, **kwargs)

    async def get_or_create(self, defaults: dict[str, Any] | None = None, **filters: Any) -> tuple[ModelT, bool]:
        """Get existing record or create new one."""
        return await self._upsert.get_or_create(defaults, **filters)

    async def upsert(
        self,
        filters: dict[str, Any],
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ModelT, bool]:
        """Upsert a record."""
        return await self._upsert.upsert(filters, defaults, **kwargs)
