---
title: Timeout
description: Temporarily restrict a member's interaction
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Timeout

The `timeout` command (also available as `mute`) allows server moderators to temporarily restrict a member's ability to send messages, add reactions, and participate in voice channels.

This is an official Discord feature that temporarily restricts member interaction without removing them from the server. Tux integrates this with its moderation system, ensuring every timeout is logged as a case with its duration and reason.

## Syntax

The `timeout` command can be used in two ways:

**Slash Command:**

```text
/timeout member:@user reason:STRING duration:TIME [silent:true/false]
```

**Prefix Command:**

```text
$timeout @user -duration TIME [reason] [-silent]
```

**Aliases:**

- `to`
- `mute`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to timeout. |
| `reason` | String | No | The reason for the timeout, logged in the moderation case and included in the DM notification. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-duration` | Time | **Required** | Length of the timeout (max 28 days). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### -duration

The length of time the member should be restricted. Tux supports a standard time format (e.g., `1h`, `30m`).

!!! warning "Discord Limit"
    Discord limits the maximum timeout duration to **28 days**. If you provide a longer duration, Tux will automatically cap it at 28 days.

- **Format:** `[number][unit]` (e.g., `12h`, `7d`, `45m`)
- **Aliases:** `-t`, `-d`, `-e`

### -silent

Whether to suppress the DM notification to the timed-out user.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Moderate Members** - Required to apply the Discord timeout.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Timeout (Slash)

Timing out a member for 1 hour.

```text
/timeout member:@user reason:"Spamming" duration:1h
```

### Prefix with Reason

```text
$timeout @user -duration 24h Spamming in #general
```

### Max Duration (Slash)

Giving a user a 28-day timeout.

```text
/timeout member:@user reason:"Severe rule violation" duration:28d
```

## Response Format

When executed successfully, Tux will:

1. Attempt to DM the user with the timeout duration and reason (unless `-silent` is used).
2. Execute the official Discord timeout action.
3. Create a new moderation case in the database.
4. Post a confirmation message in the current channel showing the timeout details.
5. Log the action in the designated moderation log channel.

The confirmation message includes the timed-out user's name, the duration, the reason, and a link to view the moderation case.

## Error Handling

### Common Errors

#### Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Moderate Members" permission, or the target user's role is higher than Tux's role.

**What happens:** The bot sends an error message indicating insufficient permissions.

**Solutions:**

- Ensure Tux has the "Moderate Members" permission
- Move Tux's role higher in the hierarchy
- Check that Tux's role has the necessary permissions in the server settings

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### Invalid Duration

**When it occurs:** The provided duration string is invalid or exceeds 28 days.

**What happens:** The bot sends an error message indicating the duration format is invalid or too long.

**Solutions:**

- Use the `[number][unit]` format (e.g., `1h`, `7d`, `30m`)
- Ensure the total duration is less than or equal to 28 days (Discord's maximum)
- Combine units if needed (e.g., `1d12h` for 1 day and 12 hours)

#### Bots Cannot Be Timed Out

**When it occurs:** You attempt to timeout another bot.

**What happens:** The bot sends an error message indicating bots cannot be timed out.

**Solutions:**

- Bots are immune to the timeout feature - use roles or a ban if necessary
- Consider using `/kick` or `/ban` for bot moderation instead

## Related Commands

- [`/untimeout`](untimeout.md) - Remove a timeout early
- [`/jail`](jail.md) - Restriction to a specific channel (alternative to timeout)
- [`/cases`](cases.md) - View moderation history
