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

This is an official Discord feature that provides a seamless way to handle disruptive users without removing them from the server. Tux integrates this with its moderation system, ensuring every timeout is logged as a case with its duration and reason.

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

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the timeout (positional). |
| `-duration` | Time | **Required** | Length of the timeout (max 28 days). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for the timeout, logged in the moderation case and included in the DM notification.

- **Type:** String
- **Default:** "No reason provided"

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

## Response

When executed successfully, Tux will:

1. Attempt to DM the user with the timeout duration and reason (unless `-silent` is used).
2. Execute the official Discord timeout action.
3. Create a new moderation case in the database.
4. Post a confirmation message in the current channel.
5. Log the action in the designated moderation log channel.

## Error Handling

### Common Errors

#### Error: Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Moderate Members" permission, or the target user's role is higher than Tux's role.

**Solution:** Ensure Tux has the "Moderate Members" permission. Move Tux's role higher in the hierarchy.

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command.

**Solution:** Contact a server administrator to check your rank.

#### Error: Invalid Duration

**When it occurs:** The provided duration string is invalid or exceeds 28 days.

**Solution:** Use the `[number][unit]` format (e.g., `1h`, `7d`). Ensure the total duration is less than 28 days.

#### Error: Bots Cannot Be Timed Out

**When it occurs:** You attempt to timeout another bot.

**Solution:** Bots are immune to the timeout feature; use roles or a ban if necessary.

## Related Commands

- [`/untimeout`](untimeout.md) - Remove a timeout early.
- [`/jail`](jail.md) - Restriction to a specific channel (alternative to timeout).
- [`/cases`](cases.md) - View moderation history.
