---
title: Cog System
description: Tux's modular cog architecture with priority-based loading, database integration, and automatic command handling.
---

# Cog System

Tux implements a sophisticated cog (extension) system that provides modular architecture, automatic command handling, priority-based loading, and comprehensive telemetry. The system consists of two main components: `BaseCog` for individual cog functionality and `CogLoader` for extension management.

## Overview

**Cogs** are Discord.py extensions that encapsulate related functionality (commands, event handlers, background tasks). Tux's cog system enhances discord.py's extension pattern with:

- **Database Integration**: Automatic database access via `self.db`
- **Configuration Access**: Convenient config retrieval via `self.get_config()`
- **Automatic Usage Generation**: Command usage strings from function signatures
- **Priority-Based Loading**: Ensures dependency order during startup
- **Graceful Error Handling**: Configuration errors don't crash the bot
- **Performance Monitoring**: Load time tracking and telemetry
- **Sentry Integration**: Comprehensive error reporting and tracing

## BaseCog Class

All Tux cogs inherit from `BaseCog`, which provides common functionality and integration points.

### Database Access

```python
from tux.core.base_cog import BaseCog

class MyCog(BaseCog):
    async def get_user_data(self, user_id: int):
        # Access database controllers directly
        user = await self.db.users.get_user(user_id)

        # Or use specific controller methods
        profile = await self.db.guild_config.get_guild_config(user_id)
        return user, profile
```

**Available Database Controllers:**

- `self.db.users` - User management
- `self.db.guild_config` - Guild settings
- `self.db.cases` - Moderation cases
- `self.db.levels` - User leveling system
- `self.db.permissions` - Permission management
- And more...

### Configuration Access

```python
class MyCog(BaseCog):
    async def setup_feature(self):
        # Get nested configuration values
        api_key = self.get_config("EXTERNAL_API.KEY")
        timeout = self.get_config("EXTERNAL_API.TIMEOUT", 30)

        # Access bot info
        bot_name = self.get_config("BOT_INFO.BOT_NAME")
        return api_key, timeout, bot_name
```

**Configuration Features:**

- **Dot notation support**: `"BOT_INFO.BOT_NAME"`
- **Default values**: Graceful fallback when keys don't exist
- **Error logging**: Issues logged but don't crash the cog

### Automatic Usage Generation

Tux automatically generates command usage strings from function signatures:

```python
class ModerationCog(BaseCog):
    @commands.hybrid_command(name="ban")
    async def ban_user(self, ctx, member: discord.Member, reason: str = None, days: int = 0):
        """Ban a user from the server."""
        # Command usage automatically becomes:
        # ban <member: Member> [reason: str] [days: int]
        pass

    @commands.hybrid_command(name="timeout")
    async def timeout_user(self, ctx, user: discord.User, duration: str, *, reason: str = None):
        """Timeout a user."""
        # Usage: timeout <user: User> <duration: str> [reason: str]
        pass
```

**Usage String Format:**

- `<required_param: Type>` - Required parameters
- `[optional_param: Type]` - Optional parameters
- `*args` and `**kwargs` handled appropriately

### Bot Integration Methods

```python
class UtilityCog(BaseCog):
    async def check_permissions(self, ctx):
        # Get bot latency
        latency = self.get_bot_latency()  # Returns float in seconds

        # Get cached user object
        user = self.get_bot_user(user_id)  # Returns discord.User or None

        # Get cached emoji
        emoji = self.get_bot_emoji(emoji_id)  # Returns discord.Emoji or None

        return latency, user, emoji
```

### Graceful Configuration Handling

```python
class ExternalServiceCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        # Check for required configuration
        if self.unload_if_missing_config(
            not self.get_config("EXTERNAL_API.KEY"),
            "EXTERNAL_API.KEY"
        ):
            return  # Early exit - cog won't be loaded

        # Safe to initialize external service
        self.api_client = ExternalAPIClient(self.get_config("EXTERNAL_API.KEY"))
```

**Configuration Skipping:**

- Logs clear warning messages
- Prevents partial initialization
- Allows bot to start with reduced functionality
- Doesn't crash other cogs

