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

## Permissions

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

## Response Format

When executed successfully, Tux will:

1. Locate the latest jail case for the member in the database.
2. Remove the "Jail" role from the member.
3. Re-assign the roles stored in the jail case.
4. Attempt to DM the user with the unjail confirmation (unless `-silent` is used).
5. Create a new moderation case for the unjail action.
6. Post a confirmation message in the current channel showing the unjail details.
7. Log the action in the designated moderation log channel.

The confirmation message includes the unjailed user's name, the reason (if provided), and a link to view the moderation case. All roles that were stored when the user was jailed are automatically restored.

## Error Handling

### Common Errors

#### Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Manage Roles" permission, or the target user's highest role is equal to or higher than Tux's highest role.

**What happens:** The bot sends an error message indicating insufficient permissions.

**Solutions:**

- Ensure Tux has the "Manage Roles" permission in the server settings
- Move Tux's role above the target's role in the server hierarchy
- Check that Tux's role has the necessary permissions in the server settings

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than required.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### No Jail Case Found

**When it occurs:** The bot cannot find a record of the user being jailed in its database.

**What happens:** The bot sends an error message indicating no jail case was found for the user.

**Solutions:**

- You may need to manually restore the user's roles if they were jailed elsewhere or if the case was deleted
- Check if the user was jailed using a different bot or method
- Use `/cases search user:@user type:jail` to verify if a jail case exists

#### Member Not Jailed

**When it occurs:** The user does not have the "Jail" role.

**What happens:** The bot sends an error message indicating the member is not currently jailed.

**Solutions:**

- No action needed - the user is already not jailed
- Verify the user's jail status by checking their roles or using `/cases search user:@user type:jail`

#### Roles Not Restored

**When it occurs:** Some roles may no longer exist, or Tux's highest role is now below those roles in the hierarchy.

**What happens:** The unjail succeeds, but some roles cannot be restored. Tux logs which roles could not be restored.

**Solutions:**

- Tux will log which roles could not be restored - check the moderation log channel
- Hand-assign any missing roles if necessary
- Ensure Tux's role is high enough in the hierarchy to manage the roles that need to be restored
- Verify that the roles still exist in the server

## Related Commands

- [`/jail`](jail.md) - Restrict a member to the jail channel and remove roles
- [`/cases`](cases.md) - View the details of the original jail case
