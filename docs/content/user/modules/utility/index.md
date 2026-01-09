---
title: Utility
description: Useful utility commands for everyday Discord server management
tags:
  - user-guide
  - modules
  - utility
icon: lucide/compass
---

# Utility

The Utility module provides helpful commands for everyday server management and user interaction. These commands cover a wide range of utilities including polls, reminders, user information, encoding tools, and server status checks.

These practical tools enhance server functionality and user experience by helping keep your server organized and engaging. From creating polls to setting reminders and checking server status, the Utility module provides the essential toolkit for active community management.

## Command Groups

This module includes the following command groups:

### Wiki

The `/wiki` command group provides quick access to specialized documentation wikis.

**Commands:**

- `/wiki arch` - Search the Arch Linux Wiki
- `/wiki atl` - Search the All Things Linux Wiki

## Commands

| Command | Description | Documentation |
|---------|-------------|---------------|
| `/ping` | Check bot latency and status | [Details](ping.md) |
| `/poll` | Create a poll with multiple options (Slash only) | [Details](poll.md) |
| `/remindme` | Set a reminder for yourself | [Details](remindme.md) |
| `/afk` | Set or clear your AFK status | [Details](afk.md) |
| `/wiki` | Search Wikipedia | [Details](wiki.md) |
| `/encode` `/decode` | Encode or decode text | [Details](encode-decode.md) |
| `/timezones` | View current times across the globe | [Details](timezones.md) |
| `/self_timeout` | Time yourself out | [Details](self-timeout.md) |
| `$run` | Run code snippets (Prefix only) | [Details](run.md) |

## Common Use Cases

### Server Status Check

Quickly check if the bot is online and responsive to ensure it is functioning correctly.

**Steps:**

1. Use the `/ping` command in any text channel.
2. Observe the bot's response time (latency).

**Example:**

```text
/ping
```

### Creating Polls

Get community feedback on decisions or topics by creating interactive polls.

**Steps:**

1. Use the `/poll` command with a title and comma-separated options.
2. The bot will create a message with reaction buttons for each option.
3. Users can vote by clicking the reactions.

**Example:**

```text
/poll title:"What should we do next?" options:"Option 1, Option 2, Option 3"
```

### Setting Reminders

Set personal reminders for important events or tasks.

**Steps:**

1. Use the `/remindme` command with a duration and the reminder text.
2. Tux will set a timer and DM you (or message the channel) when the time expires.

**Example:**

```text
/remindme time:2h reminder:"Check the announcement channel"
```

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Send Messages** - Required for command responses
- **Add Reactions** - Required for creating interactive polls
- **Manage Messages** - Required for some utility functions and cleanup
- **Embed Links** - Required for rich utility responses

### User Permissions

Most utility commands are available to all users by default. Some advanced commands like `$run` may require higher permission ranks.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Configuration Guide](../../../admin/config/index.md)
- [Command Reference](../../reference/index.md)
