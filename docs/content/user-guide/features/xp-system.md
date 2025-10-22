# XP & Leveling System

Tux features a comprehensive XP (experience points) and leveling system to engage your community.

## Overview

The XP system:

- Awards XP for sending messages
- Tracks user levels based on total XP
- Automatically assigns roles at certain levels
- Shows rankings and leaderboards
- Fully configurable per server

## How It Works

### Earning XP

Users earn XP by:

- **Sending messages** - Primary XP source
- **Bonus XP** - Multipliers for certain roles
- **Admin awards** - Manual XP grants

### XP Gain Rules

- ✅ Regular messages in channels
- ❌ Bot messages (bots don't gain XP)
- ❌ Command messages (messages starting with prefix)
- ❌ Messages in blacklisted channels
- ❌ Messages while on cooldown

### Cooldown

To prevent spam farming:

- Cooldown period between XP gains (configurable)
- Default: 60 seconds
- Messages during cooldown don't award XP

### XP Blacklist

Administrators can blacklist users from gaining XP:

```
/levels blacklist @user
```

Blacklisted users:

- Keep their current XP/level
- Don't gain new XP
- Useful for bots or inactive accounts

## Levels

### How Levels Work

XP accumulates and determines your level:

- More XP → Higher level
- Level calculation uses an exponent formula
- Each level requires more XP than the last

### Level Formula

XP required for level N:

```
XP = (Level ^ Exponent) * BaseXP
```

Default exponent: Configurable in server settings

### Viewing Levels

Check anyone's level and XP:

```
/level                              # Your level
/level @user                        # Someone's level
```

**Shows:**

- Current level
- Total XP
- XP to next level
- Server rank position
- Progress to next level

## Role Rewards

### Automatic Role Assignment

Configure roles to be automatically granted at certain levels:

```toml
[xp_config]
xp_roles = [
    { level = 5, role_id = 123456 },
    { level = 10, role_id = 789012 },
    { level = 25, role_id = 345678 },
]
```

When a user reaches the level, they automatically get the role!

### Role Management

- **Granted automatically** when level is reached
- **Removed automatically** if XP is reduced below level
- **Multiple roles** possible (one per level tier)
- **Customizable** levels and roles

## XP Multipliers

Some roles can have XP multipliers:

```toml
[xp_config]
xp_multipliers = [
    { role_id = 111222, multiplier = 1.5 },  # 50% bonus
    { role_id = 333444, multiplier = 2.0 },  # 2x XP
]
```

### Use Cases for Multipliers

- **Boost donors/supporters**
- **Reward active contributors**
- **Temporary event bonuses**
- **VIP/premium roles**

## Leaderboard & Rankings

### Server Rankings

Use `/level @user` to see rankings:

- **Rank Position** - Where you stand in the server
- **Total Members** - How many are ranked
- **Percentile** - Top X% of server

### Competitive Element

- Rankings are public (unless using DMs)
- Encourages activity and engagement
- Recognition for active members

## Configuration

### Required Setup

The XP system requires configuration:

1. **Enable XP** in config
2. **Set XP roles** for rewards
3. **Optional:** Set multipliers
4. **Optional:** Blacklist channels

### Configuration Example

```toml
[xp_config]
# XP Settings
xp_cooldown = 60                    # Seconds between XP gains
levels_exponent = 2.0               # Level difficulty curve
enable_xp_cap = true                # Cap at max configured level

# Role Rewards
xp_roles = [
    { level = 5, role_id = 1234567890 },
    { level = 10, role_id = 2345678901 },
    { level = 25, role_id = 3456789012 },
    { level = 50, role_id = 4567890123 },
]

# XP Multipliers
xp_multipliers = [
    { role_id = 5678901234, multiplier = 1.5 },
]

# Channel Blacklist
xp_blacklist_channels = [8901234567, 9012345678]
```

**See:** [Admin Guide - Features Configuration](../../admin-guide/configuration/features.md)

## Admin Management

### Setting XP/Levels

Administrators can directly manage user XP:

```
/levels set @user level:25          # Set level
/levels add @user xp:1000           # Add XP
/levels remove @user xp:500         # Remove XP
/levels reset @user                 # Reset to 0
```

**Permission:** Rank 5 (Administrator)

### Blacklisting

Prevent users from gaining XP:

```
/levels blacklist @user             # Toggle blacklist
```

**Use Cases:**

- Bots (prevent them from gaining XP)
- Inactive/left users
- Temporary XP freeze (not punishment)

## Best Practices

### Choosing Level Thresholds

✅ **Good progression:**

- Level 5: First reward (achievable quickly)
- Level 10: Active member recognition
- Level 25: Dedicated member
- Level 50: Veteran status
- Level 100: Legend

❌ **Avoid:**

- Too many roles (clutters server)
- Unachievable levels (discourages)
- Rewards too early (no progression)

### Role Rewards

- **Cosmetic roles** - Color roles, badges
- **Exclusive access** - Special channels for high levels
- **Perks** - Special permissions or features
- **Recognition** - Status and prestige

### Multipliers

- **Keep reasonable** - 1.5x to 2x max recommended
- **Reward support** - Donors, boosters
- **Temporary boosts** - Events, competitions
- **Don't break balance** - Everyone should be able to level

## Formulas & Calculations

### XP to Level

```python
level = int((xp / base_xp) ** (1 / exponent))
```

### Level to XP

```python
xp_required = (level ** exponent) * base_xp
```

### Next Level XP

```python
next_level_xp = ((current_level + 1) ** exponent) * base_xp
```

## Common Questions

### How much XP per message?

Base XP per message is configurable. Default is typically 15-25 XP per message.

### Can XP be transferred?

No, XP is tied to specific users in specific servers. It doesn't transfer between servers or users.

### Does XP persist if someone leaves?

Yes, XP is stored in the database. If they rejoin, their XP remains.

### Can I import XP from another bot?

Not automatically, but administrators can manually set levels with `/levels set`.

### Is there an XP cap?

Optional. You can enable `enable_xp_cap` to stop XP gain at the max configured level.

## Troubleshooting

### Not Gaining XP

**Causes:**

- On cooldown (sent message too soon)
- Blacklisted from XP
- Channel is blacklisted
- Using commands (commands don't award XP)

**Solutions:**

- Wait for cooldown to expire
- Check blacklist: ask admin
- Try different channel
- Send regular messages, not commands

### Roles Not Applying

**Causes:**

- XP roles not configured
- Role deleted from server
- Bot missing "Manage Roles" permission

**Solutions:**

- Configure XP_ROLES in config
- Recreate the role
- Grant bot permission

### Wrong XP Amount

**Causes:**

- Multiplier applied
- Admin manually adjusted
- Database migration issue

**Solutions:**

- Check if you have multiplier role
- Ask admin if they modified your XP
- Report if suspicious

## Tips

!!! tip "Active Participation"
    The best way to level up is genuine participation in conversations!

!!! tip "Cooldown Strategy"
    Sending quality messages is better than spam - cooldown prevents farming.

!!! tip "Check Progress"
    Use `/level` frequently to track your progress and see how much XP you need.

!!! warning "Don't Farm XP"
    Spamming messages to gain XP may result in moderation action. Engage naturally!

## Leaderboard Ideas

While Tux doesn't have a built-in leaderboard command yet, you can:

- Use `/level` to check rankings
- Create a dedicated channel to showcase top members
- Announce level milestones
- Host level-up competitions

## Related Commands

- **[Level Commands](../commands/levels.md)** - View and manage XP
- **[Configuration](../commands/config.md)** - Set up XP system

## Related Documentation

- **[Levels System Developer Docs](../../developer-guide/modules/levels-system.md)** - Technical implementation
- **[Admin Configuration](../../admin-guide/configuration/features.md)** - Configuring XP system

---

**Next:** Learn about [Starboard](starboard.md) for highlighting messages.
