---
title: Lifecycle Orchestration
description: Complete bot lifecycle orchestration from startup through shutdown, coordinating database, permissions, cogs, and monitoring systems.
---

# Lifecycle Orchestration

The bot orchestration system (`src/tux/core/setup/`) provides comprehensive lifecycle management for Tux, coordinating the complex startup and shutdown sequences that integrate database connections, permission systems, cog loading, caching, and monitoring.

This system ensures reliable initialization with proper error handling and graceful degradation.

## Architecture Overview

The orchestration system follows a layered architecture with clear separation of concerns:

```text
TuxApp (app.py)
├── Application Lifecycle (startup/shutdown/signal handling)
└── Discord Connection Management

Tux (bot.py)
├── Discord.py Integration
├── Service Coordination (DB, Sentry, Tasks, Emoji)
└── Lifecycle Hooks (setup_hook, on_disconnect, shutdown)

BotSetupOrchestrator (orchestrator.py)
├── Setup Phase Coordination
├── Error Handling & Recovery
└── Progress Tracking via Sentry

Setup Services (setup/*.py)
├── DatabaseSetupService - Connection & Migrations
├── PermissionSetupService - Authorization System
├── CogSetupService - Extension Loading
└── PrefixManager - Command Prefix Caching
```

## Application Layer (TuxApp)

### Startup Sequence

The `TuxApp` class orchestrates the complete bot lifecycle:

```python
class TuxApp:
    """Application wrapper managing bot lifecycle."""

    async def start(self) -> None:
        """Complete startup with error handling."""
        # 1. Sentry initialization
        SentryManager.setup()

        # 2. Signal handler registration
        self.setup_signals(loop)

        # 3. Configuration validation
        self._validate_config()

        # 4. Owner permission resolution
        owner_ids = self._resolve_owner_ids()

        # 5. Bot instance creation
        bot = self._create_bot_instance(owner_ids)

        # 6. Internal setup wait
        await self._await_bot_setup()

        # 7. Discord connection
        await self._login_and_connect()
```

**Startup Phases:**

1. **Sentry Setup** - Error tracking ready before any failures
2. **Signal Handling** - Graceful shutdown preparation
3. **Configuration** - Critical validation before expensive operations
4. **Bot Creation** - Discord.py bot instance with all configurations
5. **Setup Wait** - Ensure internal bot setup completes
6. **Connection** - Discord gateway/WebSocket connection

### Signal Handling & Shutdown

```python
def setup_signals(self, loop: asyncio.AbstractEventLoop) -> None:
    """Register SIGTERM/SIGINT handlers for graceful shutdown."""

def _handle_signal_shutdown(self, signum: int) -> None:
    """Process shutdown signals with Sentry reporting."""
    SentryManager.report_signal(signum, None)
    # Cancel all tasks
    # Trigger shutdown sequence
```

**Shutdown Sequence:**

1. **Signal Processing** - Capture and report shutdown signals
2. **Task Cancellation** - Stop all running background tasks
3. **Bot Shutdown** - Close Discord connections and cleanup
4. **Resource Cleanup** - Database, HTTP client, Sentry flush

## Bot Core Layer (Tux)

### Initialization Architecture

The `Tux` bot class uses lazy initialization to prevent blocking:

```python
def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize with lazy async setup."""
    super().__init__(*args, **kwargs)

    # Core services
    self.task_monitor = TaskMonitor(self)
    self.db_service = DatabaseService()
    self.sentry_manager = SentryManager()
    self.emoji_manager = EmojiManager(self)

    # Schedule setup task (non-blocking)
    asyncio.get_event_loop().call_soon(self._create_setup_task)
```

**Key Design Patterns:**

- **Lazy Setup** - Async initialization scheduled via `call_soon`
- **Service Injection** - All components initialized but not connected
- **Error Isolation** - Component failures don't crash entire bot
- **State Tracking** - Multiple flags prevent duplicate operations

### Setup Orchestration

```python
def _create_setup_task(self) -> None:
    """Create setup task in proper event loop context."""
    if self.setup_task is None:
        self.setup_task = asyncio.create_task(self.setup(), name="bot_setup")

async def setup(self) -> None:
    """Comprehensive bot setup with error handling."""
    with start_span("bot.setup", "Bot setup process") as span:
        # Lazy import to avoid circular dependencies
        from tux.core.setup.orchestrator import BotSetupOrchestrator

        orchestrator = BotSetupOrchestrator(self)
        await orchestrator.setup(span)
```

