---
title: Plugin System
description: Custom plugin system for self-hosters to extend Tux with their own commands and features.
tags:
  - developer-guide
  - concepts
  - core
  - plugins
---

# Plugin System

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The plugin system lets you extend Tux with custom commands and features. Place your custom modules in the `plugins` directory, and they're automatically discovered and loaded when the bot starts.

## Overview

Plugins are custom extensions you create for your Tux instance. They work exactly like built-in modules but are loaded separately, making it easy to add custom functionality without modifying core code.

**Key Features:**

- **Automatic Discovery** - Plugins are found and loaded automatically
- **Same Capabilities** - Full access to database, configuration, and bot features
- **Hot Reload Support** - Changes reload without restarting the bot
- **Low Priority Loading** - Loaded after handlers and modules

## Creating a Plugin

### Basic Structure

Create a Python file in `src/tux/plugins/` with a cog class and setup function:

```python
from discord.ext import commands
from tux.core.base_cog import BaseCog
from tux.core.bot import Tux

class MyCustomPlugin(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.command(name="hello")
    async def hello_command(self, ctx: commands.Context) -> None:
        """Say hello!"""
        await ctx.send("Hello from my custom plugin!")

async def setup(bot: Tux) -> None:
    await bot.add_cog(MyCustomPlugin(bot))
```

### Required Components

**Cog Class:**

Your plugin must inherit from `BaseCog` to get database access, configuration helpers, and other Tux features. The cog class contains your commands and event handlers.

**Setup Function:**

Every plugin needs an `async def setup(bot: Tux)` function. This is called when the plugin is loaded. Use it to add your cog to the bot.

### File Naming

Use Python naming conventions for your plugin files:

- Use lowercase with underscores: `my_custom_plugin.py`
- Don't start with underscores (those files are ignored)
- Use `.py` extension

## Plugin Capabilities

Plugins have the same capabilities as built-in modules:

### Database Access

Access the database through `self.db`:

```python
class MyPlugin(BaseCog):
    @commands.command()
    async def get_user(self, ctx, user_id: int):
        user = await self.db.users.get_by_id(user_id)
        await ctx.send(f"User: {user.name}")
```

### Configuration Access

Read configuration values:

```python
class MyPlugin(BaseCog):
    @commands.command()
    async def check_config(self, ctx):
        bot_name = self.get_config("BOT_INFO.BOT_NAME", "Tux")
        await ctx.send(f"Bot name: {bot_name}")
```

### Permission System

Use the permission system for access control:

```python
from tux.core.checks import requires_command_permission

class MyPlugin(BaseCog):
    @commands.command()
    @requires_command_permission()
    async def admin_command(self, ctx):
        """Command that requires permissions."""
        await ctx.send("Admin only!")
```

### Event Listeners

Listen to Discord events:

```python
class MyPlugin(BaseCog):
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.send("Welcome to the server!")
```

## Loading Order

Plugins are loaded in this order:

1. **Handlers** - Event handlers and error handlers (highest priority)
2. **Modules** - Built-in bot functionality
3. **Plugins** - Your custom plugins (lowest priority)

This ensures handlers are ready before commands, and built-in modules load before custom plugins.

## Best Practices

### Follow Naming Conventions

Use clear, descriptive names for your plugins. Follow Python naming conventions and avoid conflicts with built-in modules.

### Use BaseCog

Always inherit from `BaseCog` instead of `commands.Cog`. This gives you database access, configuration helpers, and automatic usage generation.

### Handle Errors Gracefully

Use try/except blocks for operations that might fail. Log errors appropriately and provide user-friendly error messages.

### Document Your Commands

Include docstrings for your commands. They appear in help commands and make your plugin easier to use.

### Test Your Plugin

Test your plugin thoroughly before deploying. Use the hot reload system to test changes quickly during development.

## Troubleshooting

### Plugin Not Loading

If your plugin doesn't load:

1. Check the file is in `src/tux/plugins/`
2. Verify it has a `setup()` function
3. Check for syntax errors in logs
4. Ensure the cog class inherits from `BaseCog`

### Commands Not Working

If commands don't work:

1. Verify the `@commands.command()` decorator is applied
2. Check command names don't conflict with built-in commands
3. Ensure permissions are configured if using `@requires_command_permission()`

### Database Access Issues

If database access fails:

1. Verify the database is initialized
2. Check you're using `self.db` from `BaseCog`
3. Ensure database migrations are up to date

## Resources

- **Plugin Directory**: `src/tux/plugins/`
- **Example Plugin**: See `src/tux/plugins/README.md` for examples
- **Base Cog**: See `base-cog.md` for available features
- **Hot Reload**: See lifecycle documentation for reload system
