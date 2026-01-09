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

The `info` command is a powerful lookup tool that provides an overview into various Discord entities. The `info` command gathers all relevant data into an organized and readable embed.

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

## Supported Entities

The command automatically detects the type of entity provided based on mentions, IDs, or links.

- **Members & Users:** Join dates, registration dates, roles, and IDs.
- **Channels:** Type, position, slowmode settings, and category.
- **Roles:** Color, permissions, member count, and hoist status.
- **Servers (Guilds):** Owner, member breakdown (humans vs bots), boost status, and creation date.
- **Messages:** Author, content snippet, attachment counts, and direct links.
- **Emojis & Stickers:** Animated status, source link, and creation date.
- **Threads & Events:** Owner, status, and related timing information.
- **Invites:** Code, server source, and expiration data.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | STRING | Yes | The ID, mention, or link of the object you want information about. |

## Usage Examples

### Look Up a Member

Get detailed server-specific information about a member.

```text
/info entity:@User
```

### Inspect a Role

Check the permissions and color of a specific role.

```text
/info entity:@Admin
```

### Server Overview

Provide a server ID to see its statistics (the bot must be in the server).

```text
/info entity:123456789012345678
```

### Channel Details

View the settings of a specific channel.

```text
/info entity:#general
```

## Permissions

### Bot Permissions

Tux requires the following permissions to execute this command:

- **Embed Links** - To display the gathered information.
- **Read Message History** - Needed to look up specific messages by ID.

### User Permissions

This command is available to all users. Administrative data (like server bans) might be restricted to higher ranks if configured differently.

## Response

The response is a rich embed tailored to the type of object detected. It typically includes:

- A title with the entity's name.
- Key timestamps (Created, Joined).
- Unique identifiers (IDs).
- Specific metadata (Roles, Permissions, Status).

## Related Commands

- [`/avatar`](avatar.md) - View profile pictures of users.
- [`/membercount`](membercount.md) - Quick server population stats.
