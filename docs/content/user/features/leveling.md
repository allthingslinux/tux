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

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The XP & Leveling system rewards active community members with experience points for their messages. As you gain XP, you level up and can unlock special roles and rewards. This gamification system encourages engagement and recognizes active contributors.

## How It Works

### Earning XP

You earn XP automatically by:

- **Sending messages** in text channels
- **Active participation** in conversations
- **Regular engagement** with the community

### XP Gain Rules

XP is awarded based on:

- **Message activity** - Each message gives XP (with cooldown)
- **Role multipliers** - Certain roles give bonus XP
- **Channel restrictions** - Some channels don't award XP
- **Cooldown system** - Prevents spam farming

### Level Calculation

Your level is calculated from your total XP:

- **Exponential growth** - Higher levels require more XP
- **Automatic calculation** - Level updates as you gain XP
- **Progress tracking** - See how close you are to the next level

## Viewing Your Level

### Check Your Level

Use the `/level` command to see your current level and XP:

```text
/level
```

Or check another user's level:

```text
/level @username
```

### Level Display

The level command shows:

- **Current level** - Your current level number
- **Total XP** - Your accumulated experience points
- **Progress bar** - Visual progress to next level (if enabled)
- **XP required** - How much XP needed for next level

## Leveling Up

### Automatic Role Assignment

When you level up:

1. **Your level increases** automatically
2. **Roles are assigned** based on your new level
3. **Previous roles** may be removed (only highest level role kept)
4. **Progress resets** for the next level

### Role Rewards

Configure roles to be assigned at specific levels:

- **Level 5** → "Active Member" role
- **Level 10** → "Regular Contributor" role
- **Level 25** → "Veteran" role
- **Level 50** → "Elite Member" role

## XP Mechanics

### Cooldown System

To prevent spam farming:

- **Cooldown period** - Must wait between XP gains (default: 1 second)
- **Per-message basis** - Each message checked individually
- **Automatic enforcement** - No manual intervention needed

### XP Multiplier System

Certain roles can give bonus XP:

- **1.055x multiplier** - Small bonus (5.5% more XP) - Common for boosters
- **1.075x multiplier** - Moderate bonus (7.5% more XP) - Common for donors
- **1.1x multiplier** - Good bonus (10% more XP) - Common for contributors
- **1.2x multiplier** - Large bonus (20% more XP) - For special roles
- **Custom multipliers** - Configure any multiplier value per role

### Channel Blacklist

Some channels don't award XP:

- **Bot channels** - Commands don't give XP
- **Spam channels** - Prevent farming in specific channels
- **Admin channels** - Moderation channels excluded

### What Doesn't Give XP

XP is not awarded for:

- **Bot messages** - Bot accounts don't gain XP
- **Command messages** - Messages starting with bot prefix
- **Blacklisted channels** - Channels configured to exclude XP
- **Blacklisted users** - Users manually blacklisted from XP

## Commands

### User Commands

**View Level:**

```text
/level [user]
```

Shows your level or another user's level with XP and progress.

### Administrator Commands

**Set Level:**

```text
/levels set @user 10
```

Sets a user's level to a specific value. XP is automatically calculated.

**Set XP:**

```text
/levels setxp @user 5000
```

Sets a user's XP to a specific amount. Level is automatically calculated.

**Reset Progress:**

```text
/levels reset @user
```

Resets a user's XP and level to 0.

**Blacklist User:**

```text
/levels blacklist @user
```

Toggles XP blacklist for a user. Blacklisted users cannot gain XP.

## Configuration

The XP system is configured through your server's configuration file.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `xp_cooldown` | `integer` | `1` | Seconds between XP gains |
| `levels_exponent` | `float` | `2` | Exponent for level calculation (can be decimal like 1.75) |
| `xp_blacklist_channels` | `array` | `[]` | Channel IDs that don't award XP |
| `xp_roles` | `array` | `[]` | Roles assigned at specific levels |
| `xp_multipliers` | `array` | `[]` | Role-based XP multipliers |
| `show_xp_progress` | `boolean` | `true` | Show progress bar in level command |
| `enable_xp_cap` | `boolean` | `false` | Enable maximum level cap |

### Example Configuration

```toml
[xp]
# Cooldown between XP gains (seconds)
xp_cooldown = 1

# Level calculation exponent (1.75 makes leveling easier, 2.0 is default, 2.5+ is harder)
levels_exponent = 1.75

# Channels that don't award XP
xp_blacklist_channels = [123456789012345678]

# Roles assigned at specific levels (progression system)
xp_roles = [
    { level = 5, role_id = 111222333444555666 },   # Beginner role
    { level = 10, role_id = 222333444555666777 },  # Active member
    { level = 15, role_id = 333444555666777888 },  # Regular contributor
    { level = 20, role_id = 444555666777888999 }   # Veteran member
]

# Role-based XP multipliers (only highest multiplier applies)
xp_multipliers = [
    { role_id = 555666777888999000, multiplier = 1.055 },  # Booster (5.5% bonus)
    { role_id = 666777888999000111, multiplier = 1.075 },  # Donor (7.5% bonus)
    { role_id = 777888999000111222, multiplier = 1.1 },    # Contributor (10% bonus)
    { role_id = 888999000111222333, multiplier = 1.2 }     # Special role (20% bonus)
]

# Show progress bar in level command
show_xp_progress = true

# Enable maximum level cap
enable_xp_cap = false
```

