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

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the poll ban (positional). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for the poll restriction, logged in the moderation case and included in the DM notification. In the prefix command, this is a positional flag.

- **Type:** String
- **Default:** "No reason provided"

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

## Response

When executed successfully, Tux will:

1. Update its internal database to mark the user as poll-banned.
2. Attempt to DM the user informing them they can no longer create polls (unless `-silent` is used).
3. Create a new moderation case for the poll ban.
4. Post a confirmation message in the current channel.
5. Log the action in the designated moderation log channel.

## Error Handling

### Common Errors

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than what's required to use this command.

**Solution:** Contact a server administrator to check your rank.

#### Error: User Already Poll Banned

**When it occurs:** The target user is already restricted from creating polls.

**Solution:** No action needed, or use [`/pollunban`](pollunban.md) to restore their access.

## Related Commands

- [`/pollunban`](pollunban.md) - Restore a member's ability to create polls.
- [`/cases`](cases.md) - View the moderation history for poll bans.
