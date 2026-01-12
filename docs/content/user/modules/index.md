---
title: Modules
description: Complete documentation for all Tux command modules
tags:
  - user-guide
  - modules
  - commands
icon: lucide/command
---

# Modules

Tux organizes commands into modules, each providing a focused set of functionality for your Discord server. This section contains complete documentation for all available command modules, including detailed command references, usage examples, and configuration guides.

Whether you're looking for moderation tools, utility commands, fun features, or administrative controls, you'll find everything you need to make the most of Tux's capabilities.

## Available Modules

| Module | Description | Documentation |
|--------|-------------|---------------|
| **Moderation** | Comprehensive moderation tools for managing your Discord server | [Details](moderation/index.md) |
| **Utility** | Useful utility commands for everyday server management | [Details](utility/index.md) |
| **Fun** | Entertainment and fun commands for your Discord server | [Details](fun/index.md) |
| **Info** | Information display commands for Discord objects and entities | [Details](info/index.md) |
| **Snippets** | Create and manage code snippets and aliases for quick access | [Details](snippets/index.md) |
| **Tools** | Useful tools and integrations for enhanced functionality | [Details](tools/index.md) |
| **Levels** | Level and XP tracking system for Discord guilds | [Details](levels/index.md) |
| **Config** | Comprehensive guild configuration and management system | [Details](config/index.md) |

## Getting Started

To get started with Tux's commands:

1. **Invite Tux** to your server using the [Setup Guide](../../admin/setup/index.md)
2. **Configure permissions** using the [Permission Configuration](../../admin/config/commands.md) guide
3. **Explore modules** using the links above to find commands that fit your needs

## Command Types

Tux supports both slash commands and prefix commands:

- **Slash commands**: Modern Discord slash commands (e.g., `/ping`)
- **Prefix commands**: Traditional text commands using the `$` prefix (e.g., `$ping`)

Most commands support both formats, though some specialized commands may only be available as slash commands.

## Permissions

Tux uses a dynamic permission system that allows you to configure who can use which commands. By default, most utility and fun commands are available to all users, while moderation and configuration commands require appropriate permission ranks.

!!! tip "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../admin/config/commands.md) guide.

## Related Documentation

- [Admin Setup Guide](../../admin/setup/index.md) - Initial bot setup and configuration
- [Permission Configuration](../../admin/config/commands.md) - Configure command permissions
- [Admin Configuration Guide](../../admin/config/index.md) - Complete configuration reference
