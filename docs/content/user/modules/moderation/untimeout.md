---
title: Untimeout
description: Remove an active timeout from a member
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Untimeout

The `untimeout` command (also available as `unmute`) allows server moderators to lift an active Discord timeout from a member before it naturally expires. This restores the member's ability to send messages and participate in the community immediately.

## Syntax

The `untimeout` command can be used in two ways:

**Slash Command:**

```text
/untimeout member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$untimeout @user [reason] [-silent]
```

**Aliases:**

- `uto`
- `unmute`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to remove the timeout from. |
| `reason` | String | No | The reason for lifting the timeout early, logged in the moderation case and included in the DM notification. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### -silent

Whether to suppress the DM notification to the user being untimed out.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Moderate Members** - Required to remove the Discord timeout.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Untimeout (Slash)

Removing a timeout from a member.

```text
/untimeout member:@user reason:"Manual release"
```

### With Reason (Slash)

```text
/untimeout member:@user reason:"Good behavior"
```

### With Reason

```text
$untimeout @user Early release after appeal
```

## Response Format

When executed successfully, Tux will:

1. Attempt to DM the user stating their timeout has been lifted (unless `-silent` is used).
2. Remove the official Discord timeout restriction.
3. Create a new moderation case in the database.
4. Post a confirmation message in the current channel showing the untimeout details.
5. Log the action in the designated moderation log channel.

The confirmation message includes the untimed-out user's name, the reason (if provided), and a link to view the moderation case.

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

#### User Not Timed Out

**When it occurs:** You attempt to untimeout a member who does not have an active timeout.

**What happens:** The bot sends an error message indicating the user is not currently timed out.

**Solutions:**

- No action needed - the user is already not timed out
- Verify the user's timeout status by checking their profile or using `/cases search user:@user type:timeout`

#### Member Not Found

**When it occurs:** The provided mention or ID is invalid.

**What happens:** The bot sends an error message indicating the member could not be found.

**Solutions:**

- Ensure you are mentioning a valid member currently in the guild
- Double-check the user ID if using an ID instead of a mention
- Verify the member hasn't already left the server

## Related Commands

- [`/timeout`](timeout.md) - Apply a temporary restriction to a member
- [`/cases`](cases.md) - View moderation history
