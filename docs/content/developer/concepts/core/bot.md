---
title: Bot Core
description: Tux Discord bot core implementation with lifecycle management, database integration, telemetry, and graceful resource cleanup.
---

# Bot Core

The bot core (`src/tux/core/bot.py`) defines the main `Tux` class, which extends discord.py's `commands.Bot` and provides comprehensive lifecycle management including setup orchestration, cog loading, database integration, error handling, telemetry, and graceful resource cleanup.

## Overview

The `Tux` class is the heart of the Discord bot, orchestrating all major components:

- **Database Integration** - Automatic database access via `self.db`
- **Cog Management** - Extension loading with priority ordering
- **Telemetry & Monitoring** - Sentry integration and performance tracking
- **Background Tasks** - Task monitoring and cleanup
- **Emoji Management** - Custom emoji resolution and caching
- **Lifecycle Management** - Structured startup and shutdown sequences

## Class Architecture

### Core Attributes

```python
class Tux(commands.Bot):
    """Main bot class extending discord.py's commands.Bot."""

    # Lifecycle state tracking
    is_shutting_down: bool = False         # Shutdown prevention flag
    setup_complete: bool = False           # Setup completion flag
    start_time: float | None = None        # Uptime tracking timestamp

    # Async tasks
    setup_task: asyncio.Task[None] | None = None     # Async initialization task
    _startup_task: asyncio.Task[None] | None = None  # Post-ready tasks

    # Service integrations
    task_monitor: TaskMonitor              # Background task management
    db_service: DatabaseService            # Database connection manager
    sentry_manager: SentryManager          # Error tracking and telemetry
    prefix_manager: Any | None = None      # Command prefix caching
    emoji_manager: EmojiManager            # Custom emoji resolver

    # UI components
    console: Console                       # Rich console for formatted output
    uptime: float                          # Instance creation timestamp
```

### Initialization Sequence

The bot initialization follows a carefully orchestrated sequence:

```python
def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize bot with lazy async setup."""
    super().__init__(*args, **kwargs)  # discord.py Bot initialization

    # Core state flags
    self.is_shutting_down = False
    self.setup_complete = False
    self.start_time = None

    # Service integrations
    self.task_monitor = TaskMonitor(self)
    self.db_service = DatabaseService()
    self.sentry_manager = SentryManager()
    self.emoji_manager = EmojiManager(self)
    self.console = Console(stderr=True, force_terminal=True)

    # Schedule async setup task creation
    asyncio.get_event_loop().call_soon(self._create_setup_task)
```

**Key Initialization Features:**

- **Lazy Setup** - Async initialization scheduled via `call_soon` to avoid blocking
- **Service Injection** - All major services (database, Sentry, tasks, emoji) initialized
- **State Tracking** - Multiple flags prevent duplicate operations and track lifecycle
- **Error Prevention** - Guards against calling async operations before event loop is ready

## Setup Orchestration

### Async Setup Task Creation

```python
def _create_setup_task(self) -> None:
    """Create setup task in proper event loop context."""
    if self.setup_task is None:
        self.setup_task = asyncio.create_task(self.setup(), name="bot_setup")
```

**Why This Pattern:**

- Prevents `RuntimeError` when creating tasks before event loop is ready
- Uses `call_soon` to defer task creation to next event loop iteration
- Ensures proper async context for database connections and cog loading

### Comprehensive Setup Process

```python
async def setup(self) -> None:
    """Perform one-time bot setup and initialization."""
    with start_span("bot.setup", "Bot setup process") as span:
        # Lazy import to avoid circular dependencies
        from tux.core.setup.orchestrator import BotSetupOrchestrator

        orchestrator = BotSetupOrchestrator(self)
        await orchestrator.setup(span)
```

**Setup Components:**

- **Database Connection** - Connection pool initialization and validation
- **Cog Loading** - Priority-based extension loading with error handling
- **Cache Initialization** - Prefix caches, user caches, guild data
- **Background Tasks** - Periodic maintenance tasks and cleanup routines

### Setup Error Handling

```python
except (TuxDatabaseConnectionError, ConnectionError) as e:
    logger.error("❌ Database connection failed")
    logger.info("💡 To start the database, run: uv run docker up")
    capture_database_error(e, operation="connection")
    raise RuntimeError("Database setup failed") from e
```

**Error Recovery Strategies:**

- **Database Failures** - Clear error messages with recovery instructions
- **Sentry Reporting** - All setup failures captured for monitoring
- **Graceful Failure** - Bot won't start with incomplete setup
- **User Guidance** - Specific commands to resolve common issues

