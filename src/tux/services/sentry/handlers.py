"""Event filtering and processing handlers for Sentry."""

from __future__ import annotations

import re
from typing import Any

from sentry_sdk.types import Event


def _sanitize_sensitive_data(text: str) -> str:
    """
    Sanitize sensitive data from strings to prevent leaking secrets.

    Removes or masks:
    - Database connection strings with passwords
    - API keys in URLs or headers
    - Tokens in various formats
    - Passwords in connection strings

    Parameters
    ----------
    text : str
        The text to sanitize.

    Returns
    -------
    str
        Sanitized text with sensitive data masked.
    """
    # Pattern for database URLs: postgresql://user:password@host
    text = re.sub(
        r"(postgresql|mysql|sqlite)://[^:]+:[^@]+@",
        r"\1://***:***@",
        text,
        flags=re.IGNORECASE,
    )

    # Pattern for API keys in URLs: ?API_KEY=xxx or &api_key=xxx
    text = re.sub(
        r"([?&])(?:api[_-]?key|token|secret|password)=[^&\s]+",
        r"\1***",
        text,
        flags=re.IGNORECASE,
    )

    # Pattern for Bearer tokens: Bearer xxxxx
    text = re.sub(
        r"Bearer\s+[A-Za-z0-9_-]+",
        "Bearer ***",
        text,
        flags=re.IGNORECASE,
    )

    # Pattern for Authorization headers: Authorization: xxxxx
    return re.sub(
        r"Authorization:\s*[^\s]+",
        "Authorization: ***",
        text,
        flags=re.IGNORECASE,
    )


def _sanitize_event_data(event: Event) -> Event:
    """
    Sanitize sensitive data from Sentry event.

    Recursively sanitizes strings in event data to prevent leaking
    passwords, API keys, tokens, and other sensitive information.

    Parameters
    ----------
    event : Event
        The Sentry event to sanitize.

    Returns
    -------
    Event
        The sanitized event.
    """
    sanitized: dict[str, Any] = {}
    for key, value in event.items():
        # Skip sanitization of certain keys that are safe
        if key in ("logger", "level", "timestamp", "event_id"):
            sanitized[key] = value
        elif isinstance(value, str):
            sanitized[key] = _sanitize_sensitive_data(value)
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_event_data(value)  # type: ignore[arg-type]
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_sensitive_data(item) if isinstance(item, str) else item
                for item in value  # type: ignore[misc]
            ]
        else:
            sanitized[key] = value
    return sanitized  # type: ignore[return-value]


def before_send(event: Event, hint: dict[str, Any]) -> Event | None:
    """
    Filter and modify events before sending to Sentry.

    This function:
    1. Filters out noisy loggers (discord, httpx, etc.)
    2. Sanitizes sensitive data (passwords, API keys, tokens)

    Parameters
    ----------
    event : Event
        The Sentry event to potentially filter or modify.
    hint : dict[str, Any]
        Additional context about the event.

    Returns
    -------
    Event | None
        The event if it should be sent, None if it should be filtered out.

    Notes
    -----
    Security: This function sanitizes sensitive data like database passwords,
    API keys, and tokens from error messages to prevent leaking secrets.
    """
    excluded_loggers = {
        "discord.gateway",
        "discord.client",
        "discord.http",
        "httpx",
        "httpcore.http11",
        "httpcore.connection",
        "asyncio",
    }

    # Filter out noisy loggers
    if event.get("logger") in excluded_loggers:
        return None

    # Sanitize sensitive data before sending
    return _sanitize_event_data(event)


def before_send_transaction(event: Event, hint: dict[str, Any]) -> Event | None:
    """
    Filter and group spans before sending transaction events.

    Parameters
    ----------
    event : Event
        The transaction event to process.
    hint : dict[str, Any]
        Additional context about the transaction.

    Returns
    -------
    Event | None
        The modified transaction event.
    """
    if "spans" in event:
        spans = event["spans"]
        if isinstance(spans, list):
            event["spans"] = _filter_and_group_spans(spans)
    return event


def traces_sampler(sampling_context: dict[str, Any]) -> float:
    """
    Determine sampling rate for traces based on context.

    This sampler respects parent sampling decisions to maintain distributed trace
    integrity. If a transaction has a parent (from distributed tracing), it will
    inherit the parent's sampling decision.

    Parameters
    ----------
    sampling_context : dict[str, Any]
        Context containing transaction information and parent sampling decision.

    Returns
    -------
    float
        Sampling rate between 0.0 and 1.0, or boolean (True/False) for absolute decisions.
    """
    # Always inherit parent sampling decision to avoid breaking distributed traces
    # This ensures complete traces across services
    parent_sampled = sampling_context.get("parent_sampled")
    if parent_sampled is not None:
        return float(parent_sampled)

    # Determine sampling rate based on operation type
    transaction_context = sampling_context.get("transaction_context", {})
    op = transaction_context.get("op", "")

    # High-value operations: commands and interactions (10% sampled)
    if op in ["discord.command", "discord.interaction"]:
        return 0.1

    # Medium-value operations: database queries and HTTP requests (5% sampled)
    if op in ["database.query", "http.request"]:
        return 0.05

    # Low-value operations: background tasks (2% sampled)
    # Default: catch-all for other operations (1% sampled)
    return 0.02 if op in ["task.background", "task.scheduled"] else 0.01


