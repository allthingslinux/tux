---
title: Logging System
description: Centralized logging configuration using loguru with environment-based levels, third-party interception, and structured logging.
tags:
  - developer-guide
  - concepts
  - core
  - logging
---

# Logging System

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Tux uses loguru for all logging, providing a single global logger configured once at startup. The logging system routes all application and third-party library logs through loguru with consistent formatting, making debugging easier.

## Overview

The logging system provides:

- **Single Global Logger** - One logger configured for the entire application
- **Environment-Based Configuration** - Log levels set via `.env` file
- **Third-Party Interception** - All library logs routed through loguru
- **IDE-Clickable Paths** - File paths in logs are clickable in your IDE
- **Structured Logging** - Support for structured data in log messages

## Basic Usage

Import and use the logger directly—it's pre-configured:

```python
from loguru import logger

logger.info("Bot started successfully")
logger.debug("Processing user request", user_id=12345)
logger.warning("Rate limit approaching", remaining=5)
logger.error("Database connection failed", error=str(e))
```

The logger is configured automatically when Tux starts. The primary configuration happens in the CLI script (`scripts/tux/start.py`) before any other code runs, ensuring the `--debug` flag and environment variables are respected.

As a defensive fallback, logging is also configured in `TuxApp.start()` (`src/tux/core/app.py`) before Sentry initialization. You don't need to set it up yourself.

## Log Levels

Tux uses standard loguru log levels. Choose the appropriate level based on the importance and detail of your message:

### TRACE

Use for very detailed debugging—function entry/exit, variable dumps, and step-by-step execution tracking. Only enabled in development.

```python
logger.trace("Function entered", arg1=value1, arg2=value2)
```

### DEBUG

Use for development debugging—SQL queries, API calls, internal state, and detailed execution flow. Helpful when troubleshooting issues.

```python
logger.debug("Database query executed", query=sql, duration=0.045)
logger.debug("Cache miss, fetching from database", key=cache_key)
```

### INFO

Use for normal operations—startup/shutdown messages, user actions, important state changes, and general application flow.

```python
logger.info("Bot connected to Discord")
logger.info(f"User {user_id} executed command '{command}'")
logger.info("Database migration completed", version="abc123")
```

### SUCCESS

Use for successful operations, achievements, and positive outcomes. More visible than INFO for important successes.

```python
logger.success("User account created successfully", user_id=12345)
logger.success("Configuration saved", guild_id=67890)
```

### WARNING

Use for potentially problematic situations—rate limits approaching, deprecated features, configuration issues, and recoverable errors.

```python
logger.warning("Rate limit approaching", remaining=5)
logger.warning("Using deprecated configuration option", option="old_setting")
```

### ERROR

Use for errors that don't stop the application—failed operations, caught exceptions, and recoverable failures.

```python
logger.error("Failed to send message", channel_id=12345, error=str(e))
logger.error("Database query failed", query=sql, error=str(e))
```

### CRITICAL

Use for critical errors that might stop the application—unrecoverable failures, missing critical configuration, and fatal errors.

```python
logger.critical("Database connection lost", error=str(e))
logger.critical("Missing required configuration", setting="BOT_TOKEN")
```

## Configuration

### Log Level Priority

Log levels are determined in this order (highest to lowest priority):

1. **Explicit Parameter** - `--debug` flag (converts to `level="DEBUG"`) or `configure_logging(level="...")` (highest priority)
2. **Environment Variable** - `LOG_LEVEL=DEBUG` in `.env` file
3. **Debug Flag** - `DEBUG=1` in `.env` sets DEBUG level automatically
4. **Default** - `INFO` level if nothing is configured

The `--debug` flag is handled by the CLI script (`scripts/tux/start.py`) which passes `level="DEBUG"` to `configure_logging()`, making it an explicit parameter with the highest priority.

### Environment Configuration

Set the log level in your `.env` file:

```bash
# Set specific log level
LOG_LEVEL=DEBUG

# Or enable debug mode (sets DEBUG level)
DEBUG=1
```

The logging system reads these values automatically at startup.

### Testing Configuration

For tests, use explicit level configuration:

```python
from tux.core.logging import configure_testing_logging

configure_testing_logging()  # Sets DEBUG level for tests
```

## Log Formatting

Logs are formatted with consistent structure:

```text
HH:mm:ss.SSS | LEVEL     | location:line | message
```

For Tux code, the location shows clickable file paths like `src/tux/core/app.py:167`. For third-party libraries, it shows module and function names like `discord.gateway:on_ready`.

### Structured Logging

Include structured data in your log messages:

```python
logger.info("User action", user_id=12345, action="ban", target_id=67890)
logger.debug("Cache operation", operation="get", key="user:12345", hit=True)
```

Structured data appears in logs and can be parsed by log aggregation tools.

## Third-Party Library Logs

The logging system automatically intercepts logs from third-party libraries and routes them through loguru. This includes:

- Discord.py (discord, discord.client, discord.gateway, discord.http)
- Database libraries (sqlalchemy, asyncpg, psycopg)
- HTTP clients (httpx, aiohttp, urllib3)
- Other common libraries

Third-party logs use appropriate log levels to reduce noise. For example, Discord gateway events are logged at INFO level, while verbose DEBUG messages are suppressed.

## IDE Integration

Log messages include clickable file paths for Tux code. Clicking a path in your IDE opens the file at that line, making debugging faster. Paths are relative to the project root, so they work across different development environments.

## Best Practices

### Use Appropriate Levels

Choose log levels based on importance. Don't use ERROR for warnings, or DEBUG for normal operations. Consistent level usage makes logs easier to filter and understand.

### Include Context

Add relevant context to log messages. Include user IDs, guild IDs, command names, or other identifiers that help trace issues:

```python
# Good: Includes context
logger.error("Failed to ban user", user_id=12345, guild_id=67890, error=str(e))

# Bad: Missing context
logger.error("Failed to ban user")
```

### Avoid Sensitive Data

Never log passwords, API keys, tokens, or other sensitive information. Log enough context to debug issues without exposing secrets.

### Use Structured Data

Prefer structured logging over string formatting for better parsing:

```python
# Good: Structured data
logger.info("Command executed", command="ban", user_id=12345, success=True)

# Less ideal: String formatting
logger.info(f"Command ban executed by user {user_id}, success: {success}")
```

### Don't Over-Log

Avoid logging in tight loops or high-frequency operations. Too many logs make it hard to find important information. Use DEBUG level for detailed logging that can be disabled in production.

## Troubleshooting

### Logs Not Appearing

If logs aren't appearing:

1. Check your log level configuration in `.env`
2. Verify the logging system is initialized at startup
3. Ensure you're using the correct log level for your messages

### Too Many Logs

If logs are too verbose:

1. Increase log level to WARNING or ERROR
2. Check third-party library log levels
3. Reduce DEBUG logging in your code

### Missing Context

If logs lack context:

1. Add structured data to log messages
2. Include relevant IDs and identifiers
3. Use appropriate log levels for visibility

## Resources

- **Source Code**: `src/tux/core/logging.py`
- **Loguru Documentation**: <https://loguru.readthedocs.io/>
- **Best Practices**: See `developer/best-practices/logging.md` for detailed guidelines
