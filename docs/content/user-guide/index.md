# User Guide

Welcome to the Tux User Guide! This section covers everything you need to know to use Tux in your Discord server.

## What is Tux?

Tux is a comprehensive Discord bot built for Linux communities, offering powerful moderation tools, community engagement features, and utility commands.

## Quick Navigation

### 🚀 Getting Started

New to Tux? Start here:

- **[Inviting Tux](inviting-tux.md)** - Add Tux to your server
- **[Understanding Permissions](permissions.md)** - Learn how Tux's permission system works
- **[Configuration](commands/config.md)** - Set up Tux with the config wizard

### 📋 Commands by Category

Explore all available commands:

- **[Moderation](commands/moderation.md)** - Ban, kick, jail, timeout, warn, and case management
- **[Utility](commands/utility.md)** - Ping, polls, reminders, AFK, timezone tools
- **[Info](commands/info.md)** - User, server, and channel information
- **[Snippets](commands/snippets.md)** - Create and manage text snippets
- **[Levels](commands/levels.md)** - View and manage XP/levels
- **[Fun](commands/fun.md)** - Random commands and XKCD comics
- **[Tools](commands/tools.md)** - TLDR pages, Wolfram Alpha, Wikipedia
- **[Code Execution](commands/code-execution.md)** - Run code with Godbolt/Wandbox
- **[Config](commands/config.md)** - Server configuration commands
- **[Admin/Dev](commands/admin.md)** - Administrative and development commands

### 🎮 Features

Discover Tux's powerful features:

- **[XP & Leveling System](features/xp-system.md)** - Engage your community with ranks
- **[Starboard](features/starboard.md)** - Highlight great messages
- **[Bookmarks](features/bookmarks.md)** - Save messages for later
- **[Temporary Voice Channels](features/temp-vc.md)** - Auto-created voice channels
- **[Status Roles](features/status-roles.md)** - Roles based on Discord status
- **[GIF Limiter](features/gif-limiter.md)** - Control GIF spam

## Common Tasks

### First-Time Setup

1. **[Invite Tux](inviting-tux.md)** to your server
2. Run `/config wizard` to set up basic configuration
3. **[Configure permissions](permissions.md)** for your moderators
4. Set up your channels and roles

### Moderation

- **Timeout a user**: `/timeout @user 10m Spam`
- **Ban a user**: `/ban @user Violated rules`
- **View cases**: `/cases view` or `/cases view 123`
- **Manage jail**: `/jail @user` and `/unjail @user`

### Community Engagement

- **Check XP**: `/level` or `/level @user`
- **Create poll**: `/poll "Question?" "Option 1" "Option 2"`
- **Set reminder**: `/remindme 1h Check something`
- **View starboard**: Messages with ⭐ reactions

### Server Management

- **Create snippet**: `/createsnippet rules Server rules text...`
- **Use snippet**: `/snippet rules`
- **Set AFK**: `/afk Going to lunch`
- **Get info**: `/info @user` or `/info #channel`

## Permission System

Tux uses a **rank-based permission system** with levels 0-7:

| Rank | Name               | Typical Use            |
|------|--------------------|------------------------|
| 0    | Member             | Basic server member    |
| 1    | Trusted            | Trusted members        |
| 2    | Junior Moderator   | Can warn, timeout      |
| 3    | Moderator          | Can kick, ban          |
| 4    | Senior Moderator   | Full moderation access |
| 5    | Administrator      | Server administration  |
| 6    | Head Administrator | Full server control    |
| 7    | Server Owner       | Complete access        |

**[Learn more about permissions →](permissions.md)**

## Command Syntax

### Slash Commands (Recommended)

Tux fully supports Discord slash commands with auto-completion:

```
/command option:value
/timeout user:@someone duration:10m reason:Spam
```

### Prefix Commands

You can also use traditional prefix commands (default: `$`):

```
$command arguments
$timeout @someone 10m Spam
```

The prefix can be customized with `/config prefix`.

## Getting Help

### In-Discord Help

Use Tux's built-in help system:

```
/help                    # Show all commands
/help moderation         # Show category help
/help timeout            # Show specific command help
```

### External Resources

- **[FAQ](../community/faq.md)** - Common questions and answers
- **[Discord Support](https://discord.gg/gpmSjcjQxg)** - Get help from the community
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs or request features

## Tips for Users

!!! tip "Use Slash Commands"
    Slash commands provide:

    - Auto-completion for options
    - Built-in help text
    - Better error messages
    - Consistent syntax

!!! tip "Check Permissions"
    If a command doesn't work, check:

    1. Your assigned roles (`/config role`)
    2. The command's required rank
    3. Channel-specific permissions

!!! tip "Bookmark the Docs"
    Save this documentation for quick reference:

    - Bookmark this page
    - Use browser search (Ctrl+F) to find commands
    - Check the command reference pages

## For Server Administrators

### Initial Setup

1. **Run Config Wizard**: `/config wizard`
   - Set up moderation channels
   - Configure jail system
   - Set up starboard
   - Configure XP roles

2. **Set Up Permission Ranks**: `/config rank init`
   - Assign roles to permission ranks
   - Test permissions with different roles
   - Adjust as needed

3. **Configure Features**:
   - Enable/disable features in config
   - Set up logging channels
   - Configure XP multipliers
   - Set up automated actions

### Recommended Configuration

For a typical server:

- **Moderation Channel**: Private channel for mod logs
- **Jail Role**: Role that restricts channel access
- **Starboard**: Public channel for starred messages (requires 3-5 stars)
- **XP System**: Enable with role rewards at key levels

### Moderation Best Practices

- **Use warnings** before timeouts/bans
- **Document cases** with detailed reasons
- **Review cases regularly** with `/cases`
- **Set up automated logging** for transparency
- **Train moderators** on command usage

## Customization

### Per-Server Configuration

Each server can customize:

- Command prefix
- Permission rank assignments
- Feature enable/disable
- XP role rewards
- Starboard threshold
- Jail system configuration

Use `/config` to manage these settings.

### Role Integration

Tux integrates with Discord roles:

- **Permission Ranks**: Assign Discord roles to Tux permission ranks
- **XP Roles**: Auto-assign roles based on XP level
- **Jail System**: Uses a configured jail role
- **Status Roles**: Auto-assign based on Discord status

## What's Next?

### New Users

- **[Browse Commands](commands/moderation.md)** - Explore all available commands
- **[Learn Permissions](permissions.md)** - Understand how permissions work
- **[Try Features](features/xp-system.md)** - Discover Tux's features

### Moderators

- **[Moderation Commands](commands/moderation.md)** - Essential moderation tools
- **[Case Management](commands/moderation.md#cases)** - Track and manage cases
- **[Configuration](commands/config.md)** - Server setup and management

### Administrators

- **[Advanced Config](commands/config.md)** - Deep dive into configuration
- **[Permission Setup](permissions.md)** - Configure your permission hierarchy
- **[Self-Hosting](../getting-started/for-self-hosters.md)** - Run your own instance

Ready to explore? Choose a section from the navigation or check out the **[command reference](commands/moderation.md)**!
