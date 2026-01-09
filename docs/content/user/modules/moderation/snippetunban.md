---
title: SnippetUnban
description: Restore a member's ability to create snippets
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# SnippetUnban

The `snippetunban` command (also available as `sub`) allows server moderators to lift a previously applied snippet restriction from a member, restoring their ability to use Tux's snippet creation and management features.

## Syntax

The `snippetunban` command can be used in two ways:

**Slash Command:**

```text
/snippetunban member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$snippetunban @user [reason] [-silent]
```

**Aliases:**

- `sub`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to restore snippet access for. |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the snippet unban (positional). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for restoring snippet access, logged in the moderation case and included in the DM notification. In the prefix command, this is a positional flag. In slash commands, it is a standard argument.

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

### Basic Snippet Unban

Restoring snippet access for a member.

```text
/snippetunban member:@user reason:"Manual release"
```

### With Reason

```text
$snippetunban @user Appealed successfully, access restored
```

## Response

When executed successfully, Tux will:

1. Update its internal database to remove the snippet ban for the user.
2. Attempt to DM the user informing them they can once again create and manage snippets (unless `-silent` is used).
3. Create a new moderation case for the snippet unban.
4. Post a confirmation message in the current channel.
5. Log the action in the designated moderation log channel.

## Error Handling

### Common Errors

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than what's required to use this command.

**Solution:** Contact a server administrator to check your rank.

#### Error: User Not Snippet Banned

**When it occurs:** You attempt to unban a user who does not have an active snippet restriction.

**Solution:** No action needed.

## Related Commands

- [`/snippetban`](snippetban.md) - Prevent a member from creating snippets.
- [`/cases`](cases.md) - View the moderation history for snippet bans.
