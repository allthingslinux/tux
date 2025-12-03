"""
Sentry Instrumentation Utilities for Tracing and Performance Monitoring.

This module provides a set of decorators and context managers to simplify the
instrumentation of code with Sentry transactions and spans. It standardizes the
creation of performance monitoring traces and ensures that they gracefully handle
cases where the Sentry SDK is not initialized by providing dummy objects.

The main components are:
- Decorators (`@transaction`, `@span`): For easily wrapping entire functions or
  methods in a Sentry transaction or span.
- Context Managers (`start_transaction`, `start_span`): For instrumenting
  specific blocks of code within a function.
- Helper Functions: For adding contextual data to the currently active span.
"""

import asyncio
import functools
import time
import traceback
from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
from typing import Any, ParamSpec, TypeVar, cast

import sentry_sdk
from discord.ext import commands
from loguru import logger

from tux.shared.config import CONFIG

# Type variables for better type hints with generic functions
P = ParamSpec("P")
T = TypeVar("T")
R = TypeVar("R")


# --- Dummy Objects for Graceful Failure ---


class DummySpan:
    """
    A no-op (dummy) span object for when the Sentry SDK is not initialized.

    This class mimics the interface of a Sentry span but performs no actions,
    allowing instrumentation code (`with start_span(...)`) to run without errors
    even if Sentry is disabled.
    """

    def __init__(self) -> None:
        """Initialize the dummy span."""
        self.start_time = time.perf_counter()

    def set_tag(self, *args: Any, **kwargs: Any) -> "DummySpan":
        """
        No-op tag setter.

        Returns
        -------
        DummySpan
            Returns self for method chaining.
        """
        return self

    def set_data(self, *args: Any, **kwargs: Any) -> "DummySpan":
        """
        No-op data setter.

        Returns
        -------
        DummySpan
            Returns self for method chaining.
        """
        return self

    def set_status(self, *args: Any, **kwargs: Any) -> "DummySpan":
        """
        No-op status setter.

        Returns
        -------
        DummySpan
            Returns self for method chaining.
        """
        return self

    def set_name(self, name: str) -> "DummySpan":
        """
        No-op name setter.

        Returns
        -------
        DummySpan
            Returns self for method chaining.
        """
        return self


class DummyTransaction(DummySpan):
    """
    A no-op (dummy) transaction object for when Sentry is not initialized.

    This inherits from `DummySpan` and provides a safe fallback for the
    `start_transaction` context manager.
    """


# --- Common Helpers ---


def safe_set_name(obj: Any, name: str) -> None:
    """
    Safely set the name on a span or transaction object.

    This helper is used because the `set_name` method may not always be
    present on all span-like objects from Sentry, so this avoids
    potential `AttributeError` exceptions.

    Parameters
    ----------
    obj : Any
        The span or transaction object.
    name : str
        The name to set.
    """
    set_name_func = getattr(obj, "set_name", None)
    if callable(set_name_func):
        set_name_func(name)


def _handle_exception_in_sentry_context(context_obj: Any, exception: Exception) -> None:
    """
    Handle exceptions in a Sentry context (span or transaction) with consistent patterns.

    Parameters
    ----------
    context_obj : Any
        The Sentry span or transaction object.
    exception : Exception
        The exception that occurred.
    """
    context_obj.set_status("internal_error")
    context_obj.set_data("error", str(exception))
    context_obj.set_data("traceback", traceback.format_exc())


def _finalize_sentry_context(context_obj: Any, start_time: float) -> None:
    """
    Finalize a Sentry context with timing information.

    Parameters
    ----------
    context_obj : Any
        The Sentry span or transaction object.
    start_time : float
        The start time for duration calculation.
    """
    context_obj.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)


def create_instrumentation_wrapper[**P, R](
    func: Callable[P, R],
    context_factory: Callable[[], Any],
    is_transaction: bool = False,
) -> Callable[P, R]:
    """
    Create an instrumentation wrapper for both sync and async functions.

    This is the core helper that eliminates duplication between transaction
    and span decorators by providing a unified wrapper creation mechanism.

    Parameters
    ----------
    func : Callable[P, R]
        The function to wrap.
    context_factory : Callable[[], Any]
        A factory function that creates the Sentry context (span or transaction).
    is_transaction : bool, optional
        Whether this is a transaction (affects status setting behavior).

    Returns
    -------
    Callable[P, R]
        The wrapped function.
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            Async wrapper for instrumented functions.

            This wrapper handles execution of async functions within a Sentry
            context (span or transaction), capturing timing and error information.

            Parameters
            ----------
            *args : P.args
                Positional arguments passed to the wrapped function.
            **kwargs : P.kwargs
                Keyword arguments passed to the wrapped function.

            Returns
            -------
            R
                The return value from the wrapped function.
            """
            start_time = time.perf_counter()

            if not sentry_sdk.is_initialized():
                return await func(*args, **kwargs)

            with context_factory() as context_obj:
                try:
                    # Set name for spans (transactions handle this themselves)
                    if not is_transaction:
                        safe_set_name(context_obj, func.__qualname__)

                    result = await func(*args, **kwargs)
                except Exception as e:
                    _handle_exception_in_sentry_context(context_obj, e)
                    raise
                else:
                    context_obj.set_status("ok")
                    return result
                finally:
                    _finalize_sentry_context(context_obj, start_time)

        return cast(Callable[P, R], async_wrapper)

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """
        Sync wrapper for instrumented functions.

        This wrapper handles execution of sync functions within a Sentry
        context (span or transaction), capturing timing and error information.

        Parameters
        ----------
        *args : P.args
            Positional arguments passed to the wrapped function.
        **kwargs : P.kwargs
            Keyword arguments passed to the wrapped function.

        Returns
        -------
        R
            The return value from the wrapped function.
        """
        start_time = time.perf_counter()

        if not sentry_sdk.is_initialized():
            return func(*args, **kwargs)

        with context_factory() as context_obj:
            try:
                # Set name for spans (transactions handle this themselves)
                if not is_transaction:
                    safe_set_name(context_obj, func.__qualname__)

                result = func(*args, **kwargs)
            except Exception as e:
                _handle_exception_in_sentry_context(context_obj, e)
                raise
            else:
                context_obj.set_status("ok")
                return result
            finally:
                _finalize_sentry_context(context_obj, start_time)

    return sync_wrapper


