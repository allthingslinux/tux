---
title: Levels
description: Administrative XP and level management
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - levels
  - admin
---

# Levels

The `levels` command group provides administrative tools for managing member XP and leveling status. These commands allow moderators and administrators to manually adjust a user's progress, reset their leveling history, or restrict specific users from gaining XP.

This group is essential for resolving leveling disputes, rewarding activity, or managing server discipline in relation to the XP system.

## Base Command

The base `/levels` command serves as the entry point for administrative XP management.

**Syntax:**

```text
/levels
$levels
```

**Aliases:**

- `lvls`

When invoked without a subcommand, this command displays the help menu for the levels group.

## Subcommands

| Subcommand | Description | Usage |
|------------|-------------|-------|
| `set` | Set a member's level directly | `/levels set member:@User new_level:10` |
| `setxp` | Set a member's total XP points | `/levels setxp member:@User xp_amount:5000` |
| `reset` | Reset a member's XP and level to zero | `/levels reset member:@User` |
| `blacklist` | Prevent or allow a member to gain XP | `/levels blacklist member:@User` |

### Management Commands

#### set

Manually update a member's level. This automatically calculates and sets the XP required for that level and updates their roles based on the new level.

**Syntax:**

```text
/levels set member:USER new_level:INTEGER
$levels set <member> <new_level>
```

**Parameters:**

- `member` - The member to set the level for.
- `new_level` - The target level to assign.

Set a member's XP to a specific value. This automatically recalculates their level based on the new XP amount and updates their roles accordingly.

**Syntax:**

```text
/levels setxp member:USER xp_amount:INTEGER
$levels setxp <member> <xp_amount>
```

**Parameters:**

- `member` - The member to set XP for.
- `xp_amount` - The total XP value to assign.

#### reset

Completely reset a user's XP progress and level back to zero.

**Syntax:**

```text
/levels reset member:USER
$levels reset <member>
```

**Parameters:**

- `member` - The member whose progress will be wiped.

Toggle a member's ability to gain experience points. If blacklisted, the user will not receive XP from message activity. Use the command again to remove them from the blacklist.

**Syntax:**

```text
/levels blacklist member:USER
$levels blacklist <member>
```

**Parameters:**

- `member` - The member to toggle the XP blacklist for.

## Permissions

### Bot Permissions

Tux requires the following permissions for this command group:

- **Manage Roles** - Required to update level-based roles when levels are changed.
- **Embed Links** - To display confirmation status.

### User Permissions

Users need **Moderator** rank (typically rank 3-5) or higher to use commands in this group.

!!! note "Subcommand Permissions"
    All subcommands in the `/levels` group require high-level administrative permissions.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Configuration

This command group interacts with the XP configuration set by administrators.

- **XP Roles:** Determines which roles are assigned/removed during level changes.

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../../admin/config/index.md).

## Usage Examples

### Resetting a Spammer

If a user has gained XP through spamming, you can reset their progress.

```text
/levels reset member:@User
```

### Rewarding a Community Member

Grant a user a specific level for their contributions.

```text
/levels set member:@User new_level:20
```

## Related Documentation

- [`/level`](level.md) - View user-facing rank cards
- [XP & Leveling Feature](../../features/leveling.md) - Complete guide to the leveling system
- [Admin Configuration Guide](../../admin/config/index.md)
