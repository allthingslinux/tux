# Moderation Commands

Tux provides comprehensive moderation tools for managing your Discord server. All moderation actions are tracked in the case management system.

## Overview

Moderation commands allow you to:

- **Punish** users who violate rules (ban, kick, timeout, jail, warn)
- **Track** all moderation actions with cases
- **Manage** server content (purge messages, slowmode)
- **Poll** the community for ban decisions
- **Restrict** snippet access for rule violators

## Core Moderation Commands

### Ban

Ban a user from the server permanently.

**Usage:**

```bash
# Slash command
/ban @user reason:"Rule violation" purge:1 silent:true

# Prefix command (reason is positional, comes after user)
$ban @user Rule violation -purge 1 -silent
$ban @user Spamming links -p 7 -s
```

**Parameters:**

- `user` (required) - The user to ban
- `reason` (positional) - Reason for the ban (default: "No reason provided")
- `-purge` or `-p` - Days of messages to delete (0-7, default: 0)
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `b`

**Permission:** Rank 3 (Moderator)

**Notes:**

- Creates a ban case in the database
- Sends DM to user unless silent flag is used
- Can ban users not in the server (by ID)
- Optionally purges user's recent messages

**Example:**

```bash
/ban @spammer reason:"Advertising" purge:7
$ban @spammer Advertising -p 7
```

---

### Tempban

Temporarily ban a user for a specified duration.

**Usage:**

```bash
# Slash command
/tempban @user reason:"Cooldown period" duration:7d purge:1

# Prefix command (reason is positional, comes after user)
$tempban @user Cooldown period -duration 7d -p 1
$tempban @user Spamming -d 3d -silent
```

**Parameters:**

- `user` (required) - The user to temporarily ban
- `reason` (positional) - Reason for the tempban (default: "No reason provided")
- `-duration` or `-d` (required) - Ban duration (e.g., 1h, 3d, 1w)
- `-purge` or `-p` - Days of messages to delete (0-7, default: 0)
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `tb`

**Permission:** Rank 3 (Moderator)

**Duration Format:**

- `s` - seconds
- `m` - minutes  
- `h` - hours
- `d` - days
- `w` - weeks

**Example:**

```bash
/tempban @user reason:"Repeated warnings" duration:3d
$tempban @user Repeated warnings -d 3d
```

---

### Unban

Unban a previously banned user.

**Usage:**

```bash
# Slash command
/unban @user reason:"Appeal approved"
/unban 123456789012345678 reason:"Ban appeal accepted"

# Prefix command (reason is positional, comes after user)
$unban @user Appeal approved
$unban 123456789012345678 Ban appeal accepted
```

**Parameters:**

- `user` (required) - The user to unban (mention, ID, or username)
- `reason` (positional) - Reason for the unban (default: "No reason provided")

**Aliases:** `ub`

**Permission:** Rank 4 (Senior Moderator)

**Notes:**

- Creates an unban case
- User must be currently banned
- Can search by username or ID

**Example:**

```bash
/unban 123456789012345678 reason:"Ban appeal accepted"
$unban 123456789012345678 Ban appeal accepted
```

---

### Kick

Kick a user from the server.

**Usage:**

```bash
# Slash command
/kick @user reason:"Disruptive behavior" silent:true

# Prefix command (reason is positional, comes after user)
$kick @user Disruptive behavior -silent
$kick @user Spamming -s
```

**Parameters:**

