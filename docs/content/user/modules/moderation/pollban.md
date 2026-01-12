---
title: PollBan
description: Prevent a member from creating polls
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# PollBan

The `pollban` command (also available as `pb`) allows server moderators to restrict a member's ability to use Tux's poll creation features. This is useful for dealing with members who misuse the poll system for spam or inappropriate content.

## Syntax

The `pollban` command can be used in two ways:

**Slash Command:**

```text
/pollban member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$pollban @user [reason] [-silent]
```

**Aliases:**

- `pb`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to restrict from using polls. |
| `reason` | String | No | The reason for the poll restriction, logged in the moderation case and included in the DM notification. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### -silent

Whether to suppress the DM notification to the restricted user.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## Permissions

### Bot Permissions

Tux requires no special Discord permissions for this command, as it is handled internally via its database.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Poll Ban

Preventing a member from creating polls.

```text
/pollban member:@user reason:"Spamming"
```

### With Reason

```text
$pollban @user Repeatedly creating joke polls in #serious-discussion
```

## Response Format

When executed successfully, Tux will:

1. Update its internal database to mark the user as poll-banned.
2. Attempt to DM the user informing them they can no longer create polls (unless `-silent` is used).
3. Create a new moderation case for the poll ban.
4. Post a confirmation message in the current channel showing the poll ban details.
5. Log the action in the designated moderation log channel.

The confirmation message includes the poll-banned user's name, the reason, and a link to view the moderation case. The user will receive an error message if they attempt to use `/poll` while poll-banned.

## Error Handling

### Common Errors

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than what's required to use this command.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### User Already Poll Banned

**When it occurs:** The target user is already restricted from creating polls.

**What happens:** The bot sends an error message indicating the user is already poll-banned.

**Solutions:**

- No action needed - the user is already poll-banned
- Use [`/pollunban`](pollunban.md) to restore their access if needed
- Check the existing poll ban case using `/cases search user:@user`

## Related Commands

- [`/pollunban`](pollunban.md) - Restore a member's ability to create polls
- [`/cases`](cases.md) - View the moderation history for poll bans
- [`/poll`](../utility/poll.md) - The poll command that is restricted by this ban
