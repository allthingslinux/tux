"""Pagination operations for database controllers."""

from math import ceil
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlmodel import SQLModel

from tux.database.service import DatabaseService

from .query import QueryController

ModelT = TypeVar("ModelT", bound=SQLModel)


class PaginationResult[ModelT](BaseModel):
    """Result of a paginated query."""

    items: list[ModelT]
    total: int
    page: int
    per_page: int
    pages: int
    has_prev: bool
    has_next: bool

    class Config:
        """Pydantic configuration for PaginationResult."""

        arbitrary_types_allowed = True


class PaginationController[ModelT]:
    """Handles pagination logic and utilities."""

    def __init__(self, model: type[ModelT], db: DatabaseService) -> None:
        """Initialize the pagination controller.

        Parameters
        ----------
        model : type[ModelT]
            The SQLModel to paginate.
        db : DatabaseService
            The database service instance.
        """
        self.model = model
        self.db = db

    async def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Any | None = None,
        order_by: Any | None = None,
    ) -> PaginationResult[ModelT]:
        """Paginate records with metadata."""
        query_controller = QueryController(self.model, self.db)

        # Get total count
        total = await query_controller.count(filters)

        # Calculate pagination metadata
        pages = ceil(total / per_page) if per_page > 0 else 1
        has_prev = page > 1
        has_next = page < pages

        # Get items for current page
        offset = (page - 1) * per_page
        items = await query_controller.find_all(
            filters=filters,
            order_by=order_by,
            limit=per_page,
            offset=offset,
        )

        return PaginationResult(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_prev=has_prev,
            has_next=has_next,
        )

    async def find_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Any | None = None,
        order_by: Any | None = None,
        load_relationships: list[str] | None = None,
    ) -> PaginationResult[ModelT]:
        """Find paginated records with relationship loading."""
        query_controller = QueryController(self.model, self.db)

        # Get total count
        total = await query_controller.count(filters)

        # Calculate pagination metadata
        pages = ceil(total / per_page) if per_page > 0 else 1
        has_prev = page > 1
        has_next = page < pages

        # Get items for current page
        offset = (page - 1) * per_page
        items = await query_controller.find_all_with_options(
            filters=filters,
            order_by=order_by,
            limit=per_page,
            offset=offset,
            load_relationships=load_relationships,
        )

        return PaginationResult(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_prev=has_prev,
            has_next=has_next,
        )