## Level Calculation Formula

Levels are calculated using an exponential formula:

```text
XP Required = 500 × (Level / 5) ^ exponent
```

**Default (exponent = 2.0):**

- Level 1: 20 XP
- Level 5: 500 XP
- Level 10: 2,000 XP
- Level 25: 12,500 XP
- Level 50: 50,000 XP

**Easier progression (exponent = 1.75):**

- Level 1: 20 XP
- Level 5: 500 XP
- Level 10: 1,414 XP
- Level 25: 7,071 XP
- Level 50: 28,284 XP

**Harder progression (exponent = 2.5):**

- Level 1: 20 XP
- Level 5: 500 XP
- Level 10: 3,162 XP
- Level 25: 25,000 XP
- Level 50: 100,000 XP

Lower exponents (1.5-1.75) make leveling easier and more accessible. Higher exponents (2.5+) make higher levels significantly more challenging.

## Progress Tracking

### Progress Bar

When enabled, the level command shows a visual progress bar:

```text
▰▰▰▰▰▱▱▱▱▱ 1250/2500
```

- **Filled blocks** (▰) - Progress made
- **Empty blocks** (▱) - Progress remaining
- **Numbers** - Current XP / Required XP

### Level Progress

Track your progress:

- **Current XP** - XP within current level
- **Required XP** - XP needed for next level
- **Percentage** - Visual representation of progress
- **Total XP** - Your lifetime XP accumulation

## XP Cap

### Maximum Level

When XP cap is enabled:

- **Maximum level** - Highest level achievable
- **XP limit** - Maximum XP that can be earned
- **Role assignment** - Highest role assigned at max level
- **Display** - Shows "limit reached" in level command

### Benefits

XP cap provides:

- **Clear goals** - Maximum achievement level
- **Role management** - Prevents unlimited role assignment
- **Balance** - Keeps leveling competitive

## Role Management

### Automatic Assignment

Roles are assigned automatically:

- **On level up** - When you reach the required level
- **Highest role** - Only the highest qualifying role is kept
- **Previous roles** - Lower level roles are removed
- **Permission checks** - Tux must have permission to assign roles

### Role Configuration

Configure roles in your config:

```toml
xp_roles = [
    { level = 5, role_id = 123456789012345678 },
    { level = 10, role_id = 234567890123456789 },
    { level = 25, role_id = 345678901234567890 }
]
```

**Important:**

- Roles must be ordered by level (lowest to highest)
- Tux needs "Manage Roles" permission
- Role must be below Tux's highest role in hierarchy

## XP Multipliers

### Role-Based Bonuses

Give bonus XP to specific roles:

```toml
xp_multipliers = [
    { role_id = 123456789012345678, multiplier = 1.055 },  # Booster role
    { role_id = 234567890123456789, multiplier = 1.075 },  # Donor role
    { role_id = 345678901234567890, multiplier = 1.1 },    # Contributor role
    { role_id = 456789012345678901, multiplier = 1.2 }     # Special contributor
]
```

**Common multiplier values:**

- **1.05-1.06** - Small recognition (5-6% bonus)
- **1.075-1.08** - Moderate reward (7.5-8% bonus)
- **1.1** - Good reward (10% bonus)
- **1.15-1.2** - Significant reward (15-20% bonus)

### How Multipliers Work

