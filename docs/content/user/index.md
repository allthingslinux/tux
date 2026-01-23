---
title: User Guide
hide:
  - toc
tags:
  - user-guide
icon: octicons/person-24
---

# User Guide

Welcome to the Tux User Guide! This guide covers everything you need to know to use Tux's commands and features on your Discord server.

## Quick Start

1. **Get Help** - Use `$help` to explore all available commands
2. **Check Status** - Use `$ping` to verify the bot is online
3. **Explore Commands** - Browse command modules to find what you need

## Command Types

Tux supports both modern slash commands and traditional prefix commands:

- **Slash Commands** - Modern Discord slash commands (e.g., `/ping`, `/ban`)
- **Prefix Commands** - Traditional text commands using the `$` prefix (e.g., `$ping`, `$ban`, `$help`)

Most commands support both formats, though some specialized commands may only be available as one type. The help command is only available as a prefix command (`$help`).

## Getting Help

The easiest way to learn about Tux's commands is through the interactive help system:

```text
$help
```

This opens an interactive menu where you can:

- Browse commands by category
- View detailed command information
- See usage examples and parameters
- Discover new features

See the [Help Command](modules/utility/help.md) documentation for more details.

## Command Modules

Tux organizes commands into modules for easy navigation:

### [Moderation](modules/moderation/index.md)

Comprehensive moderation tools for managing your Discord server, including bans, kicks, timeouts, warnings, and case management.

**Key Commands:**

- `$ban` - Ban a member from the server
- `$kick` - Remove a member from the server
- `$timeout` - Temporarily restrict a member
- `$warn` - Issue a warning to a member
- `$cases` - View and manage moderation cases

### [Utility](modules/utility/index.md)

Useful utility commands for everyday server management, including polls, reminders, user information, and server status.

**Key Commands:**

- `$help` - Get help with commands
- `$ping` - Check bot status and latency
- `$poll` - Create interactive polls
- `$remindme` - Set personal reminders
- `$wiki` - Search specialized wikis

### [Fun](modules/fun/index.md)

Entertainment and fun commands to keep your server engaging and active.

**Key Commands:**

- `$random` - Generate random numbers or choices
- `$xkcd` - View XKCD comics

### [Info](modules/info/index.md)

Information display commands for Discord objects and entities, including members, channels, roles, and servers.

**Key Commands:**

- `$info` - Get detailed information about Discord entities
- `$avatar` - View user avatars
- `$membercount` - Display server member statistics

### [Snippets](modules/snippets/index.md)

Create and manage code snippets and aliases for quick access to frequently used content.

**Key Commands:**

- `$snippet` - Create a new snippet
- `$snippets` - List all snippets
- `$snippetinfo` - View snippet details

### [Tools](modules/tools/index.md)

Useful tools and integrations for enhanced functionality, including command documentation and computational tools.

**Key Commands:**

- `$tldr` - Quick command-line documentation
- `$wolfram` - Computational queries

### [Levels](modules/levels/index.md)

Level and XP tracking system for Discord guilds, rewarding active members with levels and roles.

**Key Commands:**

- `$level` - View your current level and XP
- `$levels` - View level leaderboard

### [Config](modules/config/index.md)

Comprehensive guild configuration and management system for customizing Tux to your server's needs.

**Key Commands:**

- `$config` - Open the configuration dashboard
- `$config ranks` - Manage permission ranks
- `$config roles` - Assign roles to permission ranks
- `$config commands` - Configure command permissions

## Features

Tux also includes powerful features that work automatically:

### [Leveling](features/leveling.md)

Automatic XP and level tracking for active members, with configurable rewards and multipliers.

### [Starboard](features/starboard.md)

Message starboard system that highlights popular messages when they reach a reaction threshold.

### [Bookmarks](features/bookmarks.md)

Save and organize important messages for quick reference later.

### [Status Roles](features/status-roles.md)

Automatic role assignment based on user status (online, idle, do not disturb).

### [Temp VC](features/temp-vc.md)

Temporary voice channel creation for dynamic voice chat management.

### [GIF Limiter](features/gif-limiter.md)

Rate limiting for GIF messages to prevent spam and maintain server quality.

## Permissions

Tux uses a dynamic permission system that allows server administrators to customize who can use which commands. By default:

- **Utility and Fun Commands** - Available to all users
- **Moderation Commands** - Require appropriate permission ranks
- **Configuration Commands** - Require administrator permissions

!!! tip "Permission System"
    Your server administrators configure command permissions. If you can't use a command, contact them to check your permission rank. See the [Permission Configuration](../../admin/config/commands.md) guide for administrators.

## Common Tasks

### Check Bot Status

```text
$ping
```

### Get Help with Commands

```text
# Open interactive help menu
$help

# Get help for a specific command
$help ban

# Get help for a command group
$help cases
```

### Create a Poll

```text
$poll title:"What should we do?" options:"Option 1, Option 2, Option 3"
```

### Set a Reminder

```text
$remindme time:2h reminder:"Check announcements"
```

### View Server Information

```text
$info server
$info @user
```

## Need More Help?

- **Command Help** - Use `$help` for interactive command exploration
- **Admin Guide** - See the [Admin Guide](../../admin/index.md) for server configuration
- **FAQ** - Check the [FAQ](../../faq/users.md) for common questions
- **Support** - Join the [Support Server](https://discord.gg/gpmSjcjQxg) for assistance

## Related Documentation

- [Admin Guide](../../admin/index.md) - Server configuration and management
- [Permission Configuration](../../admin/config/commands.md) - Understanding permissions
- [FAQ](../../faq/users.md) - Frequently asked questions
- [Troubleshooting](../../support/troubleshooting/user.md) - Common issues and solutions
