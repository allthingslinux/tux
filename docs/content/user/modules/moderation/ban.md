---
title: Ban
description: Ban members from your Discord server with optional message deletion
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Ban

The `ban` command allows server moderators to permanently remove members from the server. Banned members cannot rejoin the server unless they are explicitly unbanned. This command is intended for severe rule violations or users who are no longer welcome in the community.

When a user is banned, Tux can optionally delete their recent message history from the server, helping to quickly clean up spam or offensive content. By default, the bot will attempt to DM the user with the reason for their ban before executing the action.

## Syntax

The `ban` command can be used in two ways:

**Slash Command:**

```text
/ban member:@user [reason:STRING] [purge:0-7] [silent:true/false]
```

**Prefix Command:**

```text
$ban @user [reason] [-purge X] [-silent]
$b @user [reason] [-purge X] [-silent]
```

**Aliases:**

You can also use these aliases instead of `ban`:

- `b`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member/User | Yes | The member or user ID to ban from the server. |
| `reason` | String | No | The reason for the ban. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". Examples: `Spamming`, `Violation of Rule 1` |

## Flags

This command supports the following flags:

| Flag | Aliases | Type | Default | Description |
|------|---------|------|---------|-------------|
| `-purge` | `-p` | Integer (0-7) | 0 | Number of days of message history to delete. |
| `-silent` | `-s`, `-quiet` | Boolean | False | If true, Tux will not attempt to DM the user. |

### -purge

The number of days of message history to delete for the banned user. Discord allows a maximum of 7 days.

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

Tux requires the following permissions to execute this command:

- **Ban Members** - Required to perform the ban action on Discord.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Usage

Banning a user with a minimal reason.

```text
/ban member:@user reason:"Unspecified violation"
```

### With Reason (Slash)

```text
/ban member:@user reason:"Repeated harassment"
```

### With Reason (Prefix)

```text
$ban @user Repeated harassment after multiple warnings
```

### With Message Purge

Banning a user and deleting their last 3 days of messages.

```text
/ban member:@user reason:"Spam bot cleanup" purge:3
```

### Silent Ban

Banning a user without sending a DM notification to them.

```text
$ban @user -silent Severe rule breakage
```

## Response Format

When executed successfully, Tux will:

1. Attempt to DM the user with the ban reason (unless `-silent` is used).
2. Execute the ban on the Discord server.
3. Create a new moderation case in the database.
4. Post a confirmation message in the current channel showing the ban details.
5. Log the action in the designated moderation log channel.

The confirmation message includes the banned user's name, the reason, and a link to view the moderation case.

## Error Handling

### Common Errors

#### Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Ban Members" permission, or the target user's highest role is equal to or higher than Tux's highest role.

**What happens:** The bot sends an error message indicating insufficient permissions.

**Solutions:**

- Ensure Tux has the "Ban Members" permission in its role settings
- Move the "Tux" role above the role of the person you are trying to ban in the server hierarchy
- Check that Tux's role has the necessary permissions in the server settings

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use the ban command in this server.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your current rank
- Adjust the command configurations via `/config commands` if you have admin access

#### User Not Found

**When it occurs:** The provided mention or ID does not resolve to a valid Discord user.

**What happens:** The bot sends an error message indicating the user could not be found.

**Solutions:**

- Double-check the ID (ensure it is a 17-19 digit Snowflake)
- Mention the user directly using `@username`
- Verify the user is still in the server (for members) or exists (for users)

## Related Commands

- [`/unban`](unban.md) - Reinstates a previously banned member's ability to join.
- [`/tempban`](tempban.md) - Bans a member for a specified duration.
- [`/kick`](kick.md) - Removes a member without a permanent ban.
- [`/cases`](cases.md) - View and manage moderation history.