- **Base XP** - Standard XP per message
- **Multiplier applied** - Highest multiplier from user's roles
- **Bonus XP** - Additional XP based on multiplier
- **Stacking** - Only highest multiplier applies (doesn't stack)

### Example

User with 1.1x multiplier role:

- Base XP: 10
- Multiplier: 1.1x
- Actual XP gained: 11

User with multiple multiplier roles (only highest applies):

- Has Booster (1.055x) and Contributor (1.1x) roles
- Only the highest multiplier (1.1x) is applied
- Base XP: 10
- Actual XP gained: 11 (not 11.55)

## Use Cases

### Community Engagement

Encourage active participation:

- **Reward activity** - Active members level up faster
- **Recognize contributors** - High levels show dedication
- **Gamification** - Makes participation fun and rewarding

### Role Progression

Create a progression system with milestone levels:

- **Level 5** → "Grublet" - New active member
- **Level 10** → "Terminal Tinkerer" - Regular contributor
- **Level 15** → "Daemon Wrangler" - Experienced member
- **Level 20** → "Penguin Prodigy" - Veteran member

This creates clear milestones every 5 levels, making progression feel rewarding and achievable.

### Special Rewards

Reward special roles:

- **Boosters** - Extra XP multiplier
- **Contributors** - Recognition through levels
- **Long-term members** - High levels show commitment

## Tips

!!! tip "Stay Active"
    Regular participation is key to leveling up. Engage in conversations and contribute to discussions.

!!! tip "Check Your Progress"
    Use `/level` regularly to track your progress and see how close you are to the next level.

!!! tip "Understand Multipliers"
    If you have roles with XP multipliers, you'll level up faster. Check with admins about available multiplier roles.

!!! tip "Respect Cooldowns"
    Don't spam messages trying to farm XP. The cooldown system prevents this, and spam may result in moderation action.

!!! warning "Channel Restrictions"
    Not all channels award XP. Check with admins which channels are included in the XP system.

!!! warning "Blacklist Status"
    If you're not gaining XP, you may be blacklisted. Contact admins if you believe this is an error.

## Troubleshooting

### Not Gaining XP

If you're not gaining XP:

1. **Check cooldown** - Wait a moment between messages
2. **Verify channel** - Make sure the channel awards XP
3. **Check blacklist** - You may be blacklisted (contact admins)
4. **Verify bot status** - Ensure Tux is online and functioning
5. **Check message type** - Commands don't give XP

### Level Not Updating

If your level isn't updating:

1. **Check XP gain** - Make sure you're actually gaining XP
2. **Verify calculation** - Level updates automatically with XP
3. **Check logs** - Admins can check bot logs for errors
4. **Wait a moment** - Updates happen in real-time but may have slight delay

### Roles Not Being Assigned

If roles aren't being assigned:

1. **Check permissions** - Tux needs "Manage Roles" permission
2. **Verify role hierarchy** - Role must be below Tux's highest role
3. **Check configuration** - Ensure XP roles are configured correctly
4. **Verify level** - Make sure you've reached the required level

### Wrong XP Amount

If XP seems incorrect:

1. **Check multipliers** - Verify your role multipliers
2. **Review cooldown** - Cooldown may affect XP gain rate
3. **Check blacklist** - Some channels don't award XP
4. **Verify calculation** - Contact admins to review XP calculation

## For Administrators

### Setup Best Practices

1. **Configure roles first** - Set up XP roles before enabling the system
2. **Set appropriate cooldown** - Balance between engagement and spam prevention
3. **Choose channels wisely** - Exclude bot channels and spam channels
4. **Test thoroughly** - Test XP gain and role assignment before going live

### Setting Up XP Roles

When configuring XP roles:

- **Order matters** - List roles from lowest to highest level
- **Role hierarchy** - Ensure roles are positioned correctly
- **Permissions** - Tux needs permission to assign all roles
- **Testing** - Test role assignment at each level

### Multiplier Design

When setting multipliers:

- **Balance** - Don't make multipliers too high (1.5-2x is reasonable)
- **Purpose** - Use multipliers to reward specific roles (boosters, contributors)
- **Fairness** - Consider impact on leveling balance

### Monitoring

Regular monitoring tasks:

- **Review XP gain** - Check that users are gaining XP correctly
- **Monitor role assignments** - Verify roles are being assigned properly
- **Check blacklists** - Review blacklisted users and channels
- **Adjust configuration** - Fine-tune based on community feedback

### Common Configurations

**Small Server (50-200 members):**

```toml
xp_cooldown = 1
levels_exponent = 1.75  # Easier progression for smaller communities
xp_roles = [
    { level = 5, role_id = ... },   # First milestone
    { level = 10, role_id = ... },  # Active member
    { level = 15, role_id = ... },  # Regular contributor
    { level = 20, role_id = ... }   # Veteran member
]
xp_multipliers = [
    { role_id = ..., multiplier = 1.055 },  # Booster
    { role_id = ..., multiplier = 1.075 }   # Donor
]
```

**Medium Server (200-1000 members):**

```toml
xp_cooldown = 1
levels_exponent = 1.75  # Balanced progression
xp_roles = [
    { level = 5, role_id = ... },
    { level = 10, role_id = ... },
    { level = 15, role_id = ... },
    { level = 20, role_id = ... },
    { level = 30, role_id = ... }  # Additional milestone
]
xp_multipliers = [
    { role_id = ..., multiplier = 1.055 },  # Booster
    { role_id = ..., multiplier = 1.075 },  # Donor
    { role_id = ..., multiplier = 1.1 },    # Contributor
    { role_id = ..., multiplier = 1.2 }     # Special contributor
]
enable_xp_cap = false
```

**Large Server (1000+ members):**

```toml
xp_cooldown = 1
levels_exponent = 2.0  # Standard progression
xp_roles = [
    { level = 5, role_id = ... },
    { level = 10, role_id = ... },
    { level = 15, role_id = ... },
    { level = 20, role_id = ... },
    { level = 30, role_id = ... },
    { level = 50, role_id = ... }  # High-level milestone
]
xp_multipliers = [
    { role_id = ..., multiplier = 1.055 },   # Booster
    { role_id = ..., multiplier = 1.065 },   # Donor
    { role_id = ..., multiplier = 1.075 },   # Donor+
    { role_id = ..., multiplier = 1.1 },     # Contributor
    { role_id = ..., multiplier = 1.2 }      # Special contributor
]
enable_xp_cap = true  # Consider capping at high levels
```