- `user` (required) - The user to kick
- `reason` (positional) - Reason for the kick (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `k`

**Permission:** Rank 3 (Moderator)

**Notes:**

- User can rejoin with a new invite
- Creates a kick case
- Sends DM to user unless silent

**Example:**

```bash
/kick @troll reason:"Spamming"
$kick @troll Spamming
```

---

### Timeout

Timeout a user for a specified duration (mute).

**Usage:**

```bash
# Slash command
/timeout @user reason:"Spam" duration:10m silent:true

# Prefix command (reason is positional, comes after user)
$timeout @user Spam -duration 10m -silent
$timeout @user Channel flooding -d 1h -s
```

**Parameters:**

- `user` (required) - The user to timeout
- `reason` (positional) - Reason for the timeout (default: "No reason provided")
- `-duration` or `-d` (required) - Timeout duration (max 28 days)
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `to`, `mute`

**Permission:** Rank 2 (Junior Moderator)

**Duration Limits:**

- Minimum: 1 second
- Maximum: 28 days (Discord limit)

**Example:**

```bash
/timeout @spammer reason:"Channel flooding" duration:1h
$timeout @spammer Channel flooding -d 1h
```

---

### Untimeout

Remove a timeout from a user.

**Usage:**

```bash
# Slash command
/untimeout @user reason:"Cooled down" silent:true

# Prefix command (reason is positional, comes after user)
$untimeout @user Cooled down -silent
$untimeout @user Served time -s
```

**Parameters:**

- `user` (required) - The user to untimeout
- `reason` (positional) - Reason for removing timeout (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `uto`, `unmute`

**Permission:** Rank 2 (Junior Moderator)

**Example:**

```bash
/untimeout @user reason:"Served time"
$untimeout @user Served time
```

---

### Jail

Jail a user by assigning jail role and removing other roles.

**Usage:**

```bash
# Slash command
/jail @user reason:"Severe warning" silent:true

# Prefix command (reason is positional, comes after user)
$jail @user Severe warning -silent
$jail @user Final warning before ban -s
```

**Parameters:**

- `user` (required) - The user to jail
- `reason` (positional) - Reason for jailing (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `j`

**Permission:** Rank 2 (Junior Moderator)

**Requirements:**

- Jail role must be configured: `/config set jail_role @Jailed`
- Jail channel must be configured: `/config set jail_channel #jail`

**How It Works:**

1. Assigns jail role to user
2. Removes all manageable roles
3. User can only access jail channel
4. Stores removed roles for unjail

**Example:**

```bash
/jail @problematic reason:"Final warning before ban"
$jail @problematic Final warning before ban
```

---

### Unjail

Unjail a user, restoring their previous roles.

**Usage:**

```bash
# Slash command
/unjail @user reason:"Behavior improved" silent:true

# Prefix command (reason is positional, comes after user)
$unjail @user Behavior improved -silent
$unjail @user Good conduct -s
```

**Parameters:**

- `user` (required) - The user to unjail
- `reason` (positional) - Reason for unjailing (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `uj`

**Permission:** Rank 2 (Junior Moderator)

**Notes:**

- Removes jail role
- Restores previously removed roles
- Roles are stored in the jail case

**Example:**

```bash
/unjail @user reason:"Completed jail time"
$unjail @user Completed jail time
```

---

### Warn

Issue a formal warning to a user.

**Usage:**

```bash
# Slash command
/warn @user reason:"Please follow the rules" silent:true

# Prefix command (reason is positional, comes after user)
$warn @user Please follow the rules -silent
$warn @user Don't ping everyone -s
```

**Parameters:**

- `user` (required) - The user to warn
- `reason` (positional) - Reason for the warning (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `w`

**Permission:** Rank 2 (Junior Moderator)

**Notes:**

- Sends DM to user unless silent
- Creates a warning case
- Used for minor infractions
- User can accumulate multiple warnings

**Example:**

```bash
/warn @newbie reason:"Don't ping @everyone"
$warn @newbie Don't ping everyone
```

---

## Content Moderation

### Purge

Delete multiple messages at once.

**Usage:**

```bash
/purge limit:50
/purge limit:100 channel:#spam
$purge 50
$purge 100 #spam
```bash

**Parameters:**

- `limit` (required) - Number of messages to delete (1-500)
- `channel` (optional) - Channel to purge (default: current channel)

**Aliases:** `p`

**Permission:** Rank 3 (Moderator)

**Limitations:**

- Cannot delete messages older than 14 days (Discord limitation)
- Maximum 500 messages per command
- No filtering by user, content, or other criteria
- Deletes most recent messages

**Examples:**

```bash
/purge limit:50                     # Delete last 50 messages (slash)
$purge 50                           # Delete last 50 messages (prefix)
/purge limit:100 channel:#spam      # Delete 100 messages from #spam
$purge 100 #spam                    # Same, prefix version
```bash

---

### Slowmode

Set or view channel slowmode.

**Usage:**

```bash
/slowmode duration:10s
/slowmode #channel duration:30s
$slowmode 10s
$slowmode #general 30s
```bash

**Parameters:**

- `channel` (optional) - Channel to modify (default: current channel)
- `duration` - Slowmode delay (0 to disable, max 6h)

**Aliases:** `sm`

**Permission:** Rank 3 (Moderator)

**Duration Format:**

- Seconds: `30s`, `45s`
- Minutes: `2m`, `5m`
- Hours: `1h`, `2h`
- Disable: `0` or `off`

**Examples:**

```bash
/slowmode duration:30s              # Set 30s slowmode in current channel
/slowmode #general duration:1m      # Set 1m slowmode in #general
/slowmode duration:0                # Disable slowmode
```bash

---

### Clear AFK

Clear a user's AFK status manually.

**Usage:**

```bash
/clearafk @user
$clearafk @user
```bash

**Parameters:**

- `user` (required) - The user whose AFK to clear

**Aliases:** `unafk`

**Permission:** Rank 2 (Junior Moderator)

**Notes:**

- Normally AFK is cleared automatically when user sends a message
- Use this if AFK status is stuck
- Restores original nickname if it was changed

---

## Poll-Based Moderation

### Pollban

Create a poll to vote on banning a user.

**Usage:**

```bash
# Slash command
/pollban @user reason:"Community vote" silent:true

# Prefix command (reason is positional, comes after user)
$pollban @user Community vote -silent
$pollban @user Let the community decide -s
```

**Parameters:**

- `user` (required) - The user to vote on banning
- `reason` (positional) - Reason for the poll ban (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `pb`

**Permission:** Rank 3 (Moderator)

**How It Works:**

1. Creates a vote in a designated channel
2. Community members vote 👍 (ban) or 👎 (keep)
3. After voting period, action is taken based on results
4. Creates a case when completed

---

### Pollunban

Create a poll to vote on unbanning a user.

**Usage:**

```bash
# Slash command
/pollunban @user reason:"Redemption vote" silent:true

# Prefix command (reason is positional, comes after user)
$pollunban @user Redemption vote -silent
$pollunban @user Second chance vote -s
```

**Parameters:**

- `user` (required) - The banned user to vote on unbanning
- `reason` (positional) - Reason for the poll unban (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `pub`

**Permission:** Rank 4 (Senior Moderator)

---

## Snippet Restrictions

### Snippetban

Prevent a user from using snippets.

**Usage:**

```bash
# Slash command
/snippetban @user reason:"Snippet abuse" silent:true

# Prefix command (reason is positional, comes after user)
$snippetban @user Snippet abuse -silent
$snippetban @user Spamming snippets -s
```

**Parameters:**

- `user` (required) - The user to ban from snippets
- `reason` (positional) - Reason for the restriction (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `sb`

**Permission:** Rank 3 (Moderator)

**Notes:**

- User cannot use any snippet commands
- Does not affect other bot functionality
- Separate from server ban

---

### Snippetunban

Restore a user's snippet access.

**Usage:**

```bash
# Slash command
/snippetunban @user reason:"Restriction lifted" silent:true

# Prefix command (reason is positional, comes after user)
$snippetunban @user Restriction lifted -silent
$snippetunban @user Good behavior -s
```

**Parameters:**

- `user` (required) - The user to unban from snippets
- `reason` (positional) - Reason for restoring access (default: "No reason provided")
- `-silent` or `-s` - Skip sending DM to user (default: false)

**Aliases:** `sub`

**Permission:** Rank 4 (Senior Moderator)

---

## Case Management

### Cases

View and manage moderation cases.

**Usage:**

```bash
/cases                              # View all cases
/cases view 123                     # View specific case
/cases search user:@someone         # Search cases by user
```bash

**Subcommands:**

- `view <case_number>` - View specific case details
- `search` - Search cases by criteria

**Aliases:** `case`, `c`

**Permission:** Rank 2 (Junior Moderator) to view, Rank 3+ to modify

**Notes:**

- All moderation actions create cases
- Cases track: user, moderator, reason, timestamp, type
- Interactive navigation with pages
- Search and filter functionality

**Examples:**

```bash
/cases                              # Browse all cases
/cases view 42                      # View case #42
```bash

---

### Report

Report a user or issue to moderators anonymously.

**Usage:**

```bash
/report
```bash

**How It Works:**

1. Opens a modal form
2. User fills in: subject, description, evidence (optional)
3. Report sent anonymously to mod channel
4. Moderators can review and take action

**Permission:** Rank 0 (Everyone)

**Note:** This is a **slash-only** command (opens a modal).

---

## Permission Requirements

| Command       | Minimum Rank | Typical Role       |
|---------------|-------------|---------------------|
| warn          | 2           | Junior Moderator    |
| timeout       | 2           | Junior Moderator    |
| untimeout     | 2           | Junior Moderator    |
| jail          | 2           | Junior Moderator    |
| unjail        | 2           | Junior Moderator    |
| clearafk      | 2           | Junior Moderator    |
| ban           | 3           | Moderator           |
| kick          | 3           | Moderator           |
| tempban       | 3           | Moderator           |
| pollban       | 3           | Moderator           |
| snippetban    | 3           | Moderator           |
| purge         | 3           | Moderator           |
| slowmode      | 3           | Moderator           |
| unban         | 4           | Senior Moderator    |
| pollunban     | 4           | Senior Moderator    |
| snippetunban  | 4           | Senior Moderator    |
| cases (view)  | 2           | Junior Moderator    |
| report        | 0           | Everyone            |

!!! note "Customizable"
    These are default requirements. Administrators can customize per-command permissions with `/config command permission`.

## Common Workflows

### Standard Punishment Progression

For rule violations, follow this typical escalation:

1. **First offense:** `/warn @user reason:"Please read #rules"`
2. **Second offense:** `/timeout @user duration:1h reason:"Repeated violation"`
3. **Third offense:** `/jail @user reason:"Multiple violations"` or `/tempban @user duration:3d`
4. **Severe/Repeated:** `/ban @user reason:"Continued rule breaking"`

### Handling Spam

Quick response to spam:

```bash
# Timeout the spammer
/timeout @spammer duration:10m reason:"Spam"

# Clean up the spam
$purge 50 @spammer

# Set slowmode to prevent repeat
/slowmode duration:30s
```bash

### Community Decisions

For controversial cases:

```bash
# Create a poll for the community
/pollban @problematic reason:"Let community decide"

# After voting period, action taken automatically
```bash

## Moderation Flags

### Reason Flag

All commands support a reason:

```bash
/ban @user reason:"Detailed explanation here"
```bash

**Best Practices:**

- ✅ Be specific and clear
- ✅ Reference rule violations
- ✅ Keep it professional
- ❌ Don't use offensive language
- ❌ Don't make it personal

### Silent Flag

Skip sending DM to the user:

```bash
/ban @user reason:"Spam bot" silent:true
```bash

**When to use:**

- Bot accounts (won't read DMs anyway)
- Users with DMs disabled
- Emergency situations
- Raid mitigation

### Purge Flag

Delete recent messages when banning:

```bash
/ban @spammer reason:"Advertising" purge:7
```bash

**Purge days:**

- `0` - Don't delete any messages
- `1-7` - Delete messages from last N days
- Discord only allows up to 7 days

## Case System

Every moderation action creates a case with:

- **Case Number** - Unique ID for reference
- **Type** - Ban, kick, timeout, etc.
- **User** - Who was moderated
- **Moderator** - Who performed the action
- **Reason** - Why it happened
- **Timestamp** - When it occurred
- **Duration** - For timed actions
- **Additional Data** - Action-specific info

View cases with `/cases` or `/cases view <number>`.

## Best Practices

### Documentation

- Always include a clear reason
- Be specific about rule violations
- Reference your server rules
- Keep language professional

### Escalation

- Start with warnings
- Use timeouts for temporary issues
- Jail for serious but not ban-worthy
- Ban only when necessary

### Communication

- Explain rules to first-time offenders
- Use DMs to provide context
- Follow up on tempbans
- Review cases regularly

### Team Coordination

- Check existing cases before acting
- Discuss major bans with team
- Document complex situations
- Use pollban for community input

## Troubleshooting

### "Missing Permissions" Error

**Cause:** Bot lacks Discord permissions or your rank is too low.

**Solution:**

1. Check bot has appropriate Discord permissions (Ban Members, Kick Members, etc.)
2. Check configured role assignments: `/config role`
3. Verify bot's role is above target user's role

### Can't Ban/Kick Certain Users

**Cause:** Role hierarchy issue.

**Solution:**

- Bot cannot moderate users with equal or higher roles
- Move bot's role higher in Server Settings → Roles
- Or demote the user's role

### Jail Not Working

**Cause:** Jail role or channel not configured.

**Solution:**

```bash
/config set jail_role @Jailed
/config set jail_channel #jail
```bash

### Purge Command Not Working

**Cause:** Messages too old or insufficient permissions.

**Solution:**

- Cannot delete messages older than 14 days
- Ensure you have "Manage Messages" permission
- Use slash command: `/purge count:50` or prefix: `$purge 50`

## Related Commands

- **[Cases](moderation.md#cases)** - View moderation history
- **[Config](config.md)** - Configure moderation settings
- **[Permissions](../permissions.md)** - Understand permission ranks

## Need Help?

- **[Permission System](../permissions.md)** - Understand ranks
- **[Discord Support](https://discord.gg/gpmSjcjQxg)** - Ask in #support
- **[Report Bugs](https://github.com/allthingslinux/tux/issues)** - Found an issue?

---

**Next:** Learn about [Utility Commands](utility.md) for server management tools.