# --- Decorators ---


def transaction(
    op: str,
    name: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Wrap a function with a Sentry transaction.

    This handles both synchronous and asynchronous functions automatically.
    It captures the function's execution time, sets the status to 'ok' on
    success or 'internal_error' on failure, and records exceptions.

    Parameters
    ----------
    op : str
        The operation name for the transaction (e.g., 'db.query').
    name : Optional[str]
        The name for the transaction. Defaults to the function's qualified name.

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        Wrap a function with Sentry transaction instrumentation.

        Parameters
        ----------
        func : Callable[P, R]
            The function to wrap.

        Returns
        -------
        Callable[P, R]
            The wrapped function.
        """
        # Early return if Sentry is not initialized to avoid wrapper overhead
        if not sentry_sdk.is_initialized():
            return func

        transaction_name = name or f"{func.__module__}.{func.__qualname__}"

        def context_factory() -> Any:
            """
            Create Sentry transaction context.

            Returns
            -------
            Any
                Sentry transaction context manager.
            """
            return sentry_sdk.start_transaction(
                op=op,
                name=transaction_name,
            )

        return create_instrumentation_wrapper(
            func,
            context_factory,
            is_transaction=True,
        )

    return decorator


def span(
    op: str,
    description: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Wrap a function with a Sentry span.

    This should be used on functions called within an existing transaction.
    It automatically handles both sync and async functions, captures execution
    time, and records success or failure status.

    Parameters
    ----------
    op : str
        The operation name for the span (e.g., 'db.query.fetch').
    description : Optional[str]
        A description of what the span is doing. Defaults to the function's name.

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        Wrap a function with Sentry span instrumentation.

        Parameters
        ----------
        func : Callable[P, R]
            The function to wrap.

        Returns
        -------
        Callable[P, R]
            The wrapped function.
        """
        # Early return if Sentry is not initialized to avoid wrapper overhead
        if not sentry_sdk.is_initialized():
            return func

        span_name = description or f"Executing {func.__qualname__}"

        def context_factory() -> Any:
            """
            Create Sentry span context.

            Returns
            -------
            Any
                Sentry span context manager.
            """
            # Note: description parameter is deprecated, use name instead
            return sentry_sdk.start_span(op=op, name=span_name)

        return create_instrumentation_wrapper(
            func,
            context_factory,
            is_transaction=False,
        )

    return decorator


# --- Context Managers ---


@contextmanager
def start_span(op: str, name: str = "") -> Generator[DummySpan | Any]:
    """
    Context manager for creating a Sentry span for a block of code.

    Example:
        with start_span("db.query", "Fetching user data"):
            ...

    Parameters
    ----------
    op : str
        The operation name for the span.
    name : str
        The name of the span.

    Yields
    ------
    Union[DummySpan, sentry_sdk.Span]
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
        with sentry_sdk.start_span(op=op, name=name) as span:
            try:
                yield span
            finally:
                span.set_data("duration_ms", (time.perf_counter() - start_time) * 1000)


@contextmanager
def start_transaction(
    op: str,
    name: str,
) -> Generator[DummyTransaction | Any]:
    """
    Context manager for creating a Sentry transaction for a block of code.

    Example:
        with start_transaction("task", "process_daily_report"):
            ...

    Parameters
    ----------
    op : str
        The operation name for the transaction.
    name : str
        The name for the transaction.

    Yields
    ------
    Union[DummyTransaction, sentry_sdk.Transaction]
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
        with sentry_sdk.start_transaction(
            op=op,
            name=name,
        ) as transaction:
            try:
                yield transaction
            finally:
                transaction.set_data(
                    "duration_ms",
                    (time.perf_counter() - start_time) * 1000,
                )


# --- Enhanced Helper Functions ---


def get_current_span() -> Any | None:
    """
    Get the current active Sentry span.

    Returns
    -------
    Any | None
        The current span if Sentry is initialized, None otherwise.
    """
    if not sentry_sdk.is_initialized():
        return None
    return sentry_sdk.Hub.current.scope.span


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb to the current Sentry scope."""
    if not sentry_sdk.is_initialized():
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )


def finish_transaction_on_error() -> None:
    """Finish the current transaction with error status."""
    if not sentry_sdk.is_initialized():
        return

    if current_span := get_current_span():
        current_span.set_status("internal_error")
        logger.debug("Transaction finished with error status")


def set_span_attributes(attributes: dict[str, Any]) -> None:
    """
    Set multiple data attributes on the current active Sentry span.

    This helper function simplifies attaching context to a span by accepting a
    dictionary of attributes. Uses `set_data()` for span attributes (visible in
    trace explorer), not `set_tag()` (which is for filtering).

    Parameters
    ----------
    attributes : dict[str, Any]
        A dictionary where keys are the attribute names and values are the
        attribute values to set on the span. Values can be string, number,
        boolean, or arrays of these types.
    """
    if sentry_sdk.is_initialized() and (span := sentry_sdk.get_current_span()):
        for key, value in attributes.items():
            span.set_data(key, value)


def set_setup_phase_tag(span: Any, phase: str, status: str = "starting") -> None:
    """
    Set a setup phase tag on the span.

    Parameters
    ----------
    span : Any
        The Sentry span to tag
    phase : str
        The phase name (e.g., "database", "cogs")
    status : str
        The status ("starting" or "finished")
    """
    span.set_tag("setup_phase", f"{phase}_{status}")


def capture_span_exception(exception: Exception, **extra_data: Any) -> None:
    """
    Capture an exception in the current span with consistent error handling.

    This consolidates the common pattern of setting span status and data
    when an exception occurs.

    Parameters
    ----------
    exception : Exception
        The exception to capture.
    **extra_data : Any
        Additional data to attach to the span.
    """
    if sentry_sdk.is_initialized() and (span := sentry_sdk.get_current_span()):
        _handle_exception_in_sentry_context(span, exception)

        # Add any additional data
        for key, value in extra_data.items():
            span.set_data(f"extra.{key}", value)


@contextmanager
def enhanced_span(
    op: str,
    name: str = "",
    **initial_data: Any,
) -> Generator[DummySpan | Any]:
    """
    Enhanced context manager for creating a Sentry span with initial data.

    This extends the basic start_span with the ability to set initial
    tags and data, reducing boilerplate in calling code.

    Parameters
    ----------
    op : str
        The operation name for the span.
    name : str
        The name for the span.
    **initial_data : Any
        Initial data to set on the span.

    Yields
    ------
    Union[DummySpan, sentry_sdk.Span]
        The Sentry span object or a dummy object if Sentry is not initialized.
    """
    # Skip spans for very short utility operations in production
    if not sentry_sdk.is_initialized():
        yield DummySpan()
        return

    # In production, skip tracing for certain frequent operations
    if not CONFIG.DEBUG and any(
        skip_term in name.lower()
        for skip_term in ["safe_get_attr", "connect_or_create"]
    ):
        yield DummySpan()
        return

    with start_span(op, name) as span:
        # Set initial data if provided (use set_data for span attributes)
        if initial_data:
            for key, value in initial_data.items():
                span.set_data(key, value)

        try:
            yield span
        except Exception as e:
            capture_span_exception(e)
            raise


def instrument_bot_commands(bot: commands.Bot) -> None:
    """
    Automatically instruments all bot commands with Sentry transactions.

    This function iterates through all registered commands on the bot and
    wraps their callbacks with the `@transaction` decorator. This ensures
    that every command invocation is captured as a Sentry transaction.

    Parameters
    ----------
    bot : commands.Bot
        The instance of the bot whose commands should be instrumented.
    """
    # The operation for commands is standardized as `command.run`
    op = "command.run"

    for cmd in bot.walk_commands():
        # Preserve existing decorators and metadata
        original_callback = cast(Callable[..., Coroutine[Any, Any, None]], cmd.callback)
        txn_name = f"command.{cmd.qualified_name}"

        @functools.wraps(original_callback)
        async def wrapped(
            *args: Any,
            __orig_cb: Callable[..., Coroutine[Any, Any, None]] = original_callback,
            __txn_name: str = txn_name,
            **kwargs: Any,
        ) -> None:
            """
            Execute command callback with Sentry transaction instrumentation.

            Parameters
            ----------
            *args : Any
                Positional arguments passed to the command.
            __orig_cb : Callable[..., Coroutine[Any, Any, None]]
                Original command callback.
            __txn_name : str
                Transaction name for Sentry.
            **kwargs : Any
                Keyword arguments passed to the command.
            """
            if not sentry_sdk.is_initialized():
                return await __orig_cb(*args, **kwargs)
            with sentry_sdk.start_transaction(op=op, name=__txn_name):
                return await __orig_cb(*args, **kwargs)

        cmd.callback = cast(Callable[..., Coroutine[Any, Any, None]], wrapped)

    logger.info(f"Instrumented {len(list(bot.walk_commands()))} commands with Sentry.")
