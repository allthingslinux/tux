---
title: SnippetBan
description: Prevent a member from creating snippets
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# SnippetBan

The `snippetban` command (also available as `sb`) allows server moderators to restrict a member's ability to use Tux's snippet creation and management features. This is useful for dealing with members who abuse snippets by creating duplicates, irrelevant content, or violating server rules through snippets.

## Syntax

The `snippetban` command can be used in two ways:

**Slash Command:**

```text
/snippetban member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$snippetban @user [reason] [-silent]
```

**Aliases:**

- `sb`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to restrict from using snippets. |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the snippet ban (positional). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for the snippet restriction, logged in the moderation case and included in the DM notification. In the prefix command, this is a positional flag. In slash commands, it is a standard argument.

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

### Basic Snippet Ban

Preventing a member from creating snippets.

```text
/snippetban member:@user reason:"Spamming"
```

### With Reason

```text
$snippetban @user Creation of multiple spam snippets
```

## Response Format

When executed successfully, Tux will:

1. Update its internal database to mark the user as snippet-banned.
2. Attempt to DM the user informing them they can no longer create or manage snippets (unless `-silent` is used).
3. Create a new moderation case for the snippet ban.
4. Post a confirmation message in the current channel showing the snippet ban details.
5. Log the action in the designated moderation log channel.

The confirmation message includes the snippet-banned user's name, the reason, and a link to view the moderation case. The user will receive an error message if they attempt to use snippet commands while snippet-banned.

## Error Handling

### Common Errors

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than what's required to use this command.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### User Already Snippet Banned

**When it occurs:** The target user is already restricted from creating snippets.

**What happens:** The bot sends an error message indicating the user is already snippet-banned.

**Solutions:**

- No action needed - the user is already snippet-banned
- Use [`/snippetunban`](snippetunban.md) to restore their access if needed
- Check the existing snippet ban case using `/cases search user:@user`

## Related Commands

- [`/snippetunban`](snippetunban.md) - Restore a member's ability to create snippets
- [`/cases`](cases.md) - View the moderation history for snippet bans
- [`$createsnippet`](../snippets/createsnippet.md) - The snippet command that is restricted by this ban
