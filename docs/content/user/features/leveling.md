---
title: XP & Leveling
description: Earn experience points (XP) by chatting and level up to unlock roles and rewards.
tags:
  - user-guide
  - features
  - leveling
  - xp
icon: lucide/sparkles
---

# XP & Leveling

XP & Leveling is an engagement system that rewards active community members for their
participation. By sending messages in designated channels, users earn experience points (XP) that
contribute to their overall level. As users reach new milestones, Tux can automatically assign them
roles, creating a clear path for progression and recognition within the server.

The system is designed to be fair and resistant to spam, using a cooldown mechanism and configurable exponents to control the pace of leveling. It also supports multipliers, allowing you to reward specific groups like server boosters or contributors with faster progression.

## How It Works

### Mechanics

The leveling system tracks user activity and calculates levels based on total accumulated XP.

- **XP Calculation:** XP is awarded for each message sent, provided the user is not on cooldown.
- **Level Formula:** Your level is calculated from total XP using an exponential formula: `level = (total_xp / 100) ^ (1 / exponent)`.
- **Cooldowns:** To prevent spam, users only earn XP once every few seconds (configurable).
- **Multipliers:** Roles can be assigned multipliers (e.g., 1.1x) that increase the amount of XP earned per message.

### Automation

Tux handles the entire lifecycle of user progression:

- **Automatic Assignment:** When a user reaches a level milestone defined in the configuration, Tux instantly assigns the corresponding role.
- **Role Management:** The bot can be configured to manage these roles as users progress, ensuring they always have the correct rank.
- **Background Tracking:** All XP gains and level calculations happen in real-time as users chat.

### Triggers

The feature activates when:

- A user sends a message in a channel that is not blacklisted.
- A user's total XP reaches the threshold for the next level.

## User Experience

### What Users See

Leveling is designed to be rewarding but non-intrusive:

- **Silent Progression:** XP is awarded silently without notification messages.
- **Status Checks:** Users can check their current level and progress using the `/level` command.
- **Role Rewards:** New roles appear on the user's profile automatically as they reach level milestones.
- **Leaderboards:** Users can see how they rank against others using the `/levels` command.

### Interaction

Users interact with this feature by:

1. Chatting in the server's public channels.
2. Using `/level` to view their personal progress.
3. Using `/levels` to view the server leaderboard.

## Configuration

Leveling is configured through the server's `config.toml` file.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `xp_cooldown` | `integer` | `1` | Seconds required between messages to earn XP. |
| `levels_exponent` | `float` | `2.0` | The exponent used in the level calculation formula. |
| `xp_blacklist_channels` | `array` | `[]` | List of channel IDs where users cannot earn XP. |
| `xp_roles` | `array` | `[]` | List of level milestones and their associated role IDs. |
| `xp_multipliers` | `array` | `[]` | Role-based multipliers to boost XP gain. |

### Example Configuration

```toml
[xp]
xp_cooldown = 1
levels_exponent = 1.75
xp_blacklist_channels = [123456789012345678]

xp_roles = [
    { level = 5, role_id = 111222333444555666 },
    { level = 10, role_id = 222333444555666777 }
]

xp_multipliers = [
    { role_id = 555666777888999000, multiplier = 1.1 }  # 10% boost for this role
]
```

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../admin/config/index.md).

## Commands

This feature provides the following commands for users and administrators:

| Command | Description | Documentation |
|---------|-------------|---------------|
| `/level` | View your current level, XP, and progress. | [Details](../modules/levels/level.md) |
| `/levels` | View the server-wide XP leaderboard. | [Details](../modules/levels/levels.md) |
| `/levels set` | Set a user's level (Admin only). | [Details](../modules/levels/index.md) |
| `/levels reset` | Reset a user's XP and level (Admin only). | [Details](../modules/levels/index.md) |

## Permissions

### Bot Permissions

Tux requires the following permissions for this feature:

- **Read Messages** - Needed to track user activity.
- **Manage Roles** - Needed to assign roles at level milestones.
- **Send Messages** - Needed to respond to level and leaderboard commands.

### User Permissions

None required for basic usage. Administrator commands require appropriate permissions.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: Users are not gaining XP

**Symptoms:**

- The `/level` command shows no increase in XP after sending messages.

**Causes:**

- The channel is in the `xp_blacklist_channels` list.
- The user is sending messages faster than the `xp_cooldown` setting allows.
- The user has been manually blacklisted from the XP system.

**Solutions:**

1. Check the channel blacklist in your configuration.
2. Verify that the user is not sending messages during the cooldown period.
3. Use `/levels blacklist` to check the user's status.

### Issue: Roles are not being assigned

**Symptoms:**

- A user reaches a level milestone but does not receive the associated role.

**Causes:**

- Tux is missing the "Manage Roles" permission.
- The role to be assigned is positioned above Tux's highest role in the Discord settings.
- The `xp_roles` configuration has an incorrect role ID.

**Solutions:**

1. Ensure Tux has "Manage Roles" permission.
2. Move Tux's role above the leveling roles in the server hierarchy.
3. Double-check the role IDs in your `config.toml`.

## Limitations

- **Message Content:** XP is currently awarded per message, regardless of message length or content quality.
- **One Server Focus:** Leveling data is specific to each server and does not carry over between servers.
- **Role Hierarchy:** Tux cannot assign roles that are higher than its own role in the Discord hierarchy.

## Related Documentation

- [Levels Module](../modules/levels/index.md)
- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../../admin/config/commands.md)
