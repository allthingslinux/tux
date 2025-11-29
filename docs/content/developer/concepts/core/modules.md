---
title: Modules
description: Built-in feature modules providing core bot functionality including moderation, configuration, and utility commands.
tags:
  - developer-guide
  - concepts
  - core
  - modules
---

# Modules

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Modules are Tux's built-in feature packages that provide core bot functionality. Each module is a self-contained package with specific commands and features.

## Overview

Modules are organized by functionality and loaded automatically when the bot starts. They provide the core features users expect from Tux:

- **Moderation** - Ban, kick, timeout, and case management
- **Configuration** - Server settings, permissions, and channel configuration
- **Utility** - Information commands, user lookup, and server stats
- **Features** - Leveling, XP tracking, and other gameplay features

## Module Structure

Modules are located in `src/tux/modules/` and organized by category:

```text
src/tux/modules/
├── moderation/     # Moderation commands and case management
├── config/         # Server configuration commands
├── utility/        # Utility and information commands
└── features/       # Gameplay features like levels and XP
```

Each module is a Python package containing:

- **Cog Classes** - Command implementations inheriting from `BaseCog`
- **Commands** - Discord commands and interactions
- **Services** - Business logic and database operations
- **UI Components** - Views, modals, and interactive components

## Module Loading

Modules are loaded automatically by the Cog Loader during bot startup. They load after handlers but before plugins, ensuring core functionality is available before custom extensions.

**Loading Priority:**

1. Handlers (event handlers, error handlers)
2. Modules (built-in features)
3. Plugins (custom extensions)

This order ensures dependencies are available when modules need them.

## Creating Modules

While modules are built-in, understanding their structure helps when creating plugins or contributing to Tux.

### Module Package Structure

A module package typically contains:

```python
# src/tux/modules/example/__init__.py
from tux.core.base_cog import BaseCog
from tux.core.bot import Tux

class ExampleModule(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.command()
    async def example_command(self, ctx):
        """Example command."""
        await ctx.send("Example!")

async def setup(bot: Tux) -> None:
    await bot.add_cog(ExampleModule(bot))
```

### Module Best Practices

**Use BaseCog:**

All modules inherit from `BaseCog` for database access, configuration, and helper methods.

**Organize by Feature:**

Group related commands together. Large modules can be split into multiple cogs within the same package.

**Use Services:**

Separate business logic into service classes. Keep cogs focused on command handling and user interaction.

**Follow Naming Conventions:**

Use clear, descriptive names. Follow Python package naming conventions (lowercase, underscores).

## Available Modules

### Moderation Module

Provides moderation commands and case management:

- Ban, kick, timeout commands
- Case creation and tracking
- Moderation history
- Appeal system

### Configuration Module

Server configuration and settings:

- Permission rank management
- Role assignments
- Command permissions
- Channel configuration
- Log channel setup

### Utility Module

Utility and information commands:

- User information
- Server statistics
- Bot information
- Help commands

### Features Module

Gameplay and engagement features:

- Leveling system
- XP tracking
- User progression
- Rewards and achievements

## Module Development

When developing modules:

### Use Dependency Injection

Access services through the bot instance:

```python
class MyModule(BaseCog):
    @commands.command()
    async def use_service(self, ctx):
        # Access database
        user = await self.db.users.get_by_id(ctx.author.id)
        
        # Access other services
        sentry = self.bot.sentry_manager
```

### Handle Errors Gracefully

Use try/except blocks and provide user-friendly error messages:

```python
@commands.command()
async def risky_command(self, ctx):
    try:
        await perform_operation()
    except Exception as e:
        logger.error("Command failed", error=str(e))
        await ctx.send("Something went wrong. Please try again.")
```

### Use Permission Checks

Protect commands with permission decorators:

```python
from tux.core.checks import requires_command_permission

@commands.command()
@requires_command_permission()
async def admin_command(self, ctx):
    """Command requiring permissions."""
    pass
```

## Resources

- **Module Directory**: `src/tux/modules/`
- **Base Cog**: See `base-cog.md` for available features
- **Cog Loader**: See `cog-loader.md` for loading details
- **Permission System**: See `permission-system.md` for access control
