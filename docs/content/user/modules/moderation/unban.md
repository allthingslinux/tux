---
title: Unban
description: Unban a previously banned member from your Discord server
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Unban

The `unban` command allows server moderators to lift a ban from a user, allowing them to rejoin the server through a valid invite. This command supports resolving users from the server's ban list using their username, full name with discriminator, or their unique Discord ID.

Unlike the ban command, Tux does not attempt to DM the user when they are unbanned, as they are not currently in the server and cannot receive direct messages from the bot in most cases.

## Syntax

The `unban` command can be used in two ways:

**Slash Command:**

```text
/unban user:IDENTIFIER [reason:STRING]
```

**Prefix Command:**

```text
$unban IDENTIFIER [reason]
```

**Aliases:**

- `ub`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `reason` | String | No | The reason for the unban (positional). |
| `user` | String / User | Yes | The username, ID, or mention of the user to unban. |

## User Resolution

Tux is flexible when searching for banned users. You can provide:

- **Discord ID:** `123456789012345678` (Most reliable)
- **Exact Username:** `username`
- **Username and Discriminator:** `username#1234` (Legacy)
- **Partial Username:** If exactly one banned user matches the partial name, Tux will select them.

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Ban Members** - Required to remove the user from the guild's ban list.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Unban by ID

The most reliable way to unban a user.

```text
/unban user:123456789012345678
```

### Unban by Username with Reason

Unbanning a user and providing a reason for the log.

```text
$unban "User Name" Appeal accepted after 1 month
```

### Unban with Partial Match

If "JaneDoe" is the only banned user with "Jane" in their name:

```text
/unban user:Jane reason:"Partial name match"
```

## Response

When executed successfully, Tux will:

1. Resolve the user from the guild's ban list.
2. Remove the ban on the Discord server.
3. Create a new moderation case in the database.
4. Post a confirmation message in the current channel.
5. Log the action in the designated moderation log channel.

## Error Handling

### Common Errors

#### Error: User Not Found

**When it occurs:** The provided ID or name does not match any entry in the guild's ban list.

**Solution:** Double-check the ID or use the exact username. You can view the ban list in Server Settings > Bans.

#### Error: Already Unbanned

**When it occurs:** The user is not currently in the server's ban list.

**Solution:** No action needed.

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command.

**Solution:** Contact a server administrator to check your rank.

#### Error: Bot Missing Permissions

**When it occurs:** Tux lacks the "Ban Members" permission required to remove bans.

**Solution:** Grant Tux the "Ban Members" permission in the server settings.

## Related Commands

- [`/ban`](ban.md) - Permanently ban a member.
- [`/tempban`](tempban.md) - Ban a member for a set duration.
- [`/cases`](cases.md) - View moderation history and previous ban reasons.
