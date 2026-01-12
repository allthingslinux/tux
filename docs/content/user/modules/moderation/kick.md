---
title: Kick
description: Remove a member from your Discord server
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Kick

The `kick` command allows server moderators to remove a member from the server. Unlike a ban, a kicked user is free to rejoin immediately if they have a valid invite. This command is typically used for less severe rule violations or as a firm warning to a user whose behavior needs to change.

## Syntax

The `kick` command can be used in two ways:

**Slash Command:**

```text
/kick member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$kick @user [reason] [-silent]
```

**Aliases:**

- `k`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to kick from the server. |
| `reason` | String | No | The reason for the kick. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". Examples: `Inappropriate nickname`, `Disrupting the conversation` |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### -silent

Whether to suppress the DM notification to the kicked user.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Kick Members** - Required to remove the member from the server.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Kick

Kicking a user with no specified reason.

```text
/kick member:@user
```

### With Reason (Slash)

```text
/kick member:@user reason:"Disruptive behavior"
```

### With Reason (Prefix)

```text
$kick @user Refusal to change inappropriate avatar
```

### Silent Kick

Kicking a user without sending a DM notification.

```text
/kick member:@user reason:"Automated cleanup" silent:true
```

## Response Format

When executed successfully, Tux will:

1. Attempt to DM the user with the kick reason (unless `-silent` is used).
2. Execute the kick on the Discord server.
3. Create a new moderation case in the database.
4. Post a confirmation message in the current channel showing the kick details.
5. Log the action in the designated moderation log channel.

The confirmation message includes the kicked user's name, the reason, and a link to view the moderation case.

## Error Handling

### Common Errors

#### Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Kick Members" permission, or the target user's highest role is equal to or higher than Tux's highest role.

**What happens:** The bot sends an error message indicating insufficient permissions.

**Solutions:**

- Ensure Tux has the "Kick Members" permission
- Move the "Tux" role above the target's role in the server hierarchy
- Check that Tux's role has the necessary permissions in the server settings

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command in this server.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your current rank
- Adjust the command configurations via `/config commands` if you have admin access

#### Member Not Found

**When it occurs:** The provided mention or ID is invalid or they already left the server.

**What happens:** The bot sends an error message indicating the member could not be found.

**Solutions:**

- Ensure you are mentioning a valid member currently in the guild
- Double-check the user ID if using an ID instead of a mention
- Verify the member hasn't already left the server

## Related Commands

- [`/ban`](ban.md) - Permanently remove a member from the server
- [`/warn`](warn.md) - Issue a formal warning without removing the user
- [`/timeout`](timeout.md) - Temporarily restrict communication
