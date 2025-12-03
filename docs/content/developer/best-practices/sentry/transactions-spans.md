---
title: Transactions and Spans
description: How to use transactions and spans for tracing in Tux
tags:
  - developer-guide
  - best-practices
  - sentry
---

# Transactions and Spans

Transactions and spans provide detailed tracing for user-facing operations. This guide shows you how to implement them in Tux.

## Overview

- **Transactions** - Track complete user-facing operations (commands, API requests)
- **Spans** - Track individual operations within a transaction (database queries, API calls)
- **Span Data** - Add context to spans for debugging (query details, row counts, etc.)

## Automatic Instrumentation

Commands are automatically instrumented with transactions:

```python
@commands.command()
async def ping(ctx):
    # Automatically wrapped in a transaction
    # Transaction name: "command.ping"
    await ctx.send("Pong!")
```

You don't need to manually create transactions for commands—this happens automatically via `instrument_bot_commands()`.

## Creating Custom Transactions

For non-command operations that are user-facing, create custom transactions:

```python
from tux.services.sentry import start_transaction

with start_transaction(op="task", name="process_daily_report") as txn:
    await collect_statistics()
    await send_report()
```

## Creating Spans

Spans break down work within a transaction:

```python
@commands.command()  # Automatically a transaction
async def get_user(ctx, user_id: int):
    # Span for database query
    with start_span("db.query", name="Fetch user"):
        user = await db.get_user(user_id)
    
    # Span for API call
    with start_span("api.call", name="Fetch user avatar"):
        avatar = await fetch_avatar(user.id)
    
    await ctx.send(f"User: {user.name}")
```

## Adding Span Data

Use `span.set_data()` to add context to spans. This data appears in the trace explorer:

```python
from tux.services.sentry import start_span

with start_span("db.query", name="Fetch User") as span:
    user = await db.get_user(user_id)
    
    # Add context to this specific query
    span.set_data("db.table", "users")
    span.set_data("db.query_type", "SELECT")
    span.set_data("db.rows_returned", 1)
    span.set_data("db.user_id", user_id)
```

**When to use span data:**

- Operation-specific details (query text, row counts, file paths)
- Context for debugging specific operations
- Data that helps understand what happened in a particular span

## Using Decorators

You can use decorators to automatically wrap functions:

```python
from tux.services.sentry import transaction, span

# Wrap entire function with transaction
@transaction(op="task.background", name="daily_cleanup")
async def perform_daily_cleanup():
    await cleanup_old_records()

# Wrap function with span (within existing transaction)
@span(op="database.query", description="Fetch user by ID")
async def get_user(user_id: int):
    return await db.get_user(user_id)
```

## Span Data vs Tags

- **Tags** (`span.set_tag()`) - Used for **filtering** in Sentry UI
- **Data** (`span.set_data()`) - Used for **context** in trace explorer

```python
# Tags for filtering
span.set_tag("environment", "production")
span.set_tag("user_type", "premium")

# Data for context
span.set_data("db.query", "SELECT * FROM users")
span.set_data("db.rows_affected", 42)
```

## Common Patterns

### Database Operations

```python
@commands.command()  # Transaction
async def get_user(ctx, user_id: int):
    with start_span("db.query", name="Fetch User") as span:
        user = await db.get_user(user_id)
        
        # Span data for this query
        span.set_data("db.table", "users")
        span.set_data("db.operation", "SELECT")
        span.set_data("db.user_id", user_id)
        span.set_data("db.rows_returned", 1 if user else 0)
    
    await ctx.send(f"User: {user.name}")
```

### API Calls

```python
@commands.command()  # Transaction
async def fetch_data(ctx):
    with start_span("http.client", name="Call External API") as span:
        response = await httpx.get("https://api.example.com/data")
        
        # Span data for this API call
        span.set_data("http.url", "https://api.example.com/data")
        span.set_data("http.method", "GET")
        span.set_data("http.status_code", response.status_code)
        span.set_data("http.response_size_bytes", len(response.content))
    
    await ctx.send(f"Data: {response.text}")
```

### Combining Span Data with Metrics

You can use both span data (for trace context) and metrics (for aggregation):

```python
@commands.command()  # Transaction
async def search_users(ctx, query: str):
    with start_span("db.query", name="Search Users") as span:
        users = await db.search_users(query)
        
        # Span data for this specific query context
        span.set_data("db.query_text", query)
        span.set_data("db.results_count", len(users))
        span.set_data("db.search_type", "full_text")
        
        # Metrics for aggregation across all queries
        from tux.services.sentry.metrics import record_database_metric
        record_database_metric(
            operation="search",
            duration_ms=...,
            success=True,
        )
```

## Best Practices

✅ **Do:**

- Use transactions for user-facing operations
- Use spans for operations within transactions
- Add span data for debugging context
- Use tags for filtering, data for context

❌ **Don't:**

- Use transactions for setup/initialization (use metrics)
- Use spans outside of transactions (use metrics)
- Use span data for filtering (use tags)
- Include sensitive data in span data

## Related Documentation

- [Choosing Instrumentation](./choosing-instrumentation.md) - When to use transactions/spans vs metrics
- [Context and Data](./context-data.md) - Tags, context, scopes, users
- [Metrics](./metrics.md) - Metrics implementation
