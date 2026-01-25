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

The `info` command group provides a powerful lookup tool that displays detailed information about various Discord entities. Each subcommand is designed for a specific entity type, making it easy to find the information you need.

## Syntax

The `info` command is a command group with multiple subcommands:

**Slash Command:**

```text
/info <subcommand> <entity>
```

**Prefix Command:**

```text
$info <subcommand> <entity>
$i <subcommand> <entity>
```

**Aliases:**

You can also use these aliases instead of `info`:

- `i`

When you call `/info` without any subcommand, it displays help information showing available subcommands.

## Subcommands

### `info server`

Get information about a server/guild.

**Aliases:** `guild`, `s`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `guild_id` | STRING | No | The guild ID to get information about. If omitted, shows current server. |

**Examples:**

```text
/info server
/info server 123456789012345678
$info server
$i s 123456789012345678
```

**Information Displayed:**

- Owner, vanity URL, boosts
- Channel counts (text, voice, forum)
- Emoji and sticker counts
- Role count
- Member breakdown (humans vs bots)
- Ban count
- Creation date

### `info user` / `info member`

Get information about a user or member.

**Aliases:** `user`, `member`, `u`, `m`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | STRING | Yes | The user or member to get information about (mention or ID). |

**Examples:**

```text
/info user @User
/info member 123456789012345678
$info user @User#1234
$i u 123456789012345678
```

**Information Displayed:**

- Bot status, username, ID
- Join date (for members)
- Registration date
- Roles (for members)
- Avatar and banner

### `info emoji`

Get information about an emoji.

**Aliases:** `e`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `emoji` | EMOJI | Yes | The emoji to get information about (mention or ID). |

**Examples:**

```text
/info emoji :emoji_name:
/info emoji 123456789012345678
$info emoji :emoji_name:
$i e 123456789012345678
```

**Information Displayed:**

- Animated status
- Managed status
- Availability
- Requires colons status
- Creation date

### `info role`

Get information about a role.

**Aliases:** `r`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | ROLE | Yes | The role to get information about (mention or ID). |

**Examples:**

```text
/info role @RoleName
/info role 987654321098765432
$info role @Admin
$i r 987654321098765432
```

**Information Displayed:**

- Color, position
- Mentionable, hoisted, managed status
- Member count
- Permissions
- Creation date

### `info channel`

Get information about a channel or thread.

**Aliases:** `c`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | CHANNEL/THREAD | Yes | The channel or thread to get information about (mention or ID). |

**Examples:**

```text
/info channel #general
/info channel 123456789012345678
$info channel #general
$i c 123456789012345678
```

**Information Displayed:**

- Type, position, category
- Slowmode (for text channels)
- NSFW status (for text channels)
- Bitrate and user limit (for voice channels)
- Available tags (for forum channels)
- Thread-specific info (for threads)
- Creation date

### `info invite`

Get information about an invite.

**Aliases:** `inv`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `invite_code` | STRING | Yes | The invite code or URL to get information about. |

**Examples:**

```text
/info invite discord.gg/invitecode
/info invite https://discord.gg/invitecode
$info invite invitecode
$i inv discord.gg/invitecode
```

**Information Displayed:**

- Guild and channel
- Inviter
- Uses (current/max)
- Expiration date
- Temporary status
- Creation date

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

Each subcommand returns a rich embed tailored to the entity type. The embed includes:

- **Title** - The entity's name or identifier
- **Timestamps** - Creation date, join date (for members), or other relevant dates formatted as Discord timestamps
- **Unique identifiers** - Full Discord IDs for reference
- **Entity-specific metadata** - Such as roles (for members), permissions (for roles/channels), member counts, status information, and more
- **Visual elements** - Colors (for roles), avatars (for users), thumbnails (for emojis), and other visual indicators

The embed format varies based on the entity type to show the most relevant information for each object.

## Related Commands

- [`/avatar`](avatar.md) - View profile pictures of users
- [`/membercount`](membercount.md) - Quick server population statistics