## Database Integration

### Database Coordinator Property

```python
@property
def db(self) -> DatabaseCoordinator:
    """Get database coordinator for accessing database controllers."""
    if self._db_coordinator is None:
        self._db_coordinator = DatabaseCoordinator(self.db_service)
    return self._db_coordinator
```

**Usage Pattern:**

```python
# Access database controllers through bot.db
user = await self.db.users.get_user(user_id)
config = await self.db.guild_config.get_guild_config(guild_id)
case = await self.db.cases.create_case(case_data)
```

**Database Controllers Available:**

- `self.db.users` - User management and profiles
- `self.db.guild_config` - Guild-specific settings
- `self.db.cases` - Moderation case tracking
- `self.db.levels` - User leveling system
- `self.db.permissions` - Permission management
- `self.db.snippets` - Code snippet storage

### Performance Considerations

- **Lazy Initialization** - Coordinator created only when first accessed
- **Connection Pooling** - Efficient database connection reuse
- **Transaction Management** - Automatic transaction handling in controllers
- **Query Optimization** - Built-in caching and prepared statements

## Lifecycle Management

### Discord.py Hook Integration

```python
async def setup_hook(self) -> None:
    """Discord.py lifecycle hook called before connecting to Discord."""
    # Initialize emoji manager
    if not self._emoji_manager_initialized:
        await self.emoji_manager.init()
        self._emoji_manager_initialized = True

    # Check setup task completion
    if self.setup_task and self.setup_task.done():
        if getattr(self.setup_task, "_exception", None) is not None:
            self.setup_complete = False
        else:
            self.setup_complete = True
            logger.info("✅ Bot setup completed successfully")

    # Schedule post-ready startup tasks
    self._startup_task = self.loop.create_task(self._post_ready_startup())
```

**Hook Execution Order:**

1. **Bot Initialization** (`__init__`)
2. **Setup Hook** - Async initialization before Discord connection
3. **Discord Connection** - Login and WebSocket connection
4. **Ready Event** - Bot fully connected and operational

### Post-Ready Startup Sequence

```python
async def _post_ready_startup(self) -> None:
    """Execute post-ready startup tasks after bot is fully connected."""
    # Wait for Discord READY event
    await self.wait_until_ready()

    # Wait for internal setup completion
    await self._wait_for_setup()

    # Record operational start time
    self.start_time = discord.utils.utcnow().timestamp()

    # Display startup banner
    await self._log_startup_banner()

    # Enable Sentry command tracing
    instrument_bot_commands(self)

    # Record initial bot statistics
    self._record_bot_stats()
```

**Post-Ready Sequence:**

1. **Discord Connection** - Wait for WebSocket ready
2. **Internal Setup** - Ensure database and cogs are ready
3. **Timestamp Recording** - Mark operational start time
4. **Banner Display** - Show formatted startup information
5. **Sentry Instrumentation** - Enable command tracing
6. **Statistics Recording** - Capture initial bot metrics

## Telemetry & Monitoring

### Sentry Integration

```python
# Command instrumentation for tracing
instrument_bot_commands(self)

# Bot statistics recording
self.sentry_manager.set_context("bot_stats", {
    "guild_count": len(self.guilds),
    "user_count": len(self.users),
    "channel_count": sum(len(g.channels) for g in self.guilds),
    "uptime": discord.utils.utcnow().timestamp() - (self.start_time or 0),
})
```

**Sentry Features:**

- **Command Tracing** - Automatic performance monitoring for all commands
- **Bot Statistics** - Guild/user/channel counts and uptime
- **Error Reporting** - All exceptions captured with context
- **Performance Spans** - Setup, shutdown, and major operations traced

### Disconnect Monitoring

```python
async def on_disconnect(self) -> None:
    """Handle Discord disconnection events."""
    logger.warning("⚠️ Bot disconnected from Discord")

    if self.sentry_manager.is_initialized:
        self.sentry_manager.set_tag("event_type", "disconnect")
        self.sentry_manager.capture_message(
            "Bot disconnected from Discord, this happens sometimes and is fine as long as it's not happening too often",
            level="info",
        )
```

**Disconnect Handling:**

- **Automatic Reconnection** - discord.py handles reconnection logic
- **Sentry Monitoring** - Disconnect patterns tracked for reliability analysis
- **User Communication** - Appropriate log levels for normal vs concerning disconnects

## Background Task Management

### Task Monitor Integration

