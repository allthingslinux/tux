---
title: PollUnban
description: Restore a member's ability to create polls
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# PollUnban

The `pollunban` command (also available as `pub`) allows server moderators to lift a previously applied poll restriction from a member, restoring their ability to use Tux's poll creation features.

## Syntax

The `pollunban` command can be used in two ways:

**Slash Command:**

```text
/pollunban member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$pollunban @user [reason] [-silent]
```

**Aliases:**

- `pub`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to restore poll access for. |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the poll unban (positional). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for restoring poll access, logged in the moderation case and included in the DM notification. In the prefix command, this is a positional flag. In slash commands, it is a standard argument.

- **Type:** String
- **Default:** "No reason provided"

### -silent

Whether to suppress the DM notification to the user.

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

### Basic Poll Unban

Restoring poll access for a member.

```text
/pollunban member:@user reason:"Manual release"
```

### With Reason

```text
$pollunban @user Behavior improved, restriction lifted
```

## Response Format

When executed successfully, Tux will:

1. Update its internal database to remove the poll ban for the user.
2. Attempt to DM the user informing them they can once again create polls (unless `-silent` is used).
3. Create a new moderation case for the poll unban.
4. Post a confirmation message in the current channel showing the poll unban details.
5. Log the action in the designated moderation log channel.

The confirmation message includes the poll-unbanned user's name, the reason (if provided), and a link to view the moderation case.

## Error Handling

### Common Errors

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than what's required to use this command.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### User Not Poll Banned

**When it occurs:** You attempt to unban a user who does not have an active poll restriction.

**What happens:** The bot sends an error message indicating the user is not currently poll-banned.

**Solutions:**

- No action needed - the user is already not poll-banned
- Verify the user's poll ban status using `/cases search user:@user`

## Related Commands

- [`/pollban`](pollban.md) - Prevent a member from creating polls
- [`/cases`](cases.md) - View the moderation history for poll bans
- [`/poll`](../utility/poll.md) - The poll command that is restored by this unban
