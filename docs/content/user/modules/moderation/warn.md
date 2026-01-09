---
title: Warn
description: Issue a formal warning to a member
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Warn

<!-- markdownlint-disable MD013 -->
The `warn` command allows server moderators to issue a formal warning to a member. While this command doesn't restrict the user's access to the server, it creates a permanent moderation case in Tux's database. This allows moderators to track a user's behavior over time and take more severe actions if rules are repeatedly broken.

## Syntax

The `warn` command can be used in two ways:

**Slash Command:**

```text
/warn member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$warn @user [reason] [-silent]
```

**Aliases:**

- `w`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to issue a warning to. |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the warning (positional). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for the warning. In the prefix command, this is a positional flag. In slash commands, it is a standard argument.

- **Type:** String
- **Default:** "No reason provided"
- **Examples:** `Minor spamming`, `Inappropriate language in #general`

### -silent

Whether to suppress the DM notification to the warned user. The warning is still logged in the database.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Send Messages** - To confirm the warning and log it.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Warning (Slash)

Issuing a warning with a simple reason.

```text
/warn member:@user reason:"Please stop tagging everyone"
```

### Prefix Usage

```text
$warn @user Rule 4 violation
```

### Silent Warning

Logging a warning without notifying the user.

```text
/warn member:@user reason:"Internal note on behavior" silent:true
```

## Response

When executed successfully, Tux will:

1. Attempt to DM the user with the warning reason (unless `-silent` is used).
2. Create a new moderation case in the database.
3. Post a confirmation message in the current channel.
4. Log the action in the designated moderation log channel.

## Error Handling

### Common Errors

#### Error: Member Not Found

**When it occurs:** The provided mention or ID is invalid.

**Solution:** Ensure you are mentioning a valid member currently in the guild.

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command.

**Solution:** Contact a server administrator to check your rank.

#### Error: Cannot DM User

**When it occurs:** Tux is unable to send a DM to the user (e.g., they have DMs disabled) and `-silent` was not used.

**Solution:** The warning is still recorded in the database, but the user will not receive the notification.

## Related Commands

- [`/kick`](kick.md) - Remove a member from the server.
- [`/timeout`](timeout.md) - Temporarily restrict communication.
- [`/cases`](cases.md) - View a user's full warning and moderation history.
