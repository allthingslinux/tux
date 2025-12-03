---
title: Roles Configuration
tags:
  - admin-guide
  - configuration
  - roles
---

# Roles Configuration

Role assignments connect Discord roles to permission ranks, allowing Tux to determine user permissions based on their Discord roles. This guide covers how to assign, manage, and troubleshoot role-to-rank mappings.

## Overview

Tux's permission system works by mapping Discord roles to permission ranks:

- **Discord Roles**: The roles users have in your server
- **Permission Ranks**: Numeric levels (0-10) that determine access rights
- **Role Assignments**: The connection between Discord roles and permission ranks

When a user has multiple roles, they get the **highest** permission rank among all their assigned roles.

## How It Works

### Permission Calculation

1. User joins/has roles in Discord
2. Tux looks up which permission ranks are assigned to those roles
3. User gets the highest rank among all their role assignments
4. Commands check if user's rank meets the required rank

### Example

If a user has these roles:

- `@Moderator` → Rank 3
- `@Event Staff` → Rank 2
- `@Member` → Rank 0

The user gets **Rank 3** permissions (the highest).

## Setting Up Role Assignments

### Using the Dashboard (Recommended)

1. Run `/config roles` (or `/config role`) to open the roles configuration dashboard
2. The dashboard shows existing role assignments and available Discord roles
3. Click on a Discord role to assign it to a permission rank
4. Select the desired rank from the dropdown
5. The assignment appears in the dashboard

### Using Commands

You can also manage role assignments with text commands:

**Assign a role to a rank:**

```text
/config role assign 3 @Moderator
```

**Remove a role assignment:**

```text
/config role unassign @Moderator
```

**List all assignments:**

```text
/config role list
```

## Default Rank Setup

Before assigning roles, ensure you have permission ranks set up:

1. Use `/config ranks` → "🚀 Init Default Ranks" to create ranks 0-7
2. Or use `/config ranks init` via command

## Best Practices

### Role Hierarchy Planning

- **Start with defaults**: Map your basic roles first
- **Progressive permissions**: Ensure higher ranks have more permissions
- **Clear naming**: Use descriptive role names that indicate their permission level
- **Regular review**: Audit role assignments periodically

### Common Role Patterns

```text
Server Owner (Rank 7) → @Server Owner
Head Admin (Rank 6) → @Head Administrator
Admin (Rank 5) → @Administrator
Senior Mod (Rank 4) → @Senior Moderator
Moderator (Rank 3) → @Moderator
Jr Mod (Rank 2) → @Junior Moderator
Trusted (Rank 1) → @Trusted Member
Member (Rank 0) → @Member (everyone starts here)
```

### Special Considerations

- **Bot roles**: Don't assign bot roles to permission ranks unless they should have admin access
- **Integration roles**: Be careful with roles from bots/integrations
- **Temporary roles**: Consider if temporary roles (events, giveaways) need rank assignments
- **Multiple assignments**: One role can only be assigned to one rank, but multiple roles can have the same rank

## Managing Assignments

### Adding Assignments

**Dashboard Method:**

- Open `/config roles`
- Find the Discord role in the unassigned section
- Click the role and select a rank

**Command Method:**

```text
/config role assign <rank_number> @RoleName
```

### Removing Assignments

**Dashboard Method:**

- Open `/config roles`
- Find the assigned role
- Click the role and select "Unassign" or choose a different rank

**Command Method:**

```text
/config role unassign @RoleName
```

### Viewing Assignments

**Dashboard Method:**

- Run `/config roles` to see all current assignments

**Command Method:**

```text
/config role list
```

## Troubleshooting

### Users Can't Access Commands

If users can't access commands they should have:

1. **Check role assignments**: Use `/config role list` to verify roles are assigned correctly
2. **Verify user roles**: Ensure users actually have the Discord roles assigned to ranks
3. **Check rank hierarchy**: Users get the highest rank from all their roles
4. **Command permissions**: Ensure commands have rank requirements set (`/config overview` → Command Permissions)
5. **Role position**: Discord role hierarchy doesn't affect permission ranks

### Roles Not Appearing

If roles don't show in the dashboard:

1. **Bot permissions**: Ensure the bot can see roles (needs to be in the server)
2. **Role visibility**: Bot needs permission to view roles
3. **Role position**: Bot's highest role must be above roles it needs to assign
4. **Cache issues**: Try refreshing the dashboard

### Permission Not Working as Expected

If permissions aren't working:

1. **Rank initialization**: Ensure ranks are set up (`/config ranks`)
2. **Role assignments**: Verify roles are assigned to ranks (`/config roles`)
3. **User role check**: Confirm users have the expected Discord roles
4. **Command config**: Check command permission requirements
5. **Bot permissions**: Ensure bot has necessary Discord permissions

### Multiple Role Conflicts

If users have conflicting permissions:

1. **Understand hierarchy**: Users always get the highest rank from their roles
2. **Review assignments**: Check which roles are assigned to which ranks
3. **Role cleanup**: Remove unnecessary role assignments
4. **Consolidate ranks**: Consider if multiple roles should have the same rank

## Advanced Configuration

### Custom Permission Ranks

After setting up default ranks (0-7), you can create custom ranks (8-10):

1. Use `/config ranks` → "+ Create Rank"
2. Create specialized ranks for unique server roles
3. Assign Discord roles to your custom ranks

### Integration with Commands

Role assignments work with command permissions:

- Set command requirements in `/config overview` → Command Permissions
- Users need at least the required rank to use commands
- Higher ranks automatically have access to lower-ranked commands

### Audit and Monitoring

Regularly review your role assignments:

- Use `/config role list` to see all assignments
- Check for orphaned assignments (roles that no longer exist)
- Audit permission changes in server logs
- Document your role hierarchy for other admins

## Related Configuration

- **[Rank Setup](./ranks.md)** - Create and manage permission ranks
- **[Command Permissions](./commands.md)** - Set rank requirements for commands
- **[Permission System](../../developer/concepts/core/permission-system.md)** - Technical details