### Lifecycle Hooks

```python
async def setup_hook(self) -> None:
    """Discord.py hook called before connection."""
    # Initialize emoji manager
    await self.emoji_manager.init()

    # Check setup task completion
    if self.setup_task.done():
        if self.setup_task.exception():
            self.setup_complete = False
        else:
            self.setup_complete = True

    # Schedule post-ready tasks
    self._startup_task = self.loop.create_task(self._post_ready_startup())

async def _post_ready_startup(self) -> None:
    """Execute tasks after Discord connection."""
    await self.wait_until_ready()  # Wait for READY event
    await self._wait_for_setup()   # Wait for internal setup

    # Record operational start time
    self.start_time = discord.utils.utcnow().timestamp()

    # Display startup banner
    await self._log_startup_banner()

    # Enable Sentry instrumentation
    instrument_bot_commands(self)

    # Record bot statistics
    self._record_bot_stats()
```

## Setup Orchestration Layer

### BotSetupOrchestrator

The orchestrator coordinates all setup services with standardized error handling:

```python
class BotSetupOrchestrator:
    """Orchestrates setup using specialized services."""

    def __init__(self, bot: Tux) -> None:
        """Initialize with lazy imports to avoid circular dependencies."""
        from .database_setup import DatabaseSetupService
        from .permission_setup import PermissionSetupService
        from .cog_setup import CogSetupService

        self.database_setup = DatabaseSetupService(bot.db_service)
        self.permission_setup = PermissionSetupService(bot, bot.db_service)
        self.cog_setup = CogSetupService(bot)

    async def setup(self, span: DummySpan) -> None:
        """Execute all setup steps with error handling."""
        # Database setup (critical - throws on failure)
        if not await self.database_setup.safe_setup():
            raise TuxDatabaseConnectionError("Database setup failed")

        # Permission system setup
        if not await self.permission_setup.safe_setup():
            raise RuntimeError("Permission system setup failed")

        # Prefix manager setup (with graceful fallback)
        await self._setup_prefix_manager(span)

        # Cog setup
        if not await self.cog_setup.safe_setup():
            raise RuntimeError("Cog setup failed")

        # Start monitoring
        self.bot.task_monitor.start()
```

**Setup Sequence:**

1. **Database** - Connection, migrations, schema validation (critical)
2. **Permissions** - Authorization system initialization (critical)
3. **Prefix Manager** - Command prefix caching (non-critical with fallback)
4. **Cogs** - Extension loading via CogLoader (critical)
5. **Monitoring** - Background task monitoring startup

### Base Setup Service Pattern

All setup services inherit from `BaseSetupService` for consistent behavior:

```python
class BaseSetupService(ABC):
    """Base class with standardized error handling."""

    async def safe_setup(self) -> bool:
        """Execute setup with tracing and error handling."""
        with start_span(f"bot.setup_{self.name}") as span:
            try:
                await self.setup()
                self.logger.info(f"✅ {self.name.title()} setup completed")
                span.set_tag(f"{self.name}.setup", "success")
                return True
            except Exception as e:
                self.logger.exception(f"❌ {self.name.title()} setup failed")
                span.set_tag(f"{self.name}.setup", "failed")
                capture_exception_safe(e)
                return False

class BotSetupService(BaseSetupService):
    """Base for services needing bot access."""
    def __init__(self, bot: Tux, name: str):
        super().__init__(name)
        self.bot = bot
```

**Standardized Features:**

- **Tracing** - All setup steps tracked with Sentry spans
- **Logging** - Consistent log format with emojis and status
- **Error Handling** - Exceptions captured but don't crash orchestrator
- **Status Reporting** - Success/failure tags for monitoring

## Setup Services

### Database Setup Service

Handles complete database initialization:

```python
class DatabaseSetupService(BaseSetupService):
    """Complete database setup and validation."""

    async def setup(self) -> None:
        """Set up database connection and schema."""
        # 1. Connect to database
        await self.db_service.connect(CONFIG.database_url)

        # 2. Create tables if needed
        await self._create_tables()

        # 3. Run migrations
        await self._upgrade_head_if_needed()

        # 4. Validate schema
        await self._validate_schema()
```

**Database Setup Steps:**

1. **Connection** - Establish database connection pool
2. **Tables** - Create tables from SQLModel metadata
3. **Migrations** - Run Alembic migrations to latest
4. **Validation** - Ensure schema matches model definitions

### Permission Setup Service

Initializes the authorization system:

