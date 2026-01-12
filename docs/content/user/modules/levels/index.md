---
title: Levels
description: Level and XP tracking system for Discord guilds
tags:
  - user-guide
  - modules
  - levels
  - xp
icon: lucide/medal
---

# Levels

The Levels module provides a comprehensive XP and leveling system for your Discord server. It tracks user activity through messages and automatically assigns roles based on their earned experience points, encouraging engagement and rewarding active community members.

This system includes automatic XP gain with configurable cooldowns, role rewards for hitting level milestones, and administrative tools to manage user progress or restrict leveling in specific areas.

## Command Groups

This module includes the following command groups:

### Levels (Admin)

The `/levels` command group provides administrative tools for managing member XP and leveling status. These commands are essential for resolving issues, rewarding specific users, or managing leveling restrictions.

**Commands:**

- `/levels set` - Set a member's level directly
- `/levels setxp` - Set a member's XP amount
- `/levels reset` - Reset a member's XP and level to zero
- `/levels blacklist` - Prevent a member from gaining XP

## Commands

| Command | Description | Documentation |
|---------|-------------|---------------|
| `/level` | View your current level and XP progress | [Details](level.md) |
| `/levels` | Administrative XP and level management | [Details](levels.md) |

## Common Use Cases

### Checking Ranking Progress

Members can check their standing in the server and see how much XP is needed for the next level.

**Steps:**

1. Use the `/level` command in any allowed channel.
2. View the progress bar and current XP stats in the resulting embed.

**Example:**

```text
/level
/level member:@user
```

### Manual Level Adjustments

Administrators can manually adjust a user's level or XP to correct errors or provide rewards.

**Steps:**

1. Use `/levels set` to set a specific level (which automatically calculates and sets the required XP).
2. Use `/levels setxp` for precise XP adjustments (which automatically recalculates the level).
3. The bot automatically updates the user's roles to match their new level.

**Example:**

```text
/levels set member:@user new_level:10
/levels setxp member:@user xp_amount:5000
```

## Configuration

This module requires the following configuration:

- **XP Roles:** Define which roles are awarded at specific levels.
- **XP Blacklist Channels:** Channels where message activity does not grant XP.
- **XP Cooldown:** Time between messages that grant XP to prevent spamming.

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../../admin/config/index.md).

## Permissions

### Bot Permissions

Tux requires the following permissions for this module:

- **Send Messages** - Required for command responses
- **Manage Roles** - Required to assign and remove level-based roles
- **Embed Links** - Required for rank cards and progress displays

### User Permissions

The `/level` command is available to all users. Administrative commands under `/levels` require Moderator rank (typically rank 3-5) or higher.

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

- [XP & Leveling Feature](../../../features/leveling.md) - Complete guide to the leveling system
- [Permission Configuration](../../../admin/config/commands.md)
- [Admin Configuration Guide](../../../admin/config/index.md)
