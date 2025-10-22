# Configuration Commands

Server configuration and setup commands for administrators.

## Overview

Config commands allow server administrators to:

- Run interactive setup wizard
- Manage permission ranks
- Configure features
- View current settings

## Main Commands

### Config

View complete guild configuration overview.

**Usage:**

```
/config
$config
```

**Permission:** Rank 0+ (Everyone can view)

**Shows:**

- Current prefix
- Configured channels (mod log, jail, starboard, etc.)
- Enabled features
- Permission rank settings
- XP configuration

---

### Config Wizard

Launch the interactive setup wizard.

**Usage:**

```
/config wizard
$config wizard
```

**Permission:** Administrator (Discord permission)

**What It Does:**

Guides you through setting up:

1. **Moderation Channels** - Log channel, jail channel
2. **Jail System** - Jail role configuration
3. **Starboard** - Channel and threshold
4. **XP System** - Role rewards configuration
5. **Basic Settings** - Prefix and other options

**Features:**

- Interactive buttons and dropdowns
- Step-by-step guidance
- Validation and error checking
- Can be cancelled at any time

**Example:**

Run `/config wizard` and follow the prompts in the interactive menu.

---

### Config Reset

Reset guild setup to allow re-running the wizard.

**Usage:**

```
/config reset
$config reset
```

**Permission:** Administrator (Discord permission)

**Warning:** This resets setup completion flag but doesn't delete your configuration. Allows you to run the wizard again.

---

## Permission Rank Management

### Config Rank

List all permission ranks in the guild.

**Usage:**

```
/config rank
$config rank
```

**Permission:** Rank 0+ (Everyone can view)

**Shows:**

- All permission ranks (0-7)
- Rank names and descriptions
- Assigned Discord roles
- Number of users with each rank

---

### Config Rank Init

Initialize permission ranks for your server.

**Usage:**

```
/config rank init
```

**Permission:** Administrator (Discord permission)

**What It Does:**

Creates the default 8 permission ranks (0-7):

- Member (0)
- Trusted (1)
- Junior Moderator (2)
- Moderator (3)
- Senior Moderator (4)
- Administrator (5)
- Head Administrator (6)
- Server Owner (7)

Run this once when first setting up Tux.

---

### Config Role

List all role-to-rank assignments.

**Usage:**

```
/config role
$config role
```

**Permission:** Rank 0+ (Everyone can view)

**Shows:**

- All Discord roles assigned to ranks
- Which rank each role is assigned to
- Number of users with each role

---

### Config Role Assign

Assign a Discord role to a permission rank.

**Usage:**

```
/config role assign 3 @Moderators
/config role assign 5 @Admins
```

**Parameters:**

- `rank` (required) - Permission rank number (0-7)
- `role` (required) - Discord role to assign

**Permission:** Administrator (Discord permission)

**Example:**

```
/config role assign 3 @Moderators
```

Now all users with @Moderators role have Rank 3 permissions.

---

### Config Role Unassign

Remove a role assignment from a permission rank.

**Usage:**

```
/config role unassign @Moderators
```

**Parameters:**

- `role` (required) - Discord role to remove from its rank

**Permission:** Administrator (Discord permission)

**Note:** Removes the role from whatever rank it's assigned to.

---

## Command-Specific Permissions

### Config Command

List all command permission overrides.

**Usage:**

```
/config command
$config command
```

**Permission:** Rank 0+ (Everyone can view)

**Shows:**

- Commands with custom permission requirements
- Required rank for each command
- Category (if applicable)

---

### Config Command Assign

Override default permission requirement for a specific command.

**Usage:**

```
/config command assign ping 2
/config command assign ban 4 moderation
```

**Parameters:**

- `command_name` (required) - Command to restrict
- `rank` (required) - New required rank (0-7)
- `category` (optional) - Command category

**Permission:** Administrator (Discord permission)

**Example:**

