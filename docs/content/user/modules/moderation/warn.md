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

The `warn` command allows server moderators to issue a formal warning to a member. While this command doesn't restrict the user's access to the server, it creates a permanent case in Tux's database. This allows moderators to track behavior over time and take more severe actions in the future if needed.

## Syntax

The `warn` command can be used in two ways:

**Slash Command:**

```text
/warn member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$warn @user [reason] [-silent]
$w @user [reason] [-silent]
```

**Aliases:**

You can also use these aliases instead of `warn`:

- `w`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to issue a warning to. |
| `reason` | String | No | The reason for the warning. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". Examples: `Minor spamming`, `Inappropriate language in #general` |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

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

## Response Format

When executed successfully, Tux will:

1. Attempt to DM the user with the warning reason (unless `-silent` is used).
2. Create a new moderation case in the database.
3. Post a confirmation message in the current channel showing the warning details.
4. Log the action in the designated moderation log channel.

The confirmation message includes the warned user's name, the reason, and a link to view the moderation case.

## Error Handling

### Common Errors

#### Member Not Found

**When it occurs:** The provided mention or ID is invalid.

**What happens:** The bot sends an error message indicating the member could not be found.

**Solutions:**

- Ensure you are mentioning a valid member currently in the guild
- Double-check the user ID if using an ID instead of a mention
- Verify the member hasn't already left the server

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### Cannot DM User

**When it occurs:** Tux is unable to send a DM to the user (e.g., they have DMs disabled) and `-silent` was not used.

**What happens:** The warning is still recorded in the database and the command succeeds, but the user will not receive the DM notification.

**Solutions:**

- The warning is still logged - no action needed
- Use the `-silent` flag if you know the user has DMs disabled
- Check the moderation log to confirm the warning was recorded

## Related Commands

- [`/kick`](kick.md) - Remove a member from the server
- [`/timeout`](timeout.md) - Temporarily restrict communication
- [`/cases`](cases.md) - View a user's full warning and moderation history
