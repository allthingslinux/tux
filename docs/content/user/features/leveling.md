---
title: XP & Leveling
description: Earn experience points (XP) by chatting and level up to unlock roles and rewards.
tags:
  - user-guide
  - features
  - leveling
  - xp
---

# XP & Leveling

Earn XP by sending messages and automatically level up to unlock roles. Each message awards XP (with cooldown), and your level is calculated from total XP using an exponential formula.

## How It Works

- Messages in eligible channels award XP (respects cooldown)
- Role multipliers provide bonus XP
- Levels calculated automatically from total XP
- Roles assigned at configured milestones
- Channel and user blacklists supported

## User Experience

- XP awarded silently as you chat
- Use `/level` to view current level and progress
- Automatic role assignment when leveling up
- Multiplier roles gain XP faster

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `xp_cooldown` | `integer` | `1` | Seconds between XP gains |
| `levels_exponent` | `float` | `2` | Level calculation exponent |
| `xp_blacklist_channels` | `array` | `[]` | Channel IDs that don't award XP |
| `xp_roles` | `array` | `[]` | Roles assigned at specific levels |
| `xp_multipliers` | `array` | `[]` | Role-based XP multipliers |

### Example Configuration

```toml
[xp]
xp_cooldown = 1
levels_exponent = 1.75
xp_blacklist_channels = [123456789012345678]
xp_roles = [
    { level = 5, role_id = 111222333444555666 },
    { level = 10, role_id = 222333444555666777 },
    { level = 15, role_id = 333444555666777888 }
]
xp_multipliers = [
    { role_id = 555666777888999000, multiplier = 1.055 },  # Booster
    { role_id = 666777888999000111, multiplier = 1.1 }     # Contributor
]
```

## Commands

| Command | Description |
|---------|-------------|
| `/level` | View your current level and XP |
| `/level [user]` | View another user's level and XP |
| `/levels set` | Set a user's level (admin) |
| `/levels setxp` | Set a user's XP (admin) |
| `/levels reset` | Reset a user's XP and level (admin) |
| `/levels blacklist` | Toggle XP blacklist for a user (admin) |

## Permissions

**Bot Permissions:**

- Read Messages
- Manage Roles
- Send Messages

**User Permissions:** None required

## Troubleshooting

**Not gaining XP:**

- Check cooldown period between messages
- Verify channel isn't blacklisted
- Ensure you're not blacklisted

**Roles not assigned:**

- Verify Tux has "Manage Roles" permission
- Check role hierarchy (roles must be below Tux's highest role)
- Confirm XP roles are configured correctly

**Wrong XP amount:**

- Check role multipliers (only highest applies)
- Verify cooldown settings
- Ensure channel isn't blacklisted
