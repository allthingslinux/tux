---
title: Jail
description: Restrict a member to a specific jail channel
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Jail

The `jail` command is a powerful moderation tool that isolates a member from the rest of the server. When applied, Tux removes the member's existing roles (storing them for later restoration) and assigns a specialized "Jail" role.

Typically, the Jail role is configured to deny access to all server channels except for a designated "jail" channel where the member can communicate with moderators to resolve the issue.

## Syntax

The `jail` command can be used in two ways:

**Slash Command:**

```text
/jail member:@user [reason:STRING] [silent:true/false]
```

**Prefix Command:**

```text
$jail @user [reason] [-silent]
$j @user [reason] [-silent]
```

**Aliases:**

You can also use these aliases instead of `jail`:

- `j`

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member` | Member | Yes | The member to jail. |
| `reason` | String | No | The reason for the jail, logged in the moderation case and included in the DM notification. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". |

## Flags

This command supports the following flags:

| Flag | Aliases | Type | Default | Description |
|------|---------|------|---------|-------------|
| `-silent` | `-s`, `-quiet` | Boolean | False | If true, Tux will not attempt to DM the user. |

### -silent

Whether to suppress the DM notification to the jailed user.

- **Type:** Boolean
- **Default:** False
- **Aliases:** `-s`, `-quiet`

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Manage Roles** - Required to remove existing roles and add the jail role.

### User Permissions

Users need appropriate moderation permissions to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Configuration

Jail behavior relies on guild-specific configuration:

- **Jail Role:** The role assigned to jailed members.
- **Jail Channel:** The channel jailed members are restricted to.

!!! info "Admin Setup"
    Administrators must set the jail channel and jail role with `/config jail` (or the Configuration Dashboard) before this command can be used. See [Jail Configuration](../../../admin/config/jail.md).

## Usage Examples

### Basic Jail (Slash)

Jailing a member for a rule violation.

```text
/jail member:@user reason:"Investigation into spamming"
```

### Prefix Usage

```text
$jail @user Inappropriate behavior in voice chat
```

## Response Format

When executed successfully, Tux will:

1. Fetch and store the member's current manageable roles.
2. Add the designated Jail role to the member.
3. Remove all other manageable roles from the member.
4. Attempt to DM the user with the jail reason (unless `-silent` is used).
5. Create a new moderation case (storing role IDs for unjailing).
6. Post a confirmation message in the current channel showing the jail details.
7. Log the action in the designated moderation log channel.

The confirmation message includes the jailed user's name, the reason, and a link to view the moderation case. The stored roles are automatically restored when using `/unjail`.

### Re-jail on rejoin

If a jailed member leaves the server and rejoins before being unjailed, Tux automatically re-applies the jail (adds the Jail role and strips any roles they gained on rejoin). No new case is created and no DM is sent. Use `/unjail` when you are ready to release them.

## Error Handling

### Common Errors

#### Missing Permissions / Higher Role

**When it occurs:** Tux lacks the "Manage Roles" permission, or the target user's highest role is equal to or higher than Tux's highest role.

**What happens:** The bot sends an error message indicating insufficient permissions.

**Solutions:**

- Ensure Tux has the "Manage Roles" permission
- Move the "Tux" role above the target's role in the server hierarchy
- Check that Tux's role has the necessary permissions in the server settings

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than the rank required to use this command.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your rank
- Adjust the command configurations via `/config commands` if you have admin access

#### Error: No Jail Role/Channel Found

**When it occurs:** The guild has not set a jail role or jail channel (use `/config jail`).

**Solution:** Ask a server administrator to configure these settings via Tux's configuration module.

#### Member Already Jailed

**When it occurs:** The target user already has the jail role or an active jail case.

**What happens:** The bot sends an error message indicating the member is already jailed.

**Solutions:**

- Use [`/unjail`](unjail.md) if you wish to release them
- Check the existing jail case using `/cases search user:@user type:jail`

## Related Commands

- [`/unjail`](unjail.md) - Restore a jailed member's roles and remove the jail restriction
- [`/timeout`](timeout.md) - A lighter alternative that doesn't involve role removal
- [`/cases`](cases.md) - View the details of a jail case
