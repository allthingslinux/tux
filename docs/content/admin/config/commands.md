---
title: Commands
tags:
  - admin-guide
  - configuration
  - commands
icon: lucide/command
---

# Commands Configuration

Configure which permission rank is required for each command. This allows you to customize access control for your server's specific needs.

## Overview

The command permissions system lets you set a required permission rank for each command. Users must have a rank equal to or higher than the required rank to use the command.

### How It Works

1. **Permission Ranks** - Users get a rank based on their Discord roles (configured in [Role Assignments](./roles.md))
2. **Command Requirements** - Each command can require a specific rank
3. **Access Control** - Users with insufficient rank are denied access with a clear error message

### Default Behavior

- **Unconfigured Commands** - By default, commands without a configured permission are **denied** for security
- **Parent Command Fallback** - If a subcommand has no permission set, the system checks the parent command's permission
  - Example: If `/config ranks` has no permission, it checks `/config` permission
- **Bypass Rules** - Bot owners, sysadmins, and server owners bypass all permission checks

## Configuration

### Using the Dashboard

1. Run `/config commands` or open the [Admin Configuration](index.md) and use **Commands** → **Open**.
2. Browse or search for the command you want to configure
3. Select the required permission rank from the dropdown
4. The change is saved immediately

### Using Commands

You can also configure permissions via slash commands (requires appropriate permissions):

```text
/config commands set command:"ban" rank:3
```

## Permission Ranks

Permission ranks range from 0 (lowest) to 10 (highest). Higher ranks automatically have access to everything lower ranks can do.

### Default Ranks

- **Rank 0: Member** - Regular community member
- **Rank 1: Trusted** - Trusted community member
- **Rank 2: Junior Moderator** - Entry-level moderation
- **Rank 3: Moderator** - Standard moderation permissions
- **Rank 4: Senior Moderator** - Experienced moderators
- **Rank 5: Administrator** - Administrative permissions
- **Rank 6: Head Administrator** - High-level administrators
- **Rank 7: Server Owner** - Server owner (highest default)

See [Ranks Configuration](./ranks.md) for more details.

## Recommended Settings

### Moderation Commands

Most moderation commands should require ranks 2-4:

- **Rank 2 (Junior Moderator)**: Warn, timeout (short durations)
- **Rank 3 (Moderator)**: Ban, kick, timeout (longer durations), jail
- **Rank 4 (Senior Moderator)**: Tempban, case modifications

### Administrative Commands

Administrative commands should require higher ranks:

- **Rank 5 (Administrator)**: Configuration commands, permission management
- **Rank 6 (Head Administrator)**: Server-wide settings, maintenance commands
- **Rank 7 (Server Owner)**: Critical operations, bot management

### Utility Commands

Most utility commands can be lower rank or unconfigured (public):

- **Rank 0-1**: Info, ping, wiki, help
- **Unconfigured (denied)**: Development commands, eval

## Best Practices

### Security First

- **Deny by default** - Commands without configured permissions are denied
- **Start restrictive** - It's easier to lower requirements than raise them
- **Review regularly** - Periodically review command permissions for appropriateness

### Use Appropriate Ranks

- Don't require rank 7 for simple commands
- Reserve high ranks for administrative operations
- Consider your server's structure when setting ranks

### Document Changes

- Keep track of permission changes
- Document why certain commands require specific ranks
- Communicate changes to your moderation team

### Test Permissions

- Test commands with different permission ranks
- Verify that users can access commands they should
- Ensure users are denied access to commands they shouldn't use

## Performance

The permission system uses caching to improve performance:

- **Command permissions** are cached for 5 minutes
- **User permission ranks** are cached for 2 minutes
- Caches are automatically invalidated when permissions change
- Cache pre-warming on bot startup reduces cold-start delays

## Troubleshooting

### Commands Always Denied

If commands are always denied even for admins:

1. Check that permission ranks are initialized (use `/config ranks init`)
2. Verify roles are assigned to permission ranks (use `/config roles`)
3. Ensure commands have permission requirements configured
4. Confirm users have roles assigned to ranks
5. Verify users' highest rank meets the command's required rank

### Permission Checks Not Working

If permission checks aren't working:

1. Verify the permission system is initialized
2. Check that the database connection is working
3. Ensure caches aren't stale (wait 5 minutes or restart the bot)
4. Check bot logs for permission-related errors

### Users Can't Access Commands

If users can't access commands they should have:

1. Check their role assignments in the permission system
2. Verify the command's required rank isn't too high
3. Confirm they have roles assigned to ranks
4. Check if they're bot owner/sysadmin (these bypass checks)
5. Note: Commands work in DMs without permission checks

## Related Configuration

- **[Ranks Configuration](./ranks.md)** - Set up permission ranks
- **[Role Assignments](./roles.md)** - Map Discord roles to permission ranks
- **[Permission System](../../developer/concepts/core/permission-system.md)** - Technical details

## See Also

- [Permission System Documentation](../../developer/concepts/core/permission-system.md) - Technical implementation details
- [Caching Best Practices](../../developer/best-practices/caching.md) - Performance optimization guide
