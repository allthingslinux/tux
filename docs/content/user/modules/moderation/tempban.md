---
title: Tempban
description: Temporarily ban members from your Discord server with automatic unban
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Tempban

The `tempban` command allows server moderators to ban a member from the server for a specific period of time. Once the duration expires, Tux will automatically unban the user, allowing them to rejoin the server.

This command is useful for "cooling off" periods or mid-level rule violations where a permanent ban is too severe but a simple kick or timeout isn't enough.

## Syntax

The `tempban` command can be used in two ways:

**Slash Command:**

```text
/tempban member:@user reason:STRING duration:TIME [purge:0-7] [silent:true/false]
```

**Prefix Command:**

```text
$tempban @user -duration TIME [reason] [-purge X] [-silent]
```

**Aliases:**

- `tb`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to temporarily ban from the server. |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the ban (positional). |
| `-duration` | Time | **Required** | Length of the ban (e.g., `1d`, `12h`). |
| `-purge` | Integer (0-7) | 0 | Number of days of message history to delete. |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for the temporary ban. In the prefix command, this is a positional flag. In slash commands, it is a standard argument.

- **Type:** String
- **Default:** "No reason provided"
- **Examples:** `Repeated spamming after warns`, `Temporary suspension for investigation`

### -duration

The length of time the user should be banned. Tux uses a standard time format (numbers followed by s, m, h, or d).

- **Type:** Time String
- **Format:** Combined units like `1d12h` or single units like `7d`.
- **Aliases:** `-t`, `-d`, `-e`

### -purge

The number of days of message history to delete for the banned user.

- **Type:** Integer
- **Range:** 0 to 7
- **Default:** 0
- **Aliases:** `-p`

### -silent

Whether to suppress the DM notification to the banned user.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Ban Members** - Required to perform the initial ban and the final unban.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Tempban

Banning a user for 24 hours.

```text
/tempban member:@user reason:"24h suspension" duration:1d
```

### With Reason and Purge (Prefix)

Banning a user for 1 week, deleting their last 7 days of messages, with a reason.

```text
$tempban @user -duration 7d -purge 7 Toxic behavior and spamming
```

### Complex Duration (Slash)

Banning a user for 2 days and 6 hours.

```text
/tempban member:@user reason:"Cooling off period" duration:2d6h
```

### Silent Tempban

Banning a user for 1 hour without a DM notification.

```text
$tempban @user -duration 1h -silent
```

## Response

When executed successfully, Tux will:

1. Attempt to DM the user with the ban duration and reason (unless `-silent` is used).
2. Execute the ban on the Discord server.
3. Create a moderation case with a set expiration time.
4. Log the action in the designated moderation log channel.
5. Automatically unban the user when the time expires.

## Error Handling

### Common Errors

#### Error: Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Ban Members" permission, or the target user's highest role is equal to or higher than Tux's highest role.

**Solution:** Ensure Tux has the "Ban Members" permission. Move the "Tux" role above the target's role in the server hierarchy.

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command in this server.

**Solution:** Contact a server administrator to check your current rank or adjust the configuration.

#### Error: Invalid Duration

**When it occurs:** The provided duration string doesn't match the expected format (e.g., `1 year` instead of `365d`).

**Solution:** Use digits followed by s, m, h, or d (e.g., `1h30m`).

#### Error: Member Not Found

**When it occurs:** The user is not in the server or the mention/ID is invalid.

**Solution:** Ensure you are mentioning a valid member currently in the guild.

## Related Commands

- [`/ban`](ban.md) - Permanent ban without automatic expiration.
- [`/unban`](unban.md) - Manually unban a user.
- [`/timeout`](timeout.md) - Temporarily restrict a user's ability to communicate without removing them from the server.
