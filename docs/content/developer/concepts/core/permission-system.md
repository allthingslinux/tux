---
title: Permission System
description: Database-driven permission system for guild-specific command access control with role-based hierarchies.
---

# Permission System

Tux uses a database-driven permission system that lets each guild customize who can use which commands. Instead of hardcoding permissions, everything is stored in the database and configured per-guild through commands.

## Overview

The permission system provides flexible, guild-specific access control:

- **Permission Ranks** - Numeric hierarchy (0-10) where higher numbers mean more permissions
- **Role Assignments** - Map Discord roles to permission ranks
- **Command Permissions** - Set required rank for each command per-guild
- **Bypass Rules** - Bot owners, sysadmins, and guild owners bypass all permission checks
- **DM Handling** - Commands bypass permission checks in direct messages
- **Performance Caching** - Fast permission checks with database caching

## How It Works

### Permission Ranks

Permission ranks form a hierarchy from 0 (lowest) to 10 (highest). Each rank has a name and description. Default ranks (0-7) can be created using `/config ranks init`:

- **Rank 0: Member** - Regular community member with standard access
- **Rank 1: Trusted** - Trusted community member
- **Rank 2: Junior Moderator** - Entry-level moderation role
- **Rank 3: Moderator** - Standard moderation permissions
- **Rank 4: Senior Moderator** - Experienced moderators
- **Rank 5: Administrator** - Administrative permissions
- **Rank 6: Head Administrator** - High-level administrators with comprehensive oversight
- **Rank 7: Server Owner** - Server owner (highest default rank)

Guilds can customize these ranks or add their own. Higher ranks automatically have access to everything lower ranks can do.

### Role Assignments

Discord roles are mapped to permission ranks. When a user has multiple roles, they get the highest rank among all their roles. For example, if someone has roles mapped to rank 2 and rank 4, they effectively have rank 4 permissions.

### Command Permissions

Each command can require a specific permission rank. Commands without a configured permission requirement are denied by default for security. Guilds configure command permissions using the unified configuration dashboard (`/config overview` → Command Permissions).

### Permission Checking

When a user runs a command, Tux:

1. Checks if they're a bot owner or sysadmin (always allowed)
2. Checks if they're the guild owner (always allowed)
3. If in a DM, allows the command (permissions don't apply to DMs)
4. Gets their highest permission rank from their roles
5. Looks up the command's required rank
6. Compares ranks and allows or denies access

This happens automatically—you don't need to write permission checking code in your commands.

## Using Permissions in Your Code

### Requiring Permissions

Use the `@requires_command_permission()` decorator on commands that need permission checks:

```python
from tux.core.checks import requires_command_permission

@commands.command()
@requires_command_permission()
async def ban(self, ctx, member: discord.Member, reason: str):
    """Ban a member from the server."""
    # Permission check happens automatically
    await ctx.guild.ban(member, reason=reason)
```

The decorator handles all permission checking automatically. If the user doesn't have the required rank, they get a clear error message.

### Allowing Unconfigured Commands

By default, commands without configured permissions are denied. If you want to allow unconfigured commands (less secure), use the `allow_unconfigured` parameter:

```python
@requires_command_permission(allow_unconfigured=True)
async def public_command(self, ctx):
    """Command that works even if not configured."""
    await ctx.send("This works!")
```

### Getting User Permission Rank

You can check a user's permission rank programmatically:

```python
from tux.core.permission_system import get_permission_system

permission_system = get_permission_system()
user_rank = await permission_system.get_user_permission_rank(ctx)
```

This returns the user's highest permission rank (0-10) based on their roles.

## Permission Configuration

Guilds configure permissions through the unified configuration dashboard. The dashboard provides an interactive interface for managing all permission settings.

**Dashboard Commands:**

- `/config` or `/config overview` - Opens the main configuration dashboard
- `/config ranks` - Opens dashboard in ranks mode to manage permission ranks
- `/config roles` (or `/config role`) - Opens dashboard in roles mode to assign roles to ranks
- `/config commands` - Opens dashboard in commands mode to set command permissions (or use `/config overview` → Command Permissions)

All configuration is stored in the database and persists across bot restarts. Configuration is per-guild, so each server can have different permission setups.

## Initialization

Permission ranks must be initialized before use. Open the configuration dashboard with `/config ranks` and use the dashboard interface to initialize default permission ranks (0-7) for your guild. This is a one-time setup—if ranks already exist, the dashboard will show existing ranks.

## Best Practices

### Security First

Commands are denied by default if not configured. This prevents accidental access to sensitive commands. Always configure permissions for commands that need protection.

### Use Appropriate Ranks

Don't require rank 7 for simple commands. Reserve high ranks for administrative operations. Most moderation commands should use ranks 2-4.

### Document Permission Requirements

In your command docstrings, mention what permission rank is required. This helps guild admins configure permissions correctly.

### Test Permission Checks

When developing commands, test with different permission ranks to ensure access control works as expected. Use the permission configuration commands to set up test scenarios.

## Troubleshooting

### Commands Always Denied

If commands are always denied even for admins, check:

1. Permission ranks are initialized for the guild (use `/config ranks` dashboard)
2. Roles are assigned to permission ranks (use `/config roles` dashboard)
3. Commands have permission requirements configured (use `/config overview` → Command Permissions)
4. Users have roles that are assigned to ranks
5. Users' highest rank meets the command's required rank

### Permission Checks Not Working

If permission checks aren't working:

1. Verify the `@requires_command_permission()` decorator is applied
2. Check that the permission system is initialized
3. Ensure the database connection is working

### Users Can't Access Commands

If users can't access commands they should have:

1. Check their role assignments in the permission system (use `/config roles` dashboard)
2. Verify the command's required rank isn't too high (use `/config overview` → Command Permissions)
3. Confirm they have roles assigned to ranks (users get the highest rank from all their roles)
4. Check if they're bot owner/sysadmin (these bypass all checks)
5. Note: Commands work in DMs without permission checks, so DM access isn't the issue

## Resources

- **Source Code**: `src/tux/core/permission_system.py`
- **Permission Decorator**: `src/tux/core/decorators.py` (also available via `tux.core.checks`)
- **Database Controllers**: `src/tux/database/controllers/permissions.py`
- **Database Models**: `src/tux/database/models/models.py`
- **Config Commands**: `src/tux/modules/config/ranks.py`, `roles.py`, `commands.py`
