---
title: Base Cog
description: Enhanced base cog class providing database access, configuration helpers, and automatic usage generation for Tux Discord bot extensions.
tags:
  - developer-guide
  - concepts
  - core
  - cogs
---

# Base Cog

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The `BaseCog` class is the foundation for all Tux cogs. It extends discord.py's `commands.Cog` with Tux-specific features that make building commands easier and more consistent.

## Overview

When you create a cog in Tux, inherit from `BaseCog` instead of `commands.Cog`. This gives you:

- **Database Access** - Direct access to all database controllers via `self.db`
- **Configuration Helpers** - Easy config retrieval with dot notation
- **Automatic Usage Generation** - Usage strings generated from function signatures
- **Graceful Error Handling** - Automatic cog unloading when configuration is missing
- **Helper Methods** - Common operations like latency checks and user lookups

## Using BaseCog

### Basic Usage

All Tux cogs should inherit from `BaseCog`:

```python
from tux.core.base_cog import BaseCog
from tux.core.bot import Tux

class MyCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)  # Enables all BaseCog features

    @commands.command()
    async def my_command(self, ctx):
        # Your command code here
        pass
```

Calling `super().__init__(bot)` sets up all BaseCog features automatically. The bot instance is stored for accessing services.

## Database Access

### Using the Database Property

Access the database through `self.db`, which provides access to all database controllers:

```python
class MyCog(BaseCog):
    @commands.command()
    async def get_user(self, ctx, user_id: int):
        # Access user controller
        user = await self.db.users.get_by_id(user_id)
        
        # Access guild config
        config = await self.db.guild_config.get_by_id(ctx.guild.id)
        
        # Access cases
        cases = await self.db.cases.find_all(filters={"user_id": user_id})
```

**Available Controllers:**

- `self.db.users` - User management and profiles
- `self.db.guild_config` - Guild-specific settings
- `self.db.cases` - Moderation case tracking
- `self.db.levels` - User leveling system
- `self.db.permissions` - Permission management
- `self.db.snippets` - Code snippet storage

The database coordinator is automatically available—you don't need to set it up yourself.

## Configuration Access

### Getting Configuration Values

Use `get_config()` to retrieve configuration values with dot notation support:

```python
class MyCog(BaseCog):
    @commands.command()
    async def check_setting(self, ctx):
        # Get nested config value
        bot_name = self.get_config("BOT_INFO.BOT_NAME", "Tux")
        
        # Get config with default
        timeout = self.get_config("MY_COG.TIMEOUT", 30)
```

**Features:**

- Supports nested keys like `"BOT_INFO.BOT_NAME"`
- Returns default values when keys are missing
- Logs errors but doesn't raise exceptions
- Works with environment variables and config files

If a configuration key is missing, the default value is returned and a warning is logged. This prevents crashes from missing configuration.

## Automatic Usage Generation

BaseCog automatically generates usage strings for commands that don't have explicit usage defined. This happens when the cog is initialized.

**How It Works:**

1. Inspects command callback signatures
2. Detects parameter types and names
3. Generates usage strings like `ban <member: Member> [reason: str]`
4. Handles FlagConverter parameters for advanced syntax
5. Falls back gracefully if generation fails

You don't need to do anything—usage strings are generated automatically. If you want custom usage, define it explicitly in the command decorator.

## Configuration Validation

### Graceful Cog Unloading

If your cog requires specific configuration, use `unload_if_missing_config()` to check and unload gracefully:

```python
class MyCog(BaseCog):
    async def cog_load(self):
        # Check if required config exists
        if self.unload_if_missing_config(
            not self.get_config("MY_COG.REQUIRED_SETTING"),
            "MY_COG.REQUIRED_SETTING"
        ):
            return  # Cog will be unloaded
        
        # Continue with normal initialization
        logger.info("MyCog loaded successfully")
```

**Behavior:**

- Returns `True` if config is missing (you should return early)
- Logs a warning about missing configuration
- Schedules background task to unload the cog
- Prevents runtime errors from missing config

This pattern lets cogs handle missing configuration gracefully instead of crashing.

## Helper Methods

BaseCog provides helper methods for common operations:

### Bot Latency

Check bot latency:

```python
latency = self.bot.latency
```

### User Lookup

Look up users by ID:

```python
user = await self.bot.get_user(user_id)
```

### Emoji Access

Access emoji manager:

```python
emoji = self.bot.emoji_manager.get("check")
```

These helpers are available through the bot instance stored in `self.bot`.

## Best Practices

### Always Inherit from BaseCog

Use `BaseCog` for all Tux cogs. It provides essential features you'll need, and using it consistently makes code easier to understand and maintain.

### Use Database Controllers

Access the database through `self.db` controllers. Don't access the database service directly—controllers provide better type safety and consistent APIs.

### Handle Missing Configuration

Use `unload_if_missing_config()` for optional cogs that require configuration. This provides better user experience than crashing or silently failing.

### Let Usage Generate Automatically

Don't manually define usage strings unless you need custom formatting. BaseCog generates accurate usage strings from your function signatures automatically.

## Troubleshooting

### Database Access Not Working

If `self.db` doesn't work:

1. Verify you're inheriting from `BaseCog`
2. Check that `super().__init__(bot)` is called
3. Ensure the database is initialized during bot setup

### Configuration Not Found

If configuration values aren't found:

1. Check the key name matches your config structure
2. Verify the configuration is loaded
3. Use defaults for optional configuration

### Usage Not Generated

If usage strings aren't generated:

1. Check command signatures are properly typed
2. Verify commands are registered correctly
3. Define usage explicitly if automatic generation fails

## Resources

- **Source Code**: `src/tux/core/base_cog.py`
- **Database Controllers**: See database documentation for available controllers
- **Configuration System**: See configuration documentation for setup
