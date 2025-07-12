"""
Sentry instrumentation utilities for tracing and performance monitoring.

This module provides decorators and context managers for instrumenting
code with Sentry transactions and spans, simplifying the addition of
performance monitoring and error tracking.
"""

import asyncio
import functools
import time
import traceback
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any, ParamSpec, TypeVar, cast

import sentry_sdk

# Type variables for better type hints with generic functions
P = ParamSpec("P")
T = TypeVar("T")
R = TypeVar("R")


class DummySpan:
    """A dummy span object for when Sentry is not initialized."""

    def set_tag(self, *args: Any, **kwargs: Any) -> "DummySpan":
        return self

    def set_data(self, *args: Any, **kwargs: Any) -> "DummySpan":
        return self

    def set_status(self, *args: Any, **kwargs: Any) -> "DummySpan":
        return self

    def set_name(self, name: str) -> "DummySpan":
        return self


class DummyTransaction(DummySpan):
    """A dummy transaction object for when Sentry is not initialized."""


def safe_set_name(obj: Any, name: str) -> None:
    """
    Safely set the name on a span or transaction object.

    Parameters
    ----------
    obj : Any
        The span or transaction object
    name : str
        The name to set
    """
    if hasattr(obj, "set_name"):
        # Use getattr to avoid static type checking issues
        set_name_func = obj.set_name
        set_name_func(name)


def transaction(
    op: str,
    name: str | None = None,
    description: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to wrap a function with a Sentry transaction.

    Parameters
    ----------
    op : str
        The operation name for the transaction.
    name : Optional[str]
        The name for the transaction. Defaults to the function name.
    description : Optional[str]
        A description of what the transaction is doing.

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_transaction_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                transaction_name = name or f"{func.__module__}.{func.__qualname__}"
                start_time = time.perf_counter()

                if not sentry_sdk.is_initialized():
                    return await func(*args, **kwargs)

                with sentry_sdk.start_transaction(
                    op=op,
                    name=transaction_name,
                    description=description or f"Executing {func.__qualname__}",
                ) as transaction_obj:
                    try:
                        result = await func(*args, **kwargs)
                    except Exception as e:
                        transaction_obj.set_status("internal_error")
                        transaction_obj.set_data("error", str(e))
                        transaction_obj.set_data("traceback", traceback.format_exc())
                        raise
                    else:
                        transaction_obj.set_status("ok")
                        return result
                    finally:
                        transaction_obj.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)

            return cast(Callable[P, R], async_transaction_wrapper)

        @functools.wraps(func)
        def sync_transaction_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            transaction_name = name or f"{func.__module__}.{func.__qualname__}"
            start_time = time.perf_counter()

            if not sentry_sdk.is_initialized():
                return func(*args, **kwargs)

            with sentry_sdk.start_transaction(
                op=op,
                name=transaction_name,
                description=description or f"Executing {func.__qualname__}",
            ) as transaction_obj:
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    transaction_obj.set_status("internal_error")
                    transaction_obj.set_data("error", str(e))
                    transaction_obj.set_data("traceback", traceback.format_exc())
                    raise
                else:
                    transaction_obj.set_status("ok")
                    return result
                finally:
                    transaction_obj.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)

        return sync_transaction_wrapper

    return decorator


def span(op: str, description: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to wrap a function with a Sentry span.

    Parameters
    ----------
    op : str
        The operation name for the span.
    description : Optional[str]
        A description of what the span is doing.

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_span_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                span_description = description or f"Executing {func.__qualname__}"
                start_time = time.perf_counter()

                if not sentry_sdk.is_initialized():
                    return await func(*args, **kwargs)

                with sentry_sdk.start_span(op=op, description=span_description) as span_obj:
                    try:
                        # Use the helper function to safely set name if available
                        safe_set_name(span_obj, func.__qualname__)

                        result = await func(*args, **kwargs)
                    except Exception as e:
                        span_obj.set_status("internal_error")
                        span_obj.set_data("error", str(e))
                        span_obj.set_data("traceback", traceback.format_exc())
                        raise
                    else:
                        span_obj.set_status("ok")
                        return result
                    finally:
                        span_obj.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)

            return cast(Callable[P, R], async_span_wrapper)

        @functools.wraps(func)
        def sync_span_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            span_description = description or f"Executing {func.__qualname__}"
            start_time = time.perf_counter()

            if not sentry_sdk.is_initialized():
                return func(*args, **kwargs)

            with sentry_sdk.start_span(op=op, description=span_description) as span_obj:
                try:
                    # Use the helper function to safely set name if available
                    safe_set_name(span_obj, func.__qualname__)

                    result = func(*args, **kwargs)
                except Exception as e:
                    span_obj.set_status("internal_error")
                    span_obj.set_data("error", str(e))
                    span_obj.set_data("traceback", traceback.format_exc())
                    raise
                else:
                    span_obj.set_status("ok")
                    return result
                finally:
                    span_obj.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)

        return sync_span_wrapper

    return decorator


@contextmanager
def start_span(op: str, description: str = "") -> Generator[DummySpan | Any]:
    """
    Context manager for creating a Sentry span.

    Parameters
    ----------
    op : str
        The operation name for the span.
    description : str
        A description of what the span is doing.

    Yields
    ------
    Union[DummySpan, Any]
        The Sentry span object or a dummy object if Sentry is not initialized.
    """
    start_time = time.perf_counter()

    if not sentry_sdk.is_initialized():
        # Create a dummy context if Sentry is not available
        dummy = DummySpan()
        try:
            yield dummy
        finally:
            pass
    else:
        with sentry_sdk.start_span(op=op, description=description) as span:
            try:
                yield span
            finally:
                span.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)


@contextmanager
def start_transaction(op: str, name: str, description: str = "") -> Generator[DummyTransaction | Any]:
    """
    Context manager for creating a Sentry transaction.

    Parameters
    ----------
    op : str
        The operation name for the transaction.
    name : str
        The name for the transaction.
    description : str
        A description of what the transaction is doing.

    Yields
    ------
    Union[DummyTransaction, Any]
        The Sentry transaction object or a dummy object if Sentry is not initialized.
    """
    start_time = time.perf_counter()

    if not sentry_sdk.is_initialized():
        # Create a dummy context if Sentry is not available
        dummy = DummyTransaction()
        try:
            yield dummy
        finally:
            pass
    else:
        with sentry_sdk.start_transaction(op=op, name=name, description=description) as transaction:
            try:
                yield transaction
            finally:
                transaction.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)
