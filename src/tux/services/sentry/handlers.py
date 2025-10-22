"""Event filtering and processing handlers for Sentry."""

from __future__ import annotations

from typing import Any

from sentry_sdk.types import Event


def before_send(event: Event, hint: dict[str, Any]) -> Event | None:
    """
    Filter and modify events before sending to Sentry.

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

    return None if event.get("logger") in excluded_loggers else event


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

    Returns
    -------
    float
        Sampling rate between 0.0 and 1.0.
    """
    transaction_context = sampling_context.get("transaction_context", {})
    op = transaction_context.get("op", "")
    if op in ["discord.command", "discord.interaction"]:
        return 0.1
    if op in ["database.query", "http.request"]:
        return 0.05
    return 0.02 if op in ["task.background", "task.scheduled"] else 0.01


def get_span_operation_mapping(op: str) -> str:
    """
    Map span operations to standardized names.

    Returns
    -------
    str
        Standardized operation name.
    """
    mapping = {
        "db": "database.query",
        "database": "database.query",
        "sql": "database.query",
        "query": "database.query",
        "http": "http.request",
        "request": "http.request",
        "api": "http.request",
        "discord": "discord.api",
        "command": "discord.command",
        "interaction": "discord.interaction",
        "task": "task.background",
        "background": "task.background",
        "scheduled": "task.scheduled",
        "cache": "cache.operation",
        "redis": "cache.operation",
        "file": "file.operation",
        "io": "file.operation",
    }
    return mapping.get(op.lower(), op)


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
        (operation for keywords, operation in mappings if any(keyword in name_lower for keyword in keywords)),
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
        if op in ["http.request"] and any(domain in description for domain in ["discord.com", "discordapp.com"]):
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