```python
# Task monitor initialization
self.task_monitor = TaskMonitor(self)

# Task cleanup during shutdown
await self.task_monitor.cleanup_tasks()
```

**Task Monitor Responsibilities:**

- **Background Task Registration** - Track all periodic tasks
- **Graceful Cancellation** - Proper task cleanup during shutdown
- **Resource Management** - Prevent task leaks and memory issues
- **Error Handling** - Task failure recovery and reporting

### Task Lifecycle

```python
# Task creation and monitoring
self.task_monitor.register_task(my_background_task)

# Cleanup during shutdown
await self.task_monitor.cleanup_tasks()
```

**Task Types Managed:**

- **Periodic Tasks** - Database cleanup, cache refresh, maintenance
- **Event-Driven Tasks** - User activity monitoring, guild updates
- **Background Services** - HTTP polling, external API synchronization

## Emoji Management

### Emoji Manager Integration

```python
# Emoji manager initialization
self.emoji_manager = EmojiManager(self)

# Async initialization in setup hook
await self.emoji_manager.init()
```

**Emoji Manager Features:**

- **Custom Emoji Caching** - Fast lookup of guild-specific emojis
- **Unicode Fallback** - Graceful degradation for missing emojis
- **Performance Optimization** - Batched loading and caching
- **Cross-Guild Support** - Emoji resolution across all joined guilds

### Usage Patterns

```python
# Get emoji by ID
emoji = self.emoji_manager.get_emoji(emoji_id)

# Resolve emoji name to object
resolved = self.emoji_manager.resolve_emoji("thumbsup", guild_id)
```

## Shutdown Management

### Graceful Shutdown Sequence

```python
async def shutdown(self) -> None:
    """Gracefully shut down the bot and clean up all resources."""
    with start_transaction("bot.shutdown", "Bot shutdown process") as transaction:
        # Idempotent guard
        if self.is_shutting_down:
            return
        self.is_shutting_down = True

        # Phase 1: Handle setup task
        await self._handle_setup_task()

        # Phase 2: Clean up background tasks
        await self._cleanup_tasks()

        # Phase 3: Close external connections
        await self._close_connections()
```

**Shutdown Phases:**

1. **Setup Task Cancellation** - Stop any ongoing initialization
2. **Task Cleanup** - Cancel and await all background tasks
3. **Connection Closure** - Discord, database, HTTP client shutdown

### Connection Closure Order

```python
async def _close_connections(self) -> None:
    """Close all external connections with error handling."""
    # 1. Discord gateway/WebSocket connection
    await self.close()

    # 2. Database connection pool
    await self.db_service.disconnect()

    # 3. HTTP client session and connection pool
    await http_client.close()
```

**Connection Cleanup:**

- **Error Isolation** - One failure doesn't prevent others from closing
- **Sentry Reporting** - Shutdown errors captured for debugging
- **Resource Safety** - All connections properly closed to prevent leaks

## Performance Monitoring

### Cache Statistics

```python
def get_prefix_cache_stats(self) -> dict[str, int]:
    """Get prefix cache statistics for monitoring."""
    if self.prefix_manager:
        return self.prefix_manager.get_cache_stats()
    return {"cached_prefixes": 0, "cache_loaded": 0, "default_prefix": 0}
```

**Cache Metrics:**

- **cached_prefixes** - Number of guild prefixes in cache
- **cache_loaded** - Whether cache has been initialized
- **default_prefix** - Fallback prefix usage count

### Bot Statistics

```python
def _record_bot_stats(self) -> None:
    """Record basic bot statistics to Sentry context."""
    if not self.sentry_manager.is_initialized:
        return

    self.sentry_manager.set_context("bot_stats", {
        "guild_count": len(self.guilds),
        "user_count": len(self.users),
        "channel_count": sum(len(g.channels) for g in self.guilds),
        "uptime": discord.utils.utcnow().timestamp() - (self.start_time or 0),
    })
```

**Statistics Tracked:**

- **Guild Count** - Number of servers bot is in
- **User Count** - Total unique users cached
- **Channel Count** - Total channels across all guilds
- **Uptime** - Time since bot became operational

## Startup Banner

### Banner Display

```python
async def _log_startup_banner(self) -> None:
    """Display the startup banner with bot information."""
    banner = create_banner(
        bot_name=CONFIG.BOT_INFO.BOT_NAME,
        version=get_version(),
        bot_id=str(self.user.id) if self.user else None,
        guild_count=len(self.guilds),
        user_count=len(self.users),
        prefix=CONFIG.get_prefix(),
    )
    self.console.print(banner)
```

