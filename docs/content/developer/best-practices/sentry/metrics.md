---
title: Sentry Metrics
description: Using Sentry metrics to track performance and usage throughout Tux
tags:
  - developer-guide
  - best-practices
  - sentry
---

# Sentry Metrics

Tux uses Sentry metrics to track performance, usage patterns, and system health. Metrics help you identify bottlenecks, monitor usage trends, and correlate performance data with errors.

## Overview

Sentry metrics are automatically enabled when Sentry is initialized. The metrics system provides three types of metrics:

- **Counters** - Track event occurrences (command usage, errors, cache hits/misses)
- **Distributions** - Track measurements with percentiles (execution times, latencies)
- **Gauges** - Track current values (cache sizes, connection pool usage)

## Available Metrics Functions

All metrics functions are available from `tux.services.sentry.metrics`:

```python
from tux.services.sentry.metrics import (
    record_command_metric,
    record_database_metric,
    record_api_metric,
    record_cog_metric,
    record_cache_metric,
    record_task_metric,
)
```

## Automatic Metrics

### Command Execution

Command metrics are automatically recorded for all commands:

- **`bot.command.execution_time`** (distribution) - Command execution time in milliseconds
- **`bot.command.usage`** (counter) - Command usage count
- **`bot.command.failures`** (counter) - Command failure count

**Attributes:**

- `command` - Command name
- `command_type` - Type of command (prefix, slash, hybrid)
- `success` - Whether command succeeded
- `error_type` - Error type if command failed

**Integration:** Automatically recorded in `track_command_end()` in `src/tux/services/sentry/context.py`

### Database Operations

Database metrics are automatically recorded for all database operations with retry logic:

- **`bot.database.operation.duration`** (distribution) - Operation duration in milliseconds
- **`bot.database.operation.count`** (counter) - Operation count
- **`bot.database.retries`** (counter) - Retry count
- **`bot.database.failures`** (counter) - Failure count

**Attributes:**

- `operation` - Operation type (query, insert, update, delete)
- `table` - Table name if applicable
- `retry_count` - Number of retries
- `success` - Whether operation succeeded
- `error_type` - Error type if operation failed

**Integration:** Automatically recorded in `_execute_with_retry()` in `src/tux/database/service.py`

## Manual Metrics Recording

### API Calls

Track external API call performance:

```python
from tux.services.sentry.metrics import record_api_metric
import time

start_time = time.perf_counter()
try:
    response = await httpx.get("https://api.example.com/data")
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    record_api_metric(
        service="example_api",
        endpoint="/data",
        duration_ms=duration_ms,
        status_code=response.status_code,
        method="GET",
        success=True,
    )
except httpx.HTTPStatusError as e:
    duration_ms = (time.perf_counter() - start_time) * 1000
    record_api_metric(
        service="example_api",
        endpoint="/data",
        duration_ms=duration_ms,
        status_code=e.response.status_code,
        method="GET",
        success=False,
    )
```

**Metrics Emitted:**

- `bot.api.call.duration` (distribution) - API call latency
- `bot.api.call.count` (counter) - API call count
- `bot.api.rate_limits` (counter) - Rate limit hits
- `bot.api.failures` (counter) - API failure count

### Cog Operations

Track cog loading, unloading, and reloading:

```python
from tux.services.sentry.metrics import record_cog_metric
import time

start_time = time.perf_counter()
try:
    await bot.load_extension("tux.modules.tools.tldr")
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    record_cog_metric(
        cog_name="tldr",
        operation="load",
        duration_ms=duration_ms,
        success=True,
    )
except Exception as e:
    duration_ms = (time.perf_counter() - start_time) * 1000
    record_cog_metric(
        cog_name="tldr",
        operation="load",
        duration_ms=duration_ms,
        success=False,
        error_type=type(e).__name__,
    )
```

**Metrics Emitted:**

- `bot.cog.operation.count` (counter) - Cog operation count
- `bot.cog.operation.duration` (distribution) - Operation duration
- `bot.cog.failures` (counter) - Cog operation failures

### Cache Operations

Track cache performance:

```python
from tux.services.sentry.metrics import record_cache_metric
import time

start_time = time.perf_counter()
cached_value = cache.get("key")
duration_ms = (time.perf_counter() - start_time) * 1000

if cached_value:
    record_cache_metric(
        cache_name="tldr",
        operation="get",
        hit=True,
        duration_ms=duration_ms,
    )
else:
    record_cache_metric(
        cache_name="tldr",
        operation="get",
        miss=True,
        duration_ms=duration_ms,
    )
    # Fetch and cache value
    value = await fetch_value()
    cache.set("key", value)
    
    # Record cache size
    record_cache_metric(
        cache_name="tldr",
        operation="set",
        size=len(cache),
    )
```

**Metrics Emitted:**

- `bot.cache.hits` (counter) - Cache hits
- `bot.cache.misses` (counter) - Cache misses
- `bot.cache.operation.duration` (distribution) - Cache operation duration
- `bot.cache.size` (gauge) - Current cache size

