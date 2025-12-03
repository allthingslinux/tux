"""Sentry metrics utilities for tracking performance and usage metrics.

This module provides helper functions for emitting Sentry metrics (counters,
distributions, and gauges) throughout the Tux bot codebase.
"""

from __future__ import annotations

from typing import Any

import sentry_sdk
from loguru import logger

from .config import is_initialized

__all__ = [
    "record_command_metric",
    "record_database_metric",
    "record_api_metric",
    "record_cog_metric",
    "record_cache_metric",
    "record_task_metric",
]


def _safe_metric_call(
    metric_func: Any,
    name: str,
    value: float,
    *,
    unit: str | None = None,
    attributes: dict[str, str | bool | float | int] | None = None,
) -> None:
    """Safely call a Sentry metric function with error handling.

    Parameters
    ----------
    metric_func : Any
        The Sentry metrics function to call (count, distribution, gauge).
    name : str
        The metric name.
    value : float
        The metric value.
    unit : str | None, optional
        The unit of measurement.
    attributes : dict[str, str | bool | float | int] | None, optional
        Additional attributes for the metric.
    """
    if not is_initialized():
        return

    try:
        if unit:
            metric_func(name, value, unit=unit, attributes=attributes or {})
        else:
            metric_func(name, value, attributes=attributes or {})
    except Exception as e:
        logger.debug(f"Failed to record Sentry metric {name}: {e}")


def record_command_metric(
    command_name: str,
    execution_time_ms: float,
    *,
    success: bool = True,
    error_type: str | None = None,
    command_type: str = "unknown",
) -> None:
    """Record command execution metrics.

    Parameters
    ----------
    command_name : str
        The name of the command executed.
    execution_time_ms : float
        Command execution time in milliseconds.
    success : bool, optional
        Whether the command executed successfully, by default True.
    error_type : str | None, optional
        The type of error if the command failed, by default None.
    command_type : str, optional
        The type of command (prefix, slash, hybrid), by default "unknown".
    """
    attributes: dict[str, str | bool | float | int] = {
        "command": command_name,
        "command_type": command_type,
        "success": success,
    }

    if error_type:
        attributes["error_type"] = error_type

    # Record execution time as distribution
    _safe_metric_call(
        sentry_sdk.metrics.distribution,
        "bot.command.execution_time",
        execution_time_ms,
        unit="millisecond",
        attributes=attributes,
    )

    # Record command usage count
    _safe_metric_call(
        sentry_sdk.metrics.count,
        "bot.command.usage",
        1,
        attributes=attributes,
    )

    # Record failure count if command failed
    if not success:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.command.failures",
            1,
            attributes=attributes,
        )


def record_database_metric(
    operation: str,
    duration_ms: float,
    *,
    table: str | None = None,
    retry_count: int = 0,
    success: bool = True,
    error_type: str | None = None,
) -> None:
    """Record database operation metrics.

    Parameters
    ----------
    operation : str
        The database operation (query, insert, update, delete, etc.).
    duration_ms : float
        Operation duration in milliseconds.
    table : str | None, optional
        The table name if applicable, by default None.
    retry_count : int, optional
        Number of retries if operation was retried, by default 0.
    success : bool, optional
        Whether the operation succeeded, by default True.
    error_type : str | None, optional
        The type of error if operation failed, by default None.
    """
    attributes: dict[str, str | bool | float | int] = {
        "operation": operation,
        "success": success,
    }

    if table:
        attributes["table"] = table
    if retry_count > 0:
        attributes["retry_count"] = retry_count
    if error_type:
        attributes["error_type"] = error_type

    # Record query execution time
    _safe_metric_call(
        sentry_sdk.metrics.distribution,
        "bot.database.operation.duration",
        duration_ms,
        unit="millisecond",
        attributes=attributes,
    )

    # Record operation count
    _safe_metric_call(
        sentry_sdk.metrics.count,
        "bot.database.operation.count",
        1,
        attributes=attributes,
    )

    # Record retries if any
    if retry_count > 0:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.database.retries",
            retry_count,
            attributes={"operation": operation, "table": table or "unknown"},
        )

    # Record failures if operation failed
    if not success:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.database.failures",
            1,
            attributes=attributes,
        )


