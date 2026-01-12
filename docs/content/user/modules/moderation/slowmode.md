---
title: Slowmode
description: Set or get the message delay for a channel
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Slowmode

The `slowmode` command allows server moderators to control the rate at which members can send messages in a channel. This is highly effective for managing high-traffic discussions, stopping spam, or forcing a slower pace in specific channels.

When slowmode is active, users will see a countdown in their message box after sending a message, indicating how long they must wait before sending another.

## Syntax

The `slowmode` command can be used in two ways:

**Slash Command:**

```text
/slowmode [seconds:STRING] [channel:CHANNEL]
```

**Prefix Command:**

```text
$slowmode [seconds] [channel]
$sm [seconds] [channel]
```

**Aliases:**

You can also use these aliases instead of `slowmode`:

- `sm`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | Channel | No | The channel to modify (defaults to current). |
| `seconds` | String | No | The delay value (e.g., `10`, `5s`, `2m`). If omitted, Tux returns the current setting. |

## Constraints

- **Maximum Delay:** Discord allows a maximum slowmode of **21600 seconds** (6 hours).
- **Minimum Delay:** `0` (disables slowmode).

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Manage Channels** - Required to modify channel settings like slowmode.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Get Current Slowmode

Check the slowmode setting for the current channel.

```text
/slowmode
```

### Set Slowmode in Current Channel

Setting a 10-second delay.

```text
/slowmode seconds:10
```

### Set Slowmode for Another Channel

Setting a 5-minute delay for #general.

```text
$slowmode #general 5m
```

### Disable Slowmode

```text
/slowmode seconds:0
```

## Response Format

When executed successfully, Tux will:

1. Update the channel's slowmode setting on Discord.
2. Return a confirmation message (slash command) or send a temporary confirmation (prefix command) stating the new slowmode setting.

The confirmation message shows the channel name and the new slowmode delay. If no delay is specified, it shows the current slowmode setting for that channel.

## Error Handling

### Common Errors

#### Invalid Delay Format

**When it occurs:** The provided delay string is not a simple number or doesn't use supported units (`s`, `m`, `h`).

**What happens:** The bot sends an error message indicating the delay format is invalid.

**Solutions:**

- Use a number (seconds) or a number with a unit (e.g., `30s`, `10m`, `2h`)
- Supported units: `s` (seconds), `m` (minutes), `h` (hours)
- Examples: `10`, `30s`, `5m`, `1h`

#### Amount Too High

**When it occurs:** The requested delay exceeds 6 hours (21600 seconds).

**What happens:** The bot sends an error message indicating the delay exceeds Discord's maximum.

**Solutions:**

- Use a delay within the 0 to 21600 second range (0 to 6 hours)
- Discord's maximum slowmode is 6 hours
- Use `0` to disable slowmode completely

#### Unsupported Channel Type

**When it occurs:** You attempt to set slowmode in a channel type that doesn't support it (e.g., a Category).

**What happens:** The bot sends an error message indicating the channel type doesn't support slowmode.

**Solutions:**

- Use slowmode in Text Channels, Threads, or Voice Channels
- Categories and other channel types don't support slowmode
- Select a specific channel within the category instead

## Related Commands

- [`/purge`](purge.md) - Clean up messages if spam has already occurred
- [`/timeout`](timeout.md) - Restrict a specific user instead of the entire channel