### Background Tasks

Track background task execution:

```python
from tux.services.sentry.metrics import record_task_metric
import time

async def background_task():
    start_time = time.perf_counter()
    try:
        # Task logic
        await do_work()
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        record_task_metric(
            task_name="daily_cleanup",
            duration_ms=duration_ms,
            success=True,
            task_type="scheduled",
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        record_task_metric(
            task_name="daily_cleanup",
            duration_ms=duration_ms,
            success=False,
            error_type=type(e).__name__,
            task_type="scheduled",
        )
```

**Metrics Emitted:**

- `bot.task.execution_time` (distribution) - Task execution time
- `bot.task.executions` (counter) - Task execution count
- `bot.task.failures` (counter) - Task failure count

## Integration Points

### Recommended Integration Locations

1. **TLDR Cache Updates** (`src/tux/modules/tools/tldr.py`)
   - Use `record_cache_metric()` for cache operations
   - Track cache update durations

2. **Discord API Wrappers** (HTTP clients)
   - Use `record_api_metric()` for Discord API calls
   - Track rate limits and latencies

3. **Cog Setup** (`src/tux/core/setup/cog_setup.py`)
   - Use `record_cog_metric()` for cog loading operations
   - Track load times and failures

4. **Background Tasks** (`src/tux/core/task_monitor.py`)
   - Use `record_task_metric()` for periodic tasks
   - Track execution times and failures

5. **Cache Systems** (prefix manager, emoji manager)
   - Use `record_cache_metric()` for cache operations
   - Track hit/miss rates and sizes

## Viewing Metrics in Sentry

1. Navigate to **Discover** in Sentry
2. Select **Metrics** from the dropdown
3. Search for metrics by name (e.g., `bot.command.execution_time`)
4. Filter by attributes (e.g., `command:ping`, `success:true`)
5. View aggregations (p50, p90, p95, p99, min, max, avg)

## Best Practices

1. **Use Appropriate Metric Types**
   - Counters for events (usage, errors, hits/misses)
   - Distributions for measurements (times, latencies, sizes)
   - Gauges for current values (cache sizes, connection counts)

2. **Include Relevant Attributes**
   - Add attributes that help filter and group metrics
   - Use consistent attribute names across related metrics

3. **Record Metrics at Key Points**
   - Record success and failure metrics
   - Include timing for performance-critical operations
   - Track retries and error types

4. **Avoid Over-Metrics**
   - Don't record metrics for every operation
   - Focus on important operations and failure points
   - Use sampling for high-frequency operations if needed

5. **Correlate with Errors**
   - Metrics automatically include trace context
   - Correlate metric spikes with error occurrences
   - Use attributes to filter metrics by error type

## Example: Complete Integration

```python
from tux.services.sentry.metrics import record_api_metric, record_cache_metric
import time

async def fetch_tldr_page(platform: str, command: str, lang: str) -> str:
    """Fetch TLDR page with metrics tracking."""
    cache_key = f"tldr:{platform}:{command}:{lang}"
    
    # Check cache
    start = time.perf_counter()
    cached = cache.get(cache_key)
    cache_duration = (time.perf_counter() - start) * 1000
    
    if cached:
        record_cache_metric(
            cache_name="tldr",
            operation="get",
            hit=True,
            duration_ms=cache_duration,
        )
        return cached
    
    record_cache_metric(
        cache_name="tldr",
        operation="get",
        miss=True,
        duration_ms=cache_duration,
    )
    
    # Fetch from API
    api_start = time.perf_counter()
    try:
        response = await httpx.get(
            f"https://tldr.sh/api/v1/pages/{platform}/{command}",
            params={"lang": lang},
        )
        api_duration = (time.perf_counter() - api_start) * 1000
        
        record_api_metric(
            service="tldr",
            endpoint=f"/pages/{platform}/{command}",
            duration_ms=api_duration,
            status_code=response.status_code,
            method="GET",
            success=True,
        )
        
        content = response.text
        cache.set(cache_key, content)
        
        record_cache_metric(
            cache_name="tldr",
            operation="set",
            size=len(cache),
        )
        
        return content
    except httpx.HTTPStatusError as e:
        api_duration = (time.perf_counter() - api_start) * 1000
        record_api_metric(
            service="tldr",
            endpoint=f"/pages/{platform}/{command}",
            duration_ms=api_duration,
            status_code=e.response.status_code,
            method="GET",
            success=False,
        )
        raise
```

## Related Documentation

- [Sentry Integration](./index.md) - General Sentry setup and configuration
- [Choosing Instrumentation](./choosing-instrumentation.md) - When to use transactions/spans vs metrics
- [Transactions and Spans](./transactions-spans.md) - How to use transactions and spans
- [Context and Data](./context-data.md) - Tags, context, scopes, users
- [Error Handling](../error-handling.md) - Error handling patterns
