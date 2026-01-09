---
title: Purge
description: Delete multiple messages from a channel in bulk
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Purge

The `purge` command (also available as `p`) allows server moderators to quickly delete a large number of messages from a channel. This is essential for cleaning up spam, removing inappropriate content, or clearing out old messages from a channel.

## Syntax

The `purge` command can be used in two ways:

**Slash Command:**

```text
/purge limit:INTEGER [channel:CHANNEL]
```

**Prefix Command:**

```text
$purge NUMBER [channel]
```

**Aliases:**

- `p`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | Integer | Yes | The number of messages to delete (1-500). |
| `channel` | Channel | No | The channel to delete messages from (defaults to current). |

## Constraints

- **Amount:** You can purge between 1 and 500 messages at a time.
- **Message Age:** Due to Discord API limitations, you can only bulk-delete messages that are **less than 14 days old**. Messages older than 14 days will be skipped.

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Manage Messages** - Required to delete messages sent by other users.
- **Read Message History** - Required to find the messages to delete.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Simple Purge

Deleting the last 50 messages in the current channel.

```text
/purge limit:50
```

### Prefix Usage

Deleting 10 messages from the channel you are currently in.

```text
$purge 10
```

### Specific Channel

Deleting 100 messages from another channel.

```text
/purge limit:100 channel:#spam-channel
```

## Response

When executed successfully, Tux will:

1. Delete the requested number of messages (up to 500, and only those under 14 days old).
2. Post an ephemeral confirmation (slash command) or a temporary message (prefix command) stating exactly how many messages were removed.

## Error Handling

### Common Errors

#### Error: Invalid Amount

**When it occurs:** You provide a number less than 1 or greater than 500.

**Solution:** Use a number within the allowed range (1-500).

#### Error: Missing Permissions

**When it occurs:** Tux does not have the "Manage Messages" permission in the target channel.

**Solution:** Ensure Tux's role has the necessary permissions in that specific channel or category.

#### Error: 14-Day Limit

**When it occurs:** You try to delete messages, but none are removed or fewer than requested are removed because they are too old.

**Solution:** This is a Discord-side limitation; older messages must be deleted manually.

## Related Commands

- [`/slowmode`](slowmode.md) - Slow down a channel to prevent future spam.
- [`/timeout`](timeout.md) - Temporarily restrict a specific user from messaging.
