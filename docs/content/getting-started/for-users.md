# Getting Started - For Users

Welcome! This guide will help you start using Tux in your Discord server.

## What is Tux?

Tux is an all-in-one Discord bot designed for Linux communities, offering:

- **Moderation Tools**: Ban, kick, timeout, jail, and comprehensive case management
- **XP & Leveling**: Engage your community with ranks and rewards
- **Utility Commands**: Polls, reminders, code execution, and more
- **Server Management**: Snippets, bookmarks, member info, and configuration
- **Fun Features**: Random commands, XKCD comics, and community engagement

## Two Ways to Use Tux

### Option 1: Use the Official Tux Bot

The easiest way to get started is to invite the official Tux bot to your server.

!!! note "Coming Soon"
    The official Tux bot invite link will be available here once the bot is publicly hosted.
    For now, you'll need to self-host (see [Self-Hoster Guide](for-self-hosters.md)).

### Option 2: Self-Host Tux

If you want full control or the official bot isn't available yet, you can [run your own instance](for-self-hosters.md).

## Next Steps

Once Tux is in your server:

### 1. Learn the Basics

- **[Permission System](../user-guide/permissions.md)** - Understand how Tux permissions work
- **[Moderation Commands](../user-guide/commands/moderation.md)** - Essential commands for moderators
- **[Configuration](../user-guide/commands/config.md)** - Set up your server with the config wizard

### 2. Explore Features

- **[XP & Leveling](../user-guide/features/xp-system.md)** - Engage your community
- **[Starboard](../user-guide/features/starboard.md)** - Highlight great messages
- **[Snippets](../user-guide/commands/snippets.md)** - Create reusable text snippets
- **[Bookmarks](../user-guide/features/bookmarks.md)** - Save messages for later

### 3. Browse All Commands

Explore the complete command reference:

- **[Moderation Commands](../user-guide/commands/moderation.md)** - Ban, kick, jail, timeout, warn
- **[Utility Commands](../user-guide/commands/utility.md)** - Ping, poll, reminders, AFK
- **[Info Commands](../user-guide/commands/info.md)** - User/server information
- **[Tools](../user-guide/commands/tools.md)** - TLDR, Wolfram, Wikipedia
- **[Fun Commands](../user-guide/commands/fun.md)** - Random, XKCD
- **[Code Execution](../user-guide/commands/code-execution.md)** - Run code snippets

## Common First Tasks

### Setting Up Permissions

Tux uses a rank-based permission system (0-7). To set up permissions for your moderators:

```text
/config rank init
/config role assign 3 @Moderators
```

[Learn more about permissions →](../user-guide/permissions.md)

### Running the Setup Wizard

Use the interactive setup wizard to configure Tux for your server:

```text
/config wizard
```

This will guide you through:

- Setting up moderation channels
- Configuring the jail system
- Setting up starboard
- Configuring XP roles

### First Moderation Actions

Try these essential moderation commands:

```text
/timeout @user 10m Spam
/warn @user Please follow the rules
/cases view
```

## Getting Help

### In-Discord Help

Use Tux's built-in help system:

```text
/help
/help moderation
/help command_name
```

### Documentation

- **[User Guide](../user-guide/index.md)** - Complete command reference
- **[FAQ](../community/faq.md)** - Common questions

### Community Support

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask questions and get help
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs

## Tips for New Users

!!! tip "Use Slash Commands"
    Tux supports both prefix commands (`$command`) and slash commands (`/command`).
    Slash commands provide auto-completion and are easier to discover!

!!! tip "Check Permissions"
    Make sure Tux has the necessary Discord permissions in your server:

```text
- Read/Send Messages
- Manage Messages
- Kick/Ban Members
- Timeout Members
- Manage Roles (for jail system)
```

!!! tip "Start with Config Wizard"
    The `/config wizard` is the easiest way to set up Tux properly. It only takes a few minutes!

## What's Next?

- **[Explore All Commands](../user-guide/commands/moderation.md)** - Browse the complete command reference
- **[Learn About Permissions](../user-guide/permissions.md)** - Understand Tux's permission system
- **[Discover Features](../user-guide/features/xp-system.md)** - Learn about XP, starboard, and more

Ready to dive in? Head to the **[User Guide](../user-guide/index.md)** to explore everything Tux can do!
