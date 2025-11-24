"""Shared filter utilities for database controllers."""

from typing import Any

from sqlalchemy import BinaryExpression, and_


def build_filters_for_model(
    filters: dict[str, Any] | Any,
    model: type[Any],
) -> BinaryExpression[bool] | Any | None:
    """
    Build filter expressions from various input types for a specific model.

    Returns
    -------
    BinaryExpression[bool] | Any | None
        Combined filter expression, or None if no filters.
    """
    if filters is None:
        return None

    if isinstance(filters, dict):
        filter_expressions: list[BinaryExpression[bool]] = [
            getattr(model, key) == value  # type: ignore[arg-type]
            for key, value in filters.items()  # type: ignore[var-annotated]
        ]
        return and_(*filter_expressions) if filter_expressions else None

    # Handle iterable of SQL expressions (but not strings/bytes)
    if hasattr(filters, "__iter__") and not isinstance(filters, str | bytes):
        return and_(*filters)

    # Return single filter expression as-is
    return filters


def build_filters(filters: Any) -> Any:
    """
    Build filter expressions from various input types (legacy function).

    Returns
    -------
    Any
        Combined filter expression, or None if no filters.
    """
    if filters is None:
        return None

    # Handle iterable of SQL expressions (but not strings/bytes)
    if hasattr(filters, "__iter__") and not isinstance(filters, str | bytes):
        return and_(*filters)

    # Return single filter expression as-is
    return filters