```python
class PermissionSetupService(BotSetupService):
    """Permission system initialization."""

    async def setup(self) -> None:
        """Initialize command authorization."""
        db_coordinator = DatabaseCoordinator(self.db_service)
        init_permission_system(self.bot, db_coordinator)
```

**Permission Components:**

- **Database Integration** - Permission storage and retrieval
- **Command Authorization** - Before-invoke hooks for all commands
- **Role-Based Access** - Guild role permission mapping
- **Owner Overrides** - Bot owner always has full access

### Cog Setup Service

Manages extension loading:

```python
class CogSetupService(BotSetupService):
    """Cog loading and plugin setup."""

    async def setup(self) -> None:
        """Load all cogs and plugins."""
        await self._load_jishaku()      # Development tools
        await self._load_cogs()         # Bot commands/extensions
        await self._load_hot_reload()   # Development hot reload
```

**Cog Loading Process:**

1. **Jishaku** - Development/debugging extension (optional)
2. **Core Cogs** - All bot commands via CogLoader priority system
3. **Hot Reload** - Development code reloading (optional)

### Prefix Manager Setup

Handles command prefix caching:

```python
async def _setup_prefix_manager(self, span: DummySpan) -> None:
    """Set up prefix manager with graceful fallback."""
    try:
        self.bot.prefix_manager = PrefixManager(self.bot)
        await self.bot.prefix_manager.load_all_prefixes()
        logger.info("✅ Prefix manager initialized")
    except Exception as e:
        logger.warning("⚠️  Bot will use default prefix for all guilds")
        self.bot.prefix_manager = None
```

**Prefix Management:**

- **Cache-First** - In-memory cache for sub-millisecond lookups
- **Lazy Loading** - Load prefixes on first access per guild
- **Graceful Fallback** - Use default prefix if cache fails
- **Event Updates** - Cache updated on prefix changes

## Error Handling & Recovery

### Critical vs Non-Critical Failures

The orchestration system distinguishes between critical and non-critical failures:

```python
# Critical failures - bot cannot start
if not await self.database_setup.safe_setup():
    raise TuxDatabaseConnectionError("Database setup failed")

if not await self.permission_setup.safe_setup():
    raise RuntimeError("Permission system setup failed")

if not await self.cog_setup.safe_setup():
    raise RuntimeError("Cog setup failed")

# Non-critical failures - graceful degradation
await self._setup_prefix_manager(span)  # Continues even if it fails
```

**Critical Components:** Database, Permissions, Cogs
**Non-Critical Components:** Prefix Manager, Emoji Manager, Hot Reload

### Error Recovery Strategies

**Database Failures:**

```bash
❌ "Database connection failed"
💡 To start the database, run: uv run docker up
```

**Permission Failures:**

```python
# Authorization system unavailable - commands may not work
logger.error("Permission system setup failed")
```

**Cog Loading Failures:**

```python
# Bot partially functional - some commands unavailable
logger.error("Cog setup failed")
```

## Performance Optimization

### Lazy Initialization

The system uses multiple levels of lazy initialization:

```python
# Level 1: Event loop ready
asyncio.get_event_loop().call_soon(self._create_setup_task)

# Level 2: After bot creation
self.setup_task = asyncio.create_task(self.setup())

# Level 3: After Discord connection
self._startup_task = self.loop.create_task(self._post_ready_startup())
```

**Performance Benefits:**

- **Fast Startup** - Bot becomes responsive quickly
- **Concurrent Setup** - Multiple services initialize in parallel
- **Resource Efficiency** - Only initialize when needed
- **Error Isolation** - Component failures don't block others

### Connection Pooling

All external connections use pooling for efficiency:

```python
# Database connection pool
await self.db_service.connect(CONFIG.database_url)

# HTTP client with connection pooling
await http_client.close()  # Graceful pool shutdown
```

### Caching Strategy

Critical data is cached for performance:

```python
# Prefix caching
self.bot.prefix_manager = PrefixManager(self.bot)
await self.bot.prefix_manager.load_all_prefixes()

# Emoji caching
await self.emoji_manager.init()
```

## Monitoring & Observability

### Sentry Integration

All orchestration steps are traced and monitored:

```python
# Setup phase tagging
set_setup_phase_tag(span, "database", "finished")
set_setup_phase_tag(span, "permissions", "finished")
set_setup_phase_tag(span, "cogs", "finished")

# Error reporting
capture_exception_safe(e)
capture_database_error(e, operation="connection")
```

