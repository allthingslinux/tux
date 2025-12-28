---
title: Application Layer
description: Tux application entrypoint and lifecycle management with signal handling, configuration validation, and graceful startup/shutdown flows.
tags:
  - developer-guide
  - concepts
  - core
  - architecture
---

# Application Layer

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The application layer (`src/tux/core/app.py`) orchestrates Tux's complete lifecycle from startup to shutdown. It handles initialization, signal handling, configuration validation, and graceful error recovery.

## Overview

The application layer manages two main responsibilities:

- **Command Prefix Resolution** - Dynamic prefix system with per-guild customization and caching
- **Bot Lifecycle Management** - Complete startup and shutdown orchestration through the `TuxApp` class

## Command Prefix Resolution

Tux uses a priority-based prefix resolution system that supports per-guild customization while maintaining fast performance through caching.

### How Prefix Resolution Works

When a message arrives, Tux checks prefixes in this order:

1. **Environment Override** - If `BOT_INFO__PREFIX` is set, all guilds use that prefix
2. **DM Channels** - Direct messages always use the default prefix (no guild context)
3. **Guild Cache** - Fast in-memory lookup for guild-specific prefixes
4. **Database Fallback** - Cache miss triggers a database lookup and cached result return
5. **Default Fallback** - Configuration default if database lookup fails

The prefix manager caches guild prefixes in memory for sub-millisecond lookups. If the database is unavailable, it gracefully falls back to the default prefix, so commands still work.

### Performance Features

- **In-memory caching** via `PrefixManager` for fast lookups
- **Lazy initialization** - prefix manager loads after bot setup
- **Graceful degradation** - falls back to defaults if database unavailable

## Bot Lifecycle Management

The `TuxApp` class manages the complete bot lifecycle with structured phases and comprehensive error handling.

### Startup Sequence

The bot startup follows a carefully orchestrated sequence:

```mermaid
graph TD
    A[Logging Configuration] --> B[Sentry Setup]
    B --> C[Signal Handler Registration]
    C --> D[Configuration Validation]
    D --> E[Owner ID Resolution]
    E --> F[Bot Instance Creation]
    F --> G[Discord Login]
    G --> H[Discord Connection]
```

**Startup Steps:**

1. **Logging Configuration** - Logging configured as fallback (normally done in CLI script). Must be before Sentry since Sentry uses the logger
2. **Sentry Initialization** - Error tracking set up to capture any startup failures
3. **Signal Handler Registration** - Event loop signal handlers registered for graceful shutdown
4. **Configuration Validation** - Bot token and critical settings verified before proceeding
5. **Owner ID Resolution** - Bot owner and optional sysadmin IDs determined
6. **Bot Instance Creation** - Tux bot instance created with proper configuration
7. **Discord Login** - Performs authentication and triggers the core setup hook (database, cogs, etc.)
8. **Discord Connection** - Establishes WebSocket connection to Discord gateway

### Signal Handling

Tux handles shutdown signals gracefully using standard asynchronous patterns.

**Operation:**

- Event loop signal handlers provide immediate response to SIGINT and SIGTERM
- Both signals trigger a graceful shutdown by calling `bot.close()`
- The bot connection naturally terminates, allowing for clean resource disposal
- Background tasks are cancelled and resources cleaned up properly

### Error Handling

The application layer provides comprehensive error handling with appropriate exit codes:

- **Exit Code 0** - Normal completion (rare, usually exits via signal)
- **Exit Code 1** - Startup failure due to error
- **Exit Code 130** - User-requested shutdown (SIGINT/Ctrl+C or SIGTERM)

All errors are captured by Sentry with context, and startup failures include helpful error messages guiding you to fix configuration issues.

### Shutdown Sequence

When shutting down, Tux performs cleanup in this order:

1. **Bot Shutdown** - Closes Discord connection via `bot.close()`, stops background tasks
2. **Resource Cleanup** - Closes database connections, HTTP clients
3. **Sentry Flush** - Sends any pending error reports (timeout-protected)
4. **Exit Code Determination** - Returns appropriate exit code based on shutdown type

Shutdown always completes cleanup, even if errors occur during the process.

## Configuration Integration

The application layer integrates deeply with Tux's configuration system, reading from multiple sources:

- **Environment Variables** - `.env` file for secrets and overrides
- **TOML/YAML/JSON files** - Static configuration files
- **Database** - Guild-specific settings (prefixes, permissions)
- **Runtime Flags** - CLI arguments and dynamic settings

Configuration is validated before creating expensive resources, preventing wasted startup time when configuration is invalid.

## Using the Application Layer

### Starting the Bot

Start the bot using the CLI command:

```bash
# Standard startup
uv run tux start

# With debug logging
uv run tux start --debug

# Check configuration first
uv run config validate
```

The application layer handles all lifecycle management automatically. You don't need to interact with `TuxApp` directly unless you're embedding Tux in another application.

### Exit Codes

The application returns exit codes you can use in scripts and systemd services:

- **0** - Normal completion
- **1** - Startup error (check logs and configuration)
- **130** - User-requested shutdown (normal for Ctrl+C)

Use exit codes in deployment scripts to detect startup failures:

```bash
uv run tux start
if [ $? -eq 1 ]; then
    echo "Bot failed to start - check logs"
    exit 1
fi
```

## Troubleshooting

### Startup Failures

**No Bot Token:**

If you see "No bot token provided", set `BOT_TOKEN` in your `.env` file. The application validates the token before attempting Discord connection.

**Database Connection Failed:**

Check your database configuration:

```bash
# Check database connectivity
uv run db health

# Verify environment variables
env | grep -E "(POSTGRES|DATABASE)"
```

**Cog Loading Failed:**

If cogs fail to load, check:

1. Cog files for syntax errors
2. Missing dependencies
3. Configuration requirements

Enable debug logging to see detailed error messages:

```bash
LOG_LEVEL=DEBUG uv run tux start
```

### Shutdown Issues

**Force Shutdown:**

If the bot doesn't shut down gracefully:

```bash
# Send SIGTERM (graceful)
kill -TERM $(pgrep -f "uv run tux")

# Send SIGKILL (force) if needed
kill -KILL $(pgrep -f "uv run tux")
```

**Hanging Processes:**

Check for hanging processes:

```bash
ps aux | grep tux
```

## Best Practices

### Configuration First

Validate configuration before creating expensive resources. This prevents wasted startup time and provides clear error messages when configuration is invalid.

### Graceful Shutdown

Always support SIGTERM/SIGINT for container orchestration. Tux handles these signals automatically, but ensure your custom code also handles shutdown gracefully.

### Error Recovery

Use structured exceptions and include context in error reports. The application layer captures errors automatically, but adding context helps debugging.

### Resource Cleanup

Always clean up resources during shutdown. The application layer handles bot resources, but clean up any custom resources you create.

## Resources

- **Source Code**: `src/tux/core/app.py`
- **Bot Class**: See `bot.md` for Discord integration details
- **Configuration**: See configuration documentation for setup
- **Sentry Integration**: See `../../best-practices/sentry/index.md` for error tracking details
