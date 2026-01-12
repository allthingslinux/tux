---
title: ClearAFK
description: Manually clear a member's AFK status
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# ClearAFK

The `clearafk` command (also available as `unafk`) allows server moderators to manually remove a member's AFK status. This is useful if a user becomes active but the automatic AFK removal fails, or if a moderator needs to reset a user's nickname back to its original state after they set an AFK message.

## Syntax

The `clearafk` command can be used in two ways:

**Slash Command:**

```text
/clearafk member:@user
```

**Prefix Command:**

```text
$clearafk @user
$unafk @user
```

**Aliases:**

You can also use these aliases instead of `clearafk`:

- `unafk`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member whose AFK status should be cleared. |

## How It Works

When a user sets themselves as AFK using Tux, the bot:

1. Records their original nickname.
2. Updates their nickname to include "[AFK]" (depending on server config).
3. Optionally times out the user (self-timeout) if enforced AFK is used.

The `clearafk` command reverses all these actions:

- Removes the AFK entry from the database.
- Attempts to restore the member's original nickname.
- Removes any self-timeout resulting from enforced AFK.

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Manage Nicknames** - Required to restore the user's original nickname.
- **Moderate Members** - Required to remove self-timeouts.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Clear AFK

```text
/clearafk member:@user
```

## Response Format

Upon successful execution, Tux will return an ephemeral confirmation message:
> "AFK status for @user has been cleared."

The command removes the AFK entry from the database, restores the member's original nickname (if it was modified), and removes any self-timeout resulting from enforced AFK.

## Error Handling

### Common Errors

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than what's required to use this command.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### User Not AFK

**When it occurs:** You attempt to clear the AFK status of a user who is not currently marked as AFK in the bot's system.

**What happens:** The bot sends an error message indicating the user is not currently AFK.

**Solutions:**

- No action needed - the user is already not AFK
- Verify the user's AFK status by checking their profile or nickname

#### Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Manage Nicknames" or "Moderate Members" permission, or the target user has a higher role than the bot.

**What happens:** The status is cleared in the database, but nickname/timeout restoration may fail.

**Solutions:**

- Ensure Tux has the "Manage Nicknames" and "Moderate Members" permissions
- Move Tux's role higher in the server hierarchy
- Check that Tux's role has the necessary permissions in the server settings

## Related Commands

- [`/afk`](../utility/afk.md) - Set your own AFK status
