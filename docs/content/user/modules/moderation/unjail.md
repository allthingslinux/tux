---
title: Unjail
description: Remove a member from jail and restore their previous roles
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Unjail

The `unjail` command releases a member from isolation, removing the "Jail" role and restoring the previous roles they held before being jailed. Tux automatically tracks and stores a member's roles when they are jailed, making it easy to return them to their original state once the issue is resolved.

## Syntax

The `unjail` command can be used in two ways:

**Slash Command:**

```text
/unjail member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$unjail @user [reason] [-silent]
```

**Aliases:**

- `uj`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to release from jail. |

## Flags

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | String | No reason provided | The reason for the unjail (positional). |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### reason

The reason for releasing the user from jail, which is logged in the moderation case and included in the DM notification. In the prefix command, this is a positional flag. In slash commands, it is a standard argument.

- **Type:** String
- **Default:** "No reason provided"

### -silent

Whether to suppress the DM notification to the member being unjailed.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## permissions

### Bot Permissions

Tux requires the following permissions:

- **Manage Roles** - Required to remove the jail role and re-add previous roles.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

### Basic Unjail (Slash)

Releasing a member from jail.

```text
/unjail member:@user
```

### With Reason (Slash)

```text
/unjail member:@user reason:"Behavior improved"
```

### With Reason

```text
$unjail @user Investigation complete, rules explained
```

## Response

When executed successfully, Tux will:

1. Locate the latest jail case for the member in the database.
2. Remove the "Jail" role from the member.
3. Re-assign the roles stored in the jail case.
4. Attempt to DM the user with the unjail confirmation (unless `-silent` is used).
5. Create a new moderation case for the unjail action.
6. Post a confirmation message in the current channel.
7. Log the action in the designated moderation log channel.

## Error Handling

### Common Errors

#### Error: Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Manage Roles" permission.

**Solution:** Ensure Tux has the "Manage Roles" permission in the server settings.

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than required.

**Solution:** Contact an administrator to check your rank.

#### Error: No Jail Case Found

**When it occurs:** The bot cannot find a record of the user being jailed in its database.

**Solution:** You may need to manually restore the user's roles if they were jailed elsewhere or if the case was deleted.

#### Error: Member Not Jailed

**When it occurs:** The user does not have the "Jail" role.

**Solution:** No action needed.

#### Error: Roles Not Restored

**When it occurs:** Some roles may no longer exist, or Tux's highest role is now below those roles in the hierarchy.

**Solution:** Tux will log which roles could not be restored. Hand-assign any missing roles if necessary.

## Related Commands

- [`/jail`](jail.md) - Restrict a member to the jail channel and remove roles.
- [`/cases`](cases.md) - View the details of the original jail case.
