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
```

**Aliases:**

- `unafk`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member whose AFK status should be cleared. |

## How It Works

When a user sets themselves as AFK using Tux, the bot:

1. Records their original nickname.
2. Updates their nickname to include "[AFK]" (depending on server config).
3. Optionally timeouts the user (self-timeout) if enforced AFK is used.

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

## Response

Upon successful execution, Tux will return an ephemeral confirmation message:
> "AFK status for @user has been cleared."

## Error Handling

### Common Errors

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than what's required to use this command.

**Solution:** Contact a server administrator to check your rank.

#### Error: User Not AFK

**When it occurs:** You attempt to clear the AFK status of a user who is not currently marked as AFK in the bot's system.

**Solution:** No action needed.

#### Error: Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Manage Nicknames" or "Moderate Members" permission, or the target user has a higher role than the bot.

**Solution:** The status is cleared in the database, but nickname/timeout restoration may fail. Ensure Tux has the correct permissions and its role is high in the hierarchy.

## Related Commands

- [`/afk`](../utility/afk.md) - Set your own AFK status.