## CogLoader System

The `CogLoader` manages the discovery, validation, and loading of all bot cogs with advanced features.

### Priority-Based Loading

Tux loads cogs in priority order to ensure dependencies are met:

```python
# Loading order (highest to lowest priority)
COG_PRIORITIES = {
    "services": 90,    # Error handlers, core services
    "config": 85,      # Configuration management
    "admin": 80,       # Administrative commands
    "levels": 70,      # User leveling system
    "moderation": 60,  # Moderation commands
    "snippets": 50,    # Code snippet management
    "guild": 40,       # Guild management
    "utility": 30,     # Utility commands
    "info": 20,        # Information commands
    "fun": 10,         # Fun/Entertainment commands
    "tools": 5,        # External tool integrations
    "plugins": 1,      # User extensions (lowest priority)
}
```

**Loading Strategy:**

1. **Sequential by priority groups**: High-priority cogs load first
2. **Concurrent within groups**: Cogs in same priority load in parallel
3. **Dependency resolution**: Handlers load before commands, services before modules

### Directory Structure

Tux organizes cogs in a hierarchical directory structure:

```text
src/tux/
├── services/handlers/     # Highest priority - error handlers, events
├── modules/               # Normal priority - bot commands
│   ├── admin/            # Administrative commands
│   ├── moderation/       # Moderation commands
│   ├── utility/          # Utility commands
│   ├── info/             # Information commands
│   └── fun/              # Fun commands
└── plugins/              # Lowest priority - user extensions
```

### Cog Discovery & Validation

The loader automatically discovers and validates cogs:

```python
# Automatic discovery criteria
async def is_cog_eligible(filepath: Path) -> bool:
    # Must be Python file (.py extension)
    # Must not start with underscore (private)
    # Must not be in ignore list
    # Must contain async setup(bot) function (AST analysis)
    pass
```

**Validation Features:**

- **AST Analysis**: Parses Python files to detect valid extensions
- **Ignore Lists**: Skip cogs via configuration
- **Duplicate Prevention**: Avoids loading same module twice
- **Error Recovery**: Continues loading other cogs if one fails

### Performance Monitoring

```python
# Automatic timing and telemetry
class CogLoader:
    load_times: dict[str, float]  # Track load times per cog

    async def _load_single_cog(self, path: Path):
        start_time = time.perf_counter()
        # ... load cog ...
        load_time = time.perf_counter() - start_time
        self.load_times[module] = load_time
        # Log warnings for slow-loading cogs (>1s)
```

**Performance Features:**

- **Load Time Tracking**: Individual cog timing
- **Slow Cog Detection**: Warns about cogs taking >1 second
- **Sentry Integration**: Performance data in error reports
- **Concurrent Loading**: Parallel loading within priority groups

### Error Handling & Recovery

```python
# Graceful error handling
try:
    await self.bot.load_extension(module)
except TuxConfigurationError:
    # Log warning, skip cog, continue loading others
    self._handle_configuration_skip(path, error)
except Exception as e:
    # Capture to Sentry, raise TuxCogLoadError
    capture_span_exception(e)
    raise TuxCogLoadError(f"Failed to load {path}") from e
```

**Error Handling Strategies:**

- **Configuration Errors**: Log warnings, skip gracefully
- **Real Errors**: Capture to Sentry, fail fast
- **Partial Loading**: Bot starts with reduced functionality
- **Dependency Management**: Priority loading prevents issues

### Telemetry & Monitoring

```python
# Comprehensive telemetry
@span("cog.load_single")
async def _load_single_cog(self, path: Path):
    set_span_attributes({
        "cog.name": path.stem,
        "cog.module": module,
        "cog.status": "loaded",  # or "failed" or "skipped"
        "load_time_ms": load_time * 1000,
    })
    # Additional telemetry for priority groups, success rates, etc.
```

**Telemetry Data:**

- **Load Times**: Individual and group timing
- **Success Rates**: Loaded vs failed cogs
- **Priority Distribution**: Cog count by priority level
- **Error Context**: Detailed error information for debugging