### Task Monitoring

Background tasks are tracked and cleaned up:

```python
# Start monitoring after setup
self.bot.task_monitor.start()

# Cleanup during shutdown
await self.task_monitor.cleanup_tasks()
```

### Bot Statistics

Operational metrics are collected:

```python
def _record_bot_stats(self) -> None:
    """Record bot statistics for monitoring."""
    self.sentry_manager.set_context("bot_stats", {
        "guild_count": len(self.guilds),
        "user_count": len(self.users),
        "channel_count": sum(len(g.channels) for g in self.guilds),
        "uptime": discord.utils.utcnow().timestamp() - self.start_time,
    })
```

## Development Workflow

### Local Development

```bash
# Start with full orchestration
uv run tux start

# Debug mode with verbose logging
uv run tux start --debug

# Check orchestration status
uv run tux status
```

### Testing Orchestration

```python
import asyncio
from tux.core.app import TuxApp

async def test_orchestration():
    """Test complete startup and shutdown."""
    app = TuxApp()

    try:
        await app.start()
    except KeyboardInterrupt:
        pass
    finally:
        await app.shutdown()
```

### Debugging Setup Issues

**Common Problems:**

```bash
# Database connection issues
uv run tux db health

# Permission system failures
# Check database tables exist
uv run tux db status

# Cog loading failures
python -c "import tux.modules.moderation.ban"
python -m py_compile src/tux/modules/moderation/ban.py

# Configuration validation
uv run tux config validate
```

**Debug Logging:**

```bash
# Enable setup tracing
LOG_LEVEL=DEBUG uv run tux start 2>&1 | grep -E "(setup|Setup|orchestrator)"

# Check setup task progress
tail -f logs/tux.log | grep -E "(🔧|✅|❌|⚠️)"
```

## Best Practices

### Orchestration Design

1. **Separation of Concerns** - Each service handles one responsibility
2. **Error Containment** - Failures isolated to prevent cascade effects
3. **Graceful Degradation** - Bot functional even with partial failures
4. **Performance First** - Lazy loading and caching for speed
5. **Observability** - Complete tracing and monitoring coverage

### Setup Service Patterns

1. **Standardized Interface** - All services inherit from BaseSetupService
2. **Consistent Logging** - Uniform log format across all services
3. **Error Handling** - Exceptions captured but don't crash orchestrator
4. **Tracing Integration** - All operations tracked with Sentry spans

### Resource Management

1. **Connection Pooling** - Efficient reuse of database/HTTP connections
2. **Task Cleanup** - All background tasks properly cancelled on shutdown
3. **Memory Management** - Cache invalidation and cleanup
4. **Signal Handling** - Graceful shutdown on system signals

### Development Practices

1. **Lazy Imports** - Avoid circular dependencies in orchestrator
2. **Configuration Validation** - Critical settings checked early
3. **Health Checks** - Regular validation of critical components
4. **Documentation** - All setup steps and error conditions documented

## Troubleshooting

### Startup Failures

**Database Issues:**

```bash
# Check Docker containers
uv run docker ps | grep postgres

# Test connection
uv run tux db health

# Check migrations
uv run tux db status
```

**Permission System:**

```bash
# Verify database tables
uv run tux db status

# Check permission initialization logs
tail -f logs/tux.log | grep -i permission
```

**Cog Loading:**

```bash
# Test individual cog imports
python -c "from tux.modules.moderation import ban"

# Check CogLoader priority system
grep -r "COG_PRIORITIES" src/tux/shared/constants.py
```

### Runtime Issues

**Memory Leaks:**

```bash
# Monitor task count
uv run tux status

# Check for hanging connections
ps aux | grep -E "(python|tux)" | head -5
```

**Performance Issues:**

```bash
# Check cache hit rates
uv run tux status

# Monitor database connections
uv run tux db status
```

**Connection Issues:**

```bash
# Test Discord connectivity
uv run tux ping

# Check WebSocket status
uv run tux ws-status
```

## Resources

- **Application Layer**: `src/tux/core/app.py`
- **Bot Core**: `src/tux/core/bot.py`
- **Orchestrator**: `src/tux/core/setup/orchestrator.py`
- **Setup Services**: `src/tux/core/setup/`
- **Prefix Manager**: `src/tux/core/prefix_manager.py`
- **Database Service**: `src/tux/database/service.py`
- **Cog Loader**: `src/tux/core/cog_loader.py`
- **Task Monitor**: `src/tux/core/task_monitor.py`
