---
title: Info
description: Get detailed information about Discord objects
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - info
---

# Info

The `info` command group provides a powerful lookup tool that displays detailed information about various Discord entities. It automatically detects the type of entity you provide (by mention, ID, or link) and gathers all relevant data into an organized and readable embed.

## Syntax

The `info` command can be used in two ways:

**Slash Command:**

```text
/info entity:STRING
```

**Prefix Command:**

```text
$info <entity>
```

**Aliases:**

- `i`

When you call `/info` without any parameters, it displays help information showing how to use the command.

## Supported Entities

The command automatically detects the type of entity you provide based on mentions, IDs, or links. You can use any of these formats:

- **User mentions:** `@username` or `@User#1234`
- **Channel mentions:** `#channel-name`
- **Role mentions:** `@RoleName`
- **IDs:** Numeric Discord IDs (e.g., `123456789012345678`)
- **Invite links:** Full invite URLs or invite codes (e.g., `discord.gg/invitecode`)

### Entity Types

The command supports the following entity types:

- **Members & Users:** Join dates, registration dates, roles, status, and IDs
- **Channels:** Type, position, slowmode settings, category, and permissions
- **Roles:** Color, permissions, member count, hoist status, and mentionable status
- **Servers (Guilds):** Owner, member breakdown (humans vs bots), boost status, creation date, and features
- **Messages:** Author, content snippet, attachment counts, embeds, and direct links
- **Emojis & Stickers:** Animated status, source link, creation date, and usage information
- **Threads:** Owner, status, creation date, and related timing information
- **Scheduled Events:** Creator, status, start/end times, and location
- **Invites:** Code, server source, expiration data, and usage statistics

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | STRING | Yes | The ID, mention, or link of the object you want information about. |

## Usage Examples

### Look Up a Member

Get detailed server-specific information about a member, including join date, roles, and account details.

```text
/info entity:@User
/info entity:123456789012345678
```

### Inspect a Role

Check the permissions, color, member count, and other details of a specific role.

```text
/info entity:@Admin
/info entity:987654321098765432
```

### Server Overview

View comprehensive server statistics including member breakdown, boost status, and server features. The bot must be in the server to view its information.

```text
/info entity:123456789012345678
```

### Channel Details

View the settings and configuration of a specific channel, including type, position, slowmode, and permissions.

```text
/info entity:#general
/info entity:123456789012345678
```

### View a Message

Get information about a specific message, including author, content preview, attachments, and embeds. Use a message link or ID.

```text
/info entity:https://discord.com/channels/123456/789012/345678
/info entity:123456789012345678
```

### Check an Invite

View invite details including the server it's for, expiration, and usage statistics.

```text
/info entity:discord.gg/invitecode
/info entity:https://discord.gg/invitecode
```

## Permissions

### Bot Permissions

Tux requires the following permissions to execute this command:

- **Embed Links** - To display the gathered information.
- **Read Message History** - Needed to look up specific messages by ID.

### User Permissions

This command is available to all users by default. Some administrative data (like server bans) might be restricted to higher permission ranks if configured differently.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Response Format

The command returns a rich embed tailored to the type of entity detected. Each entity type displays relevant information:

- **Title** - The entity's name or identifier
- **Timestamps** - Creation date, join date (for members), or other relevant dates formatted as Discord timestamps
- **Unique identifiers** - Full Discord IDs for reference
- **Entity-specific metadata** - Such as roles (for members), permissions (for roles/channels), member counts, status information, and more
- **Visual elements** - Colors (for roles), avatars (for users), thumbnails (for emojis/stickers), and other visual indicators

The embed format varies based on the entity type to show the most relevant information for each object.

## Related Commands

- [`/avatar`](avatar.md) - View profile pictures of users
- [`/membercount`](membercount.md) - Quick server population statistics