def get_span_operation_mapping(op: str) -> str:
    """
    Map span operations to standardized Sentry operation names.

    This function normalizes custom operation names to Sentry's well-known operation
    conventions for better consistency and analysis in Sentry's UI.

    Parameters
    ----------
    op : str
        The original operation name to map.

    Returns
    -------
    str
        Standardized operation name following Sentry conventions.

    Notes
    -----
    Sentry's well-known operations include:
    - `db.query` or `db` for database operations
    - `http.client` for HTTP client requests (not `http.request`)
    - `file.read`, `file.write` for file I/O
    - `task` for background tasks

    This mapping aligns with the operations checked in `traces_sampler`.
    """
    # Normalize to lowercase for case-insensitive matching
    op_lower = op.lower()

    # Direct mappings for exact matches
    mapping = {
        # Database operations - map to "database.query" (matches traces_sampler)
        "db": "database.query",
        "database": "database.query",
        "db.query": "database.query",
        "sql": "database.query",
        # Note: "query" alone is too generic, only map if it's clearly database-related
        # We don't map "query" by itself to avoid false positives
        # HTTP operations - map to "http.request" (matches traces_sampler)
        # Note: Sentry typically uses "http.client" but we use "http.request" for consistency
        "http": "http.request",
        "http.request": "http.request",
        "http.client": "http.request",  # Also accept Sentry's standard
        "request": "http.request",
        # Note: "api" alone is too generic, only map if context suggests HTTP
        # Discord operations - map to specific types (matches traces_sampler)
        "command": "discord.command",
        "discord.command": "discord.command",
        "interaction": "discord.interaction",
        "discord.interaction": "discord.interaction",
        # Note: "discord" alone maps to "discord.api" for general Discord API calls
        "discord": "discord.api",
        "discord.api": "discord.api",
        # Task operations - map to specific types (matches traces_sampler)
        "task": "task.background",
        "task.background": "task.background",
        "background": "task.background",
        "scheduled": "task.scheduled",
        "task.scheduled": "task.scheduled",
        "cron": "task.scheduled",
        "timer": "task.scheduled",
        # Cache operations
        "cache": "cache.operation",
        "cache.operation": "cache.operation",
        "redis": "cache.operation",
        # File I/O operations - use Sentry's specific conventions
        "file": "file.operation",
        "file.read": "file.read",
        "file.write": "file.write",
        "io": "file.operation",
    }

    # Check for exact match first
    if op_lower in mapping:
        return mapping[op_lower]

    # Check for prefix matches (e.g., "db.query.select" -> "database.query")
    # Return original if no mapping found
    return (
        next(
            (
                value
                for key, value in mapping.items()
                if op_lower.startswith((f"{key}.", f"{key}_"))
            ),
            None,
        )
        or op
    )


def get_transaction_operation_mapping(transaction_name: str) -> str:
    """
    Map transaction names to standardized operations.

    Returns
    -------
    str
        Standardized operation name.
    """
    name_lower = transaction_name.lower()

    # Define keyword mappings
    mappings = [
        (["command", "cmd"], "discord.command"),
        (["interaction", "slash"], "discord.interaction"),
        (["task", "background", "job"], "task.background"),
        (["scheduled", "cron", "timer"], "task.scheduled"),
        (["startup", "setup", "init"], "app.startup"),
        (["shutdown", "cleanup", "teardown"], "app.shutdown"),
    ]

    return next(
        (
            operation
            for keywords, operation in mappings
            if any(keyword in name_lower for keyword in keywords)
        ),
        "app.operation",
    )


def _filter_and_group_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Filter and group spans to reduce noise.

    Returns
    -------
    list[dict[str, Any]]
        Filtered and grouped spans.
    """
    filtered_spans: list[dict[str, Any]] = []
    span_groups: dict[str, list[dict[str, Any]]] = {}

    for span in spans:
        op = span.get("op", "")
        description = span.get("description", "")

        # Skip noisy operations
        if op in ["http.request"] and any(
            domain in description for domain in ["discord.com", "discordapp.com"]
        ):
            continue

        # Group similar spans
        group_key = f"{op}:{description[:50]}"
        if group_key not in span_groups:
            span_groups[group_key] = []
        span_groups[group_key].append(span)

    # Add representative spans from each group
    for group_spans in span_groups.values():
        if len(group_spans) == 1:
            filtered_spans.append(group_spans[0])
        else:
            # Create a summary span for grouped operations
            first_span = group_spans[0]
            summary_span = {
                **first_span,
                "description": f"{first_span.get('description', '')} (x{len(group_spans)})",
                "data": {
                    **first_span.get("data", {}),
                    "grouped_count": len(group_spans),
                },
            }
            filtered_spans.append(summary_span)

    return filtered_spans