**Banner Information:**

- **Bot Name** - Configured bot display name
- **Version** - Current bot version from version module
- **Bot ID** - Discord user ID for identification
- **Guild/User Counts** - Current server and user statistics
- **Command Prefix** - Active command prefix

## Development Workflow

### Local Development

```bash
# Start bot with full initialization
uv run tux start

# Debug mode for verbose logging
uv run tux start --debug

# Check bot status and connections
uv run tux status
```

### Testing Bot Components

```python
import asyncio
from tux.core.bot import Tux

async def test_bot_initialization():
    """Test bot initialization without connecting to Discord."""
    bot = Tux(command_prefix="!")

    # Test setup task creation
    assert bot.setup_task is not None

    # Test database coordinator access
    db = bot.db
    assert db is not None

    # Test emoji manager
    assert bot.emoji_manager is not None

    print("✅ Bot initialization tests passed")
```

### Debugging Startup Issues

**Common Startup Problems:**

```bash
# Database connection failures
❌ "Database setup failed" → uv run docker up
❌ "Connection pool exhausted" → Check database configuration

# Cog loading failures
❌ "Cog setup failed" → Check cog dependencies and imports
❌ "Circular import" → Review import structure in extensions

# Discord connection issues
❌ "Login failed" → Verify BOT_TOKEN in .env
❌ "Privileged intents" → Enable required intents in Discord Developer Portal
```

**Debug Logging:**

```bash
# Enable detailed startup logging
LOG_LEVEL=DEBUG uv run tux start

# Check setup task progress
tail -f logs/tux.log | grep -E "(setup|Setup|database|Database)"
```

## Best Practices

### Bot Architecture

1. **Separation of Concerns** - Bot handles Discord integration, services handle business logic
2. **Lazy Initialization** - Expensive operations deferred until needed
3. **Resource Management** - Proper cleanup in shutdown sequences
4. **Error Isolation** - Component failures don't crash entire bot

### Performance Optimization

1. **Connection Pooling** - Efficient database and HTTP connection reuse
2. **Caching Strategy** - Prefix and user data cached for performance
3. **Background Processing** - Long-running tasks handled asynchronously
4. **Memory Management** - Proper cleanup prevents memory leaks

### Monitoring & Observability

1. **Structured Logging** - Consistent log formats with context
2. **Sentry Integration** - Error tracking with detailed context
3. **Performance Metrics** - Startup time, cache hit rates, connection counts
4. **Health Checks** - Regular validation of critical components

### Development Practices

1. **Configuration Validation** - Critical settings checked before startup
2. **Graceful Degradation** - Bot functional even with some service failures
3. **Testing Coverage** - Unit tests for core functionality, integration tests for services
4. **Documentation** - Inline docstrings and comprehensive API documentation

## Troubleshooting

### Startup Failures

**Database Issues:**

```bash
# Check database container status
uv run docker ps | grep postgres

# Test database connectivity
uv run tux db health

# Reset database if corrupted
uv run tux db reset
```

**Configuration Problems:**

```bash
# Validate configuration files
uv run tux config validate

# Check environment variables
env | grep -E "(BOT_TOKEN|DATABASE|DISCORD)"
```

**Cog Loading Issues:**

```bash
# Check for import errors
python -c "import tux.modules.moderation.ban"

# Verify cog file syntax
python -m py_compile src/tux/modules/moderation/ban.py

# Check cog priorities and dependencies
grep -r "COG_PRIORITIES" src/tux/shared/constants.py
```

### Runtime Issues

**Memory Leaks:**

```bash
# Monitor task count
uv run tux status

# Check for hanging tasks
ps aux | grep -E "(python|tux)" | head -10
```

**Performance Problems:**

```bash
# Check database connection pool
uv run tux db status

# Monitor cache hit rates
curl http://localhost:8000/metrics  # If metrics endpoint enabled
```

**Connection Issues:**

```bash
# Test Discord connectivity
uv run tux ping

# Check WebSocket status
uv run tux ws-status
```

## Resources

- **Source Code**: `src/tux/core/bot.py`
- **Setup Orchestrator**: `src/tux/core/setup/orchestrator.py`
- **Database Coordinator**: `src/tux/database/controllers/__init__.py`
- **Sentry Integration**: See sentry documentation
- **Discord.py Bot**: <https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#bot>
- **Task Monitor**: `src/tux/core/task_monitor.py`