```
# Make /ping require Rank 2 instead of default (0)
/config command assign ping 2

# Make /ban require Rank 4 instead of default (3)
/config command assign ban 4
```

---

### Config Command Unassign

Remove custom permission requirement (revert to default).

**Usage:**

```
/config command unassign ping
```

**Parameters:**

- `command_name` (required) - Command to reset

**Permission:** Administrator (Discord permission)

**Example:**

```
# Reset /ping to default permission
/config command unassign ping
```

---

## Permission Requirements

| Command                    | Minimum Rank | Discord Permission |
|---------------------------|-------------|---------------------|
| config (view)             | 0           | -                   |
| config wizard             | -           | Administrator       |
| config reset              | -           | Administrator       |
| config rank (view)        | 0           | -                   |
| config rank init          | -           | Administrator       |
| config rank create        | -           | Administrator       |
| config rank delete        | -           | Administrator       |
| config role (view)        | 0           | -                   |
| config role assign        | -           | Administrator       |
| config role unassign      | -           | Administrator       |
| config command (view)     | 0           | -                   |
| config command assign     | -           | Administrator       |
| config command unassign   | -           | Administrator       |

## Setup Workflow

### Initial Server Setup

1. **Run the Wizard:**

   ```
   /config wizard
   ```

2. **Initialize Ranks:**

   ```
   /config rank init
   ```

3. **Assign Roles:**

   ```
   /config role assign 3 @Moderators
   /config role assign 5 @Admins
   ```

4. **Verify:**

   ```
   /config
   /config rank
   ```

### Ongoing Management

- **View role assignments:** `/config role`
- **Modify permissions:** `/config command assign`
- **Re-run wizard:** `/config reset` then `/config wizard`
- **View settings:** `/config`

## Configuration Values

The config system manages:

### Channels

- **Log Channel** - Moderation logs
- **Jail Channel** - Where jailed users can chat
- **Starboard Channel** - Starred messages

### Roles

- **Jail Role** - Role assigned to jailed users

### Features

- **XP Enabled** - XP gain enabled/disabled
- **Starboard Enabled** - Starboard active
- **And more...**

### Settings

- **Command Prefix** - Server-specific prefix
- **Starboard Threshold** - Stars required

## Tips

!!! tip "Run Wizard First"
    The easiest way to set up Tux is to run `/config wizard` right after inviting the bot!

!!! tip "Guild-Specific"
    All configuration is per-server. Each Discord server has its own independent settings.

!!! tip "View Before Changing"
    Run `/config` to see current settings before making changes.

!!! tip "Permission Ranks Are Powerful"
    Take time to set up ranks properly - they control all command access!

## Troubleshooting

### Wizard Won't Start

**Cause:** Already completed or missing permissions

**Solution:**

- Run `/config reset` to reset completion flag
- Ensure you have Discord Administrator permission
- Check bot has necessary channel/role permissions

### Can't Assign Roles to Ranks

**Cause:** Missing administrator permission

**Solution:**

- Must have Discord Administrator permission
- Run `/config rank init` first

### Rank Assignments Not Working

**Cause:** Ranks not initialized

**Solution:**

```
/config rank init                   # Initialize ranks first
/config role assign 3 @Role         # Then assign roles
```

## Best Practices

### Setup Order

1. Run wizard for basic setup
2. Initialize permission ranks
3. Assign roles to ranks
4. Test with different roles
5. Adjust as needed

### Permission Structure

- Use full 0-7 range for large servers
- Smaller servers can use fewer ranks
- Keep it simple and consistent
- Document your setup for your team

### Regular Reviews

- Review configuration quarterly
- Update as server grows
- Adjust permissions as needed
- Remove outdated settings

## Related Documentation

- **[Permission System](../permissions.md)** - Understanding permission ranks
- **[Admin Guide](../../admin-guide/configuration/index.md)** - Self-hoster config options

---

**Next:** Learn about [Admin/Dev Commands](admin.md) for bot management.
