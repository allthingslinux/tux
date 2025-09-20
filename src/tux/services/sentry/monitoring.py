"""Performance monitoring with spans and transactions."""

from __future__ import annotations

from typing import Any

import sentry_sdk
from loguru import logger

from .config import is_initialized
from .handlers import get_span_operation_mapping, get_transaction_operation_mapping


def get_current_span() -> Any | None:
    """Get the current active Sentry span."""
    return sentry_sdk.Hub.current.scope.span if is_initialized() else None


def start_transaction(op: str, name: str, description: str = "") -> Any:
    """Start a new Sentry transaction."""
    if not is_initialized():
        return None

    mapped_op = get_transaction_operation_mapping(name)

    transaction = sentry_sdk.start_transaction(
        op=mapped_op,
        name=name,
        description=description,
    )

    logger.debug(f"Started transaction: {name} (op: {mapped_op})")
    return transaction


def start_span(op: str, description: str = "") -> Any:
    """Start a new Sentry span."""
    if not is_initialized():
        return None

    mapped_op = get_span_operation_mapping(op)
    return sentry_sdk.start_span(op=mapped_op, description=description)


def finish_transaction_on_error() -> None:
    """Finish the current transaction with error status."""
    if not is_initialized():
        return

    if current_span := get_current_span():
        current_span.set_status("internal_error")
        logger.debug("Transaction finished with error status")


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb to the current Sentry scope."""
    if not is_initialized():
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )
