---
title: Bot Core
description: Tux Discord bot core implementation with lifecycle management, database integration, telemetry, and graceful resource cleanup.
tags:
  - developer-guide
  - concepts
  - core
---

# Bot Core

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The `Tux` class (`src/tux/core/bot.py`) is the main bot class that extends discord.py's `commands.Bot`. It orchestrates all major components including database access, cog loading, telemetry, background tasks, and lifecycle management.

## Overview

The `Tux` class is the heart of the Discord bot, providing:

- **Database Integration** - Automatic database access via `self.db`
- **Cog Management** - Extension loading with priority ordering
- **Telemetry & Monitoring** - Sentry integration and performance tracking
- **Background Tasks** - Task monitoring and cleanup
- **Emoji Management** - Custom emoji resolution and caching
- **Lifecycle Management** - Structured startup and shutdown sequences

## Bot Initialization

When you create a `Tux` instance, it initializes services and schedules async setup:

**Initialized Services:**

- `task_monitor` - Background task management
- `db_service` - Database connection manager
- `sentry_manager` - Error tracking and telemetry
- `emoji_manager` - Custom emoji resolver
- `console` - Rich console for formatted output

**Initialization Features:**

- **Lazy Setup** - Async initialization scheduled to avoid blocking
- **Service Injection** - All major services initialized automatically
- **State Tracking** - Flags prevent duplicate operations and track lifecycle
- **Error Prevention** - Guards against calling async operations before event loop is ready

The bot uses lazy initialization—expensive operations like database connections and cog loading happen asynchronously after the bot instance is created.

## Database Access

### Using the Database Property

Access the database through `self.db`, which provides access to all database controllers:

```python
# In your cogs
user = await self.bot.db.users.get_by_id(user_id)
config = await self.bot.db.guild_config.get_by_id(guild_id)
case = await self.bot.db.cases.create_case(case_data)
```

**Available Controllers:**

- `self.db.users` - User management and profiles
- `self.db.guild_config` - Guild-specific settings
- `self.db.cases` - Moderation case tracking
- `self.db.levels` - User leveling system
- `self.db.permissions` - Permission management
- `self.db.snippets` - Code snippet storage

The database coordinator is created lazily when first accessed, then cached for subsequent use. This provides efficient database access with connection pooling and automatic transaction management.

## Lifecycle Hooks

The bot uses Discord.py lifecycle hooks to coordinate startup and shutdown:

### Setup Hook

The `setup_hook()` is called automatically by discord.py during the login phase. It:

- Initializes the emoji manager
- Guards against duplicate initialization
- Orchestrates specialized setup services (database, permissions, prefixes, cogs)
- Schedules post-ready startup tasks

This ensures services are ready before Discord connection begins.

### Post-Ready Startup

After the bot connects to Discord and becomes ready, post-ready tasks execute:

1. **Wait until Ready** - Ensures internal cache is fully populated
2. **Record Timestamp** - Marks when bot became operational
3. **Display Banner** - Shows formatted startup information
4. **Enable Sentry Instrumentation** - Starts command performance tracking
5. **Record Statistics** - Captures initial bot metrics

These tasks happen automatically—you don't need to manage them yourself.

### Disconnect Handling

When the bot disconnects from Discord, it:

- Logs the disconnection
- Reports to Sentry for monitoring
- Relies on discord.py's automatic reconnection

Disconnections are normal and handled automatically. They're only concerning if they happen frequently.

## Telemetry & Monitoring

### Sentry Integration

Sentry is integrated throughout the bot lifecycle:

- **Command Tracing** - All commands automatically tracked for performance
- **Bot Statistics** - Guild/user/channel counts and uptime recorded
- **Error Reporting** - All exceptions captured with context
- **Performance Spans** - Setup, shutdown, and major operations traced

Command instrumentation happens automatically after cogs load. You don't need to add tracing code to your commands.

### Bot Statistics

The bot records statistics to Sentry context:

- Guild count - Number of servers bot is in
- User count - Total unique users cached
- Channel count - Total channels across all guilds
- Uptime - Time since bot became operational

These statistics help monitor bot growth and performance over time.

