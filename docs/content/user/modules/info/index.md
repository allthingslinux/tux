---
title: Info
description: Information display commands for Discord objects and entities
tags:
  - user-guide
  - modules
  - info
icon: lucide/text-search
---

# Info

The Info module provides commands to view detailed information about Discord objects including users, members, channels, roles, servers, and more. These commands help you understand server structure and member details.

By offering comprehensive information display commands, this module allows users to see detailed data about various Discord entities. Whether you need to check user details, server information, or channel settings, these commands provide all the information you need in organized embeds.

## Command Groups

This module includes the following command groups:

### Info

The `/info` command group provides subcommands for viewing detailed information about specific Discord entity types.

**Available Subcommands:**

- `info server` - Server/guild information
- `info user` / `info member` - User and member information
- `info emoji` - Emoji information
- `info role` - Role information
- `info channel` - Channel and thread information
- `info invite` - Invite information

## Commands

| Command | Aliases | Description | Documentation |
|---------|---------|-------------|---------------|
| `/info` | `i` | Get information about Discord objects (command group) | [Details](info.md) |
| `/avatar` | — | View user avatars | [Details](avatar.md) |
| `/membercount` | `mc`, `members` | View server member statistics | [Details](membercount.md) |

## Common Use Cases

### Viewing User Information

Get detailed information about server members or users, including IDs, join dates, and account age.

**Steps:**

1. Use the `/info user` or `/info member` command followed by a user mention or ID.
2. Review the rich embed containing user and server-specific details.

**Example:**

```text
/info user @user
/info member 123456789012345678
$info user @User#1234
```

### Viewing Avatars

Check user avatar images and details in a high-quality format.

**Steps:**

1. Use the `/avatar` command and specify a member.
2. The bot will return the user's global and server-specific avatars.

**Example:**

```text
/avatar member:@user
```

### Viewing Server Statistics

Get a quick breakdown of your server's population, including humans and bots.

**Steps:**

1. Use the `/membercount` command.
2. View the total member count along with the specific counts for human users and automated bots.

**Example:**

```text
/membercount
```

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Send Messages** - Required for command responses
- **Embed Links** - Required for information embeds
- **Read Message History** - Required for some context-aware information lookup

### User Permissions

Info commands are available to all users by default.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Configuration Guide](../../../admin/config/index.md)
