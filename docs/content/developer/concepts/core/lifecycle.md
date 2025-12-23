---
title: Lifecycle Orchestration
description: Complete bot lifecycle orchestration from startup through shutdown, coordinating database, permissions, cogs, and monitoring systems.
tags:
  - developer-guide
  - concepts
  - core
  - lifecycle
---

# Lifecycle Orchestration

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The lifecycle orchestration system (`src/tux/core/setup/`) manages Tux's complete startup and shutdown sequences, coordinating database connections, permission systems, cog loading, caching, and monitoring.

## Overview

The orchestration system ensures reliable initialization with proper error handling and graceful degradation. It follows a layered architecture:

- **Application Layer** - Entry point, signal handling, configuration validation, Discord connection
- **Bot Core Layer** - Discord.py integration, service coordination, lifecycle hooks
- **Setup Orchestration** - Coordinates specialized setup services in a modular sequence
- **Setup Services** - Individual services for database, permissions, prefixes, and cogs

## Startup Sequence

The bot startup follows a carefully orchestrated sequence with multiple phases:

### Application Layer Startup

The `TuxApp` class handles initial startup via `asyncio.run()`:

1. **Sentry Setup** - Error tracking initialized first to capture any failures
2. **Signal Handler Registration** - Native event loop handlers for graceful shutdown
3. **Configuration Validation** - Bot token and critical settings verified
4. **Owner ID Resolution** - Bot owner and optional sysadmin IDs determined
5. **Bot Instance Creation** - Tux bot instance created with proper configuration
6. **Discord Login** - Performs authentication and triggers the core setup hook
7. **Discord Connection** - Establishes WebSocket connection to Discord gateway

### Bot Core Setup

The `Tux` bot class performs async setup during the `setup_hook()` phase:

**Initialization:**

- Services created (database, Sentry, tasks, emoji)
- State flags initialized to track lifecycle
- Guard added to prevent duplicate setup execution

**Setup Orchestration:**

The `BotSetupOrchestrator` iterates through a list of specialized `BaseSetupService` implementations:

1. **Database Setup** - Connection, migrations, schema validation
2. **Permission Setup** - Authorization system initialization
3. **Prefix Setup** - Command prefix caching and manager initialization
4. **Cog Setup** - Extension loading via CogLoader
5. **Monitoring Startup** - Background task monitoring begins

### Setup Service Details

**Database Setup:**

- Establishes connection pool
- Creates tables from SQLModel metadata
- Runs Alembic migrations to latest version
- Validates schema matches model definitions

**Permission Setup:**

- Initializes permission system with database integration
- Sets up command authorization hooks
- Configures role-based access control
- Establishes owner override system

**Cog Setup:**

- Loads Jishaku development tools (optional)
- Loads all bot cogs via CogLoader with priority ordering
- Loads hot reload system for development (optional)

**Prefix Setup Service:**

- Initializes prefix caching system
- Loads all guild prefixes into memory
- Sets up graceful fallback to default prefix
- Configures cache updates on prefix changes

### Post-Ready Startup

After Discord connection, post-ready tasks execute once the bot is fully ready:

1. **Wait until Ready** - Ensures internal cache is populated
2. **Record Timestamp** - Marks when bot became operational
3. **Display Banner** - Shows formatted startup information
4. **Enable Sentry Instrumentation** - Starts command performance tracking
5. **Record Statistics** - Captures initial bot metrics

## Error Handling

### Critical vs Non-Critical Failures

The orchestration system distinguishes between critical and non-critical failures:

**Critical Failures (Bot Cannot Start):**

- Database connection failures
- Permission system initialization failures
- Cog loading failures

These failures prevent the bot from starting and provide clear error messages with recovery instructions.

**Non-Critical Failures (Graceful Degradation):**

- Prefix manager initialization failures (falls back to default prefix)
- Emoji manager failures (continues without custom emoji)
- Hot reload failures (continues without hot reload)

These failures are logged but don't prevent startup. The bot continues with reduced functionality.

### Error Recovery

**Database Failures:**

- Clear error messages with recovery commands
- Sentry reporting for monitoring
- Guidance on starting database services