## Cog Development Patterns

### Basic Cog Structure

```python
from tux.core.base_cog import BaseCog
from discord.ext import commands

class MyFeatureCog(BaseCog):
    """Description of what this cog does."""

    def __init__(self, bot):
        super().__init__(bot)
        # Check configuration requirements
        if self.unload_if_missing_config(
            not self.get_config("MY_FEATURE.API_KEY"),
            "MY_FEATURE.API_KEY"
        ):
            return

        # Initialize services
        self.api_client = MyAPIClient(self.get_config("MY_FEATURE.API_KEY"))

    @commands.hybrid_command(name="mycommand")
    async def my_command(self, ctx, param: str):
        """Command description."""
        # Use database access
        data = await self.db.my_table.get_data(ctx.author.id)

        # Use bot integration
        latency = self.get_bot_latency()

        await ctx.send(f"Response with data: {data}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event listener."""
        if message.author.bot:
            return
        # Handle message events

async def setup(bot):
    """Required setup function for discord.py extensions."""
    await bot.add_cog(MyFeatureCog(bot))
```

### Event Handling Cogs

```python
class EventHandlerCog(BaseCog):
    """High-priority event handlers."""

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global command error handler."""
        # Handle different error types
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission for this command.")
        else:
            # Log and handle other errors
            logger.error(f"Command error: {error}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot startup handler."""
        logger.info(f"Bot ready as {self.bot.user}")
```

### Background Task Cogs

```python
from discord.ext import tasks

class BackgroundTaskCog(BaseCog):
    """Cogs with recurring background tasks."""

    def __init__(self, bot):
        super().__init__(bot)
        self.background_task.start()

    def cog_unload(self):
        """Called when cog is unloaded."""
        self.background_task.cancel()

    @tasks.loop(hours=1)
    async def background_task(self):
        """Hourly background task."""
        try:
            # Perform maintenance tasks
            await self.cleanup_old_data()
        except Exception as e:
            logger.error(f"Background task failed: {e}")
```

## Configuration Management

### Cog Ignore Lists

```python
# In configuration (config.toml)
[cog_loader]
ignore_list = ["experimental_feature", "broken_cog"]
```

### Priority Customization

```python
# Priorities can be customized in constants.py
COG_PRIORITIES: dict[str, int] = {
    "custom_category": 95,  # Add custom priorities
    "services": 90,
    # ... existing priorities
}
```

## Debugging & Troubleshooting

### Common Issues

**Cog Not Loading:**

```bash
# Check if cog file exists and has setup function
find src/tux -name "*.py" -exec grep -l "async def setup" {} \;

# Check cog loader logs for errors
# Look for configuration warnings
```

**Configuration Errors:**

```bash
# Check environment variables
uv run tux config check

# Verify configuration structure
uv run tux config validate
```

## Best Practices

### Cog Design

1. **Single Responsibility**: Each cog should handle one feature area
2. **Configuration Checks**: Use `unload_if_missing_config()` for required settings
3. **Error Handling**: Implement proper error handling for all operations
4. **Resource Cleanup**: Implement `cog_unload()` for cleanup tasks
5. **Documentation**: Include docstrings for all commands and methods

### Loading Strategy

1. **Priority Awareness**: Place cogs in appropriate priority directories
2. **Dependency Management**: Ensure dependencies load before dependents
3. **Configuration Validation**: Fail early on missing required config
4. **Error Isolation**: One cog's failure shouldn't prevent others from loading

### Performance

1. **Lazy Loading**: Don't initialize expensive resources in `__init__`
2. **Background Tasks**: Use `discord.ext.tasks` for recurring operations
3. **Database Efficiency**: Use appropriate database methods and caching
4. **Memory Management**: Clean up resources in `cog_unload()`

## Resources

- **BaseCog Source**: `src/tux/core/base_cog.py`
- **CogLoader Source**: `src/tux/core/cog_loader.py`
- **Configuration Constants**: `src/tux/shared/constants.py`
- **Discord.py Extensions**: <https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html>
- **Sentry Tracing**: See sentry integration documentation