## Background Task Management

The `TaskMonitor` manages all background tasks:

**Task Monitor Responsibilities:**

- **Task Registration** - Tracks all periodic tasks
- **Graceful Cancellation** - Proper cleanup during shutdown
- **Resource Management** - Prevents task leaks
- **Error Handling** - Task failure recovery and reporting

Register tasks with the monitor to ensure they're cleaned up properly during shutdown:

```python
# In your cog
self.bot.task_monitor.register_task(my_background_task)
```

The task monitor ensures all tasks are cancelled and awaited during shutdown, preventing resource leaks.

## Emoji Management

The emoji manager provides fast emoji resolution:

**Features:**

- **Custom Emoji Caching** - Fast lookup of guild-specific emojis
- **Unicode Fallback** - Graceful degradation for missing emojis
- **Performance Optimization** - Batched loading and caching
- **Cross-Guild Support** - Emoji resolution across all joined guilds

Access emojis through the bot instance:

```python
emoji = self.bot.emoji_manager.get_emoji(emoji_id)
resolved = self.bot.emoji_manager.resolve_emoji("thumbsup", guild_id)
```

## Shutdown Management

The bot provides graceful shutdown with proper resource cleanup:

**Shutdown Phases:**

1. **Task Cleanup** - Cancels and awaits all background tasks
2. **Connection Closure** - Closes Discord connection via `bot.close()`
3. **External Resources** - Closes database and HTTP connections

Shutdown is idempotent—calling it multiple times is safe. All connections are closed with error isolation, so one failure doesn't prevent others from closing.

**Connection Cleanup Order:**

1. Discord gateway/WebSocket connection
2. Database connection pool
3. HTTP client session and connection pool

This order ensures dependencies are closed before the resources they depend on.

## Accessing Bot Services

In your cogs, access bot services through `self.bot`:

```python
class MyCog(BaseCog):
    @commands.command()
    async def my_command(self, ctx):
        # Database access
        user = await self.bot.db.users.get_by_id(ctx.author.id)
        
        # Sentry
        self.bot.sentry_manager.capture_message("Command executed")
        
        # Emoji
        emoji = self.bot.emoji_manager.get_emoji(emoji_id)
        
        # Task monitor
        self.bot.task_monitor.register_task(my_task)
```

All services are available through the bot instance, making dependency injection straightforward.

## Best Practices

### Use Database Controllers

Access the database through `self.bot.db` controllers. Don't access the database service directly—controllers provide better type safety and consistent APIs.

### Register Background Tasks

Register all background tasks with the task monitor. This ensures proper cleanup during shutdown and prevents resource leaks.

### Handle Errors Gracefully

Use try/except blocks and report errors to Sentry. The bot captures errors automatically, but adding context helps debugging.

### Clean Up Resources

If you create custom resources, clean them up during cog unload. The bot handles its own resources, but you're responsible for your custom ones.

## Troubleshooting

### Startup Failures

**Database Connection Failed:**

Check database connectivity and configuration:

```bash
uv run db health
env | grep -E "(POSTGRES|DATABASE)"
```

**Cog Loading Failed:**

Check for import errors or syntax issues:

```bash
python -c "import tux.modules.moderation.ban"
python -m py_compile src/tux/modules/moderation/ban.py
```

**Discord Connection Issues:**

Verify bot token and intents:

```bash
env | grep BOT_TOKEN
# Check Discord Developer Portal for required intents
```

### Runtime Issues

**Memory Leaks:**

Monitor task count and check for hanging tasks:

```bash
ps aux | grep -E "(python|tux)"
```

**Performance Problems:**

Check database connection pool and cache statistics:

```bash
uv run db status
```

**Connection Issues:**

Test Discord connectivity:

```bash
# Verify bot token and intents
env | grep BOT_TOKEN
```

## Resources

- **Source Code**: `src/tux/core/bot.py`
- **Setup Orchestrator**: See lifecycle documentation
- **Database Coordinator**: See database documentation
- **Sentry Integration**: See `../../best-practices/sentry/index.md` for details
- **Task Monitor**: `src/tux/core/task_monitor.py`