def record_api_metric(
    service: str,
    endpoint: str,
    duration_ms: float,
    *,
    status_code: int | None = None,
    method: str = "GET",
    rate_limited: bool = False,
    success: bool = True,
) -> None:
    """Record external API call metrics.

    Parameters
    ----------
    service : str
        The API service name (e.g., "discord", "tldr", "wolfram").
    endpoint : str
        The API endpoint or operation name.
    duration_ms : float
        API call duration in milliseconds.
    status_code : int | None, optional
        HTTP status code if applicable, by default None.
    method : str, optional
        HTTP method if applicable, by default "GET".
    rate_limited : bool, optional
        Whether the request was rate limited, by default False.
    success : bool, optional
        Whether the API call succeeded, by default True.
    """
    attributes: dict[str, str | bool | float | int] = {
        "service": service,
        "endpoint": endpoint,
        "method": method,
        "success": success,
        "rate_limited": rate_limited,
    }

    if status_code:
        attributes["status_code"] = status_code

    # Record API call latency
    _safe_metric_call(
        sentry_sdk.metrics.distribution,
        "bot.api.call.duration",
        duration_ms,
        unit="millisecond",
        attributes=attributes,
    )

    # Record API call count
    _safe_metric_call(
        sentry_sdk.metrics.count,
        "bot.api.call.count",
        1,
        attributes=attributes,
    )

    # Record rate limits
    if rate_limited:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.api.rate_limits",
            1,
            attributes={"service": service, "endpoint": endpoint},
        )

    # Record failures
    if not success:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.api.failures",
            1,
            attributes=attributes,
        )


def record_cog_metric(
    cog_name: str,
    operation: str,
    duration_ms: float | None = None,
    *,
    success: bool = True,
    error_type: str | None = None,
) -> None:
    """Record cog operation metrics.

    Parameters
    ----------
    cog_name : str
        The name of the cog.
    operation : str
        The operation (load, unload, reload, etc.).
    duration_ms : float | None, optional
        Operation duration in milliseconds, by default None.
    success : bool, optional
        Whether the operation succeeded, by default True.
    error_type : str | None, optional
        The type of error if operation failed, by default None.
    """
    attributes: dict[str, str | bool | float | int] = {
        "cog": cog_name,
        "operation": operation,
        "success": success,
    }

    if error_type:
        attributes["error_type"] = error_type

    # Record operation count
    _safe_metric_call(
        sentry_sdk.metrics.count,
        "bot.cog.operation.count",
        1,
        attributes=attributes,
    )

    # Record duration if provided
    if duration_ms is not None:
        _safe_metric_call(
            sentry_sdk.metrics.distribution,
            "bot.cog.operation.duration",
            duration_ms,
            unit="millisecond",
            attributes=attributes,
        )

    # Record failures
    if not success:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.cog.failures",
            1,
            attributes=attributes,
        )


def record_cache_metric(
    cache_name: str,
    operation: str,
    *,
    hit: bool = False,
    miss: bool = False,
    duration_ms: float | None = None,
    size: int | None = None,
) -> None:
    """Record cache operation metrics.

    Parameters
    ----------
    cache_name : str
        The name of the cache (e.g., "tldr", "prefix", "emoji").
    operation : str
        The cache operation (get, set, delete, update, etc.).
    hit : bool, optional
        Whether it was a cache hit, by default False.
    miss : bool, optional
        Whether it was a cache miss, by default False.
    duration_ms : float | None, optional
        Operation duration in milliseconds, by default None.
    size : int | None, optional
        Cache size if applicable, by default None.
    """
    attributes: dict[str, str | bool | float | int] = {
        "cache": cache_name,
        "operation": operation,
    }

    # Record cache hits/misses
    if hit:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.cache.hits",
            1,
            attributes=attributes,
        )
    elif miss:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.cache.misses",
            1,
            attributes=attributes,
        )

    # Record operation duration if provided
    if duration_ms is not None:
        _safe_metric_call(
            sentry_sdk.metrics.distribution,
            "bot.cache.operation.duration",
            duration_ms,
            unit="millisecond",
            attributes=attributes,
        )

    # Record cache size as gauge if provided
    if size is not None:
        _safe_metric_call(
            sentry_sdk.metrics.gauge,
            "bot.cache.size",
            float(size),
            attributes={"cache": cache_name},
        )


def record_task_metric(
    task_name: str,
    duration_ms: float,
    *,
    success: bool = True,
    error_type: str | None = None,
    task_type: str = "background",
) -> None:
    """Record background task execution metrics.

    Parameters
    ----------
    task_name : str
        The name of the task.
    duration_ms : float
        Task execution duration in milliseconds.
    success : bool, optional
        Whether the task executed successfully, by default True.
    error_type : str | None, optional
        The type of error if task failed, by default None.
    task_type : str, optional
        The type of task (background, scheduled, periodic), by default "background".
    """
    attributes: dict[str, str | bool | float | int] = {
        "task": task_name,
        "task_type": task_type,
        "success": success,
    }

    if error_type:
        attributes["error_type"] = error_type

    # Record task execution time
    _safe_metric_call(
        sentry_sdk.metrics.distribution,
        "bot.task.execution_time",
        duration_ms,
        unit="millisecond",
        attributes=attributes,
    )

    # Record task execution count
    _safe_metric_call(
        sentry_sdk.metrics.count,
        "bot.task.executions",
        1,
        attributes=attributes,
    )

    # Record failures
    if not success:
        _safe_metric_call(
            sentry_sdk.metrics.count,
            "bot.task.failures",
            1,
            attributes=attributes,
        )