**Configuration Errors:**

- Cogs requiring missing configuration are skipped gracefully
- Warnings logged with configuration guidance
- Bot continues loading other cogs

**Import Errors:**

- Syntax errors detected before loading
- Import failures cause cog group to fail
- Detailed error messages help debugging

## Shutdown Sequence

The shutdown sequence ensures proper resource cleanup:

### Shutdown Phases

1. **Signal Processing** - Shutdown signals captured and reported to Sentry
2. **Task Cancellation** - All background tasks cancelled and awaited
3. **Bot Shutdown** - Discord connections closed, bot resources cleaned up
4. **Resource Cleanup** - Database connections, HTTP clients closed
5. **Sentry Flush** - Pending error reports sent before exit

### Connection Cleanup Order

Connections are closed in dependency order:

1. Discord gateway/WebSocket connection
2. Database connection pool
3. HTTP client session and connection pool

This ensures dependencies are closed before the resources they depend on.

## Monitoring & Telemetry

### Sentry Integration

All setup phases are tracked with Sentry spans:

- Setup phase tags (database, permissions, cogs)
- Load time metrics for performance analysis
- Error context for debugging failures
- Success/failure status for monitoring

### Performance Metrics

The orchestration system tracks:

- Individual service setup times
- Total startup duration
- Slow component detection
- Cache initialization times

These metrics help identify performance bottlenecks and optimize startup time.

## Understanding the Lifecycle

### When Things Happen

**Before Discord Connection:**

- Sentry initialization
- Signal handler registration
- Configuration validation
- Bot instance creation
- Database setup
- Permission system setup
- Cog loading

**After Discord Connection:**

- Emoji manager initialization
- Startup banner display
- Sentry command instrumentation
- Bot statistics recording

**During Shutdown:**

- Background task cancellation
- Discord connection closure
- Database connection closure
- Sentry event flushing

### Why This Order Matters

**Sentry First:**

Error tracking must be ready before any operations that might fail. This ensures all startup errors are captured.

**Database Before Cogs:**

Cogs often need database access, so the database must be ready before cogs load. This prevents import-time database access issues.

**Handlers Before Modules:**

Event handlers need to be ready before commands that might trigger events. Priority-based loading ensures this.

**Cogs Before Plugins:**

Built-in modules load before custom plugins, ensuring core functionality is available when plugins need it.

## Best Practices

### Handle Setup Errors Gracefully

If your cog requires setup that might fail, use try/except blocks and provide fallback behavior. Don't let setup failures crash the bot.

### Use Appropriate Priorities

Place cogs in the correct priority folders. Handlers go in `services/handlers/`, modules go in `modules/`, and plugins go in `plugins/`.

### Clean Up Resources

If you create resources during setup, clean them up during shutdown. The bot handles its own resources, but you're responsible for custom ones.

### Monitor Performance

Use Sentry telemetry to monitor setup times. Slow setup phases indicate optimization opportunities.

## Troubleshooting

### Startup Failures

**Database Connection Failed:**

Check database configuration and connectivity:

```bash
uv run db health
env | grep -E "(POSTGRES|DATABASE)"
```

**Permission System Failed:**

Check database is accessible and migrations are up to date:

```bash
uv run db status
uv run db dev
```

**Cog Loading Failed:**

Check for import errors or syntax issues:

```bash
python -c "import tux.modules.moderation.ban"
LOG_LEVEL=DEBUG uv run tux start
```

### Slow Startup

If startup is slow:

1. Check Sentry telemetry for slow phases
2. Review cog load times
3. Check database connection pool size
4. Verify migrations aren't taking too long

### Shutdown Issues

If shutdown hangs:

1. Check for background tasks not cancelling
2. Verify database connections are closing
3. Check for hanging HTTP requests
4. Review Sentry telemetry for shutdown errors

## Resources

- **Source Code**: `src/tux/core/setup/`
- **Application Layer**: See `app.md` for startup details
- **Bot Core**: See `bot.md` for bot lifecycle
- **Cog Loader**: See `cog-loader.md` for extension loading
