# Permission System

Tux uses a **rank-based permission system** that allows server administrators to control who can use which commands. This system is flexible, hierarchical, and completely customizable per server.

## Understanding Permission Ranks

### What Are Permission Ranks?

Permission ranks (0-7) represent a hierarchy of access levels in your server. Higher ranks have more permissions and can use more powerful commands.

!!! warning "Ranks vs Levels"
    **Don't confuse these!**

    - **Permission Ranks** (0-7): Control command access
    - **XP Levels**: User progression system for engagement
    
    These are completely separate systems!

### Default Rank Hierarchy

| Rank | Name               | Description                      | Typical Commands               |
|------|--------------------|----------------------------------|--------------------------------|
| **0** | Member             | Basic server member              | Info, fun, utility commands    |
| **1** | Trusted            | Trusted community member         | Bookmarks, advanced utility    |
| **2** | Junior Moderator   | Entry-level moderation           | Warn, timeout, jail            |
| **3** | Moderator          | Standard moderation              | Kick, ban, case management     |
| **4** | Senior Moderator   | Advanced moderation              | Unban, manage others' cases    |
| **5** | Administrator      | Server administration            | Config changes, permission management |
| **6** | Head Administrator | Full server control              | Advanced config, dangerous commands |
| **7** | Server Owner       | Complete access                  | Everything                     |

!!! note "Customizable"
    These are default names and descriptions. Your server can customize rank names, assignments, and even create custom ranks!

## How It Works

### Discord Roles → Permission Ranks

Tux maps Discord roles to permission ranks:

```
Discord Role "@Moderators" → Tux Rank 3 (Moderator)
```

Users with the @Moderators role automatically get Rank 3 permissions.

### Hierarchical System

Higher ranks inherit permissions from lower ranks:

- Rank 3 can do everything Rank 0-2 can do, plus Rank 3 commands
- Rank 7 (Server Owner) can do everything

### Multiple Roles

If a user has multiple roles with different ranks, they get the **highest rank**:

- User has @Trusted (Rank 1) and @Moderator (Rank 3)
- User gets Rank 3 permissions

## Setting Up Permissions

### Step 1: Initialize Permission System

First time setup:

```
/config rank init
```

This creates the default permission ranks (0-7) in your server's database.

### Step 2: Assign Roles to Ranks

Map your Discord roles to permission ranks:

```
/config role assign 3 @Moderators
/config role assign 5 @Admins
/config role assign 2 @Helpers
```

### Step 3: View Current Assignments

See what's configured:

```
/config role
```

This shows which Discord roles are assigned to which ranks.

### Step 4: Test Permissions

Have users try commands to verify permission ranks work correctly.

**Note:** There's no `/config rank check` command. To verify ranks:

1. Try using rank-restricted commands
2. Use `/help command_name` to see required rank
3. Admins can view all role assignments with `/config role`

## Advanced Permission Configuration

### Command-Specific Permissions

Override the default rank requirement for specific commands:

```
# Make /ping require rank 2 instead of default (0)
/config command permission ping 2

# Make /ban require rank 4 instead of default (3)
/config command permission ban 4
```

### Custom Rank Names

Rename ranks to match your server:

```
/config rank rename 2 "Helper"
/config rank rename 3 "Mod"
/config rank rename 5 "Admin"
```

### Permission Bypass

Server administrators with Discord's "Administrator" permission bypass Tux's rank system entirely (they have access to everything).

!!! warning "Use Carefully"
    Discord's Administrator permission is very powerful. Only give it to fully trusted users.

## Common Permission Setups

### Small Server (< 100 members)

Simple, flat structure:

- **Rank 0**: Everyone
- **Rank 3**: Moderators (basic moderation)
- **Rank 5**: Admins (full control)

```
/config rank init
/config role assign 3 @Moderators
/config role assign 5 @Admins
```

### Medium Server (100-1000 members)

Tiered moderation:

- **Rank 0**: Everyone
- **Rank 2**: Helpers (warn, timeout)
- **Rank 3**: Moderators (kick, ban)
- **Rank 4**: Senior Mods (unban, manage cases)
- **Rank 5**: Admins (config, permissions)

```
/config rank init
/config role assign 2 @Helpers
/config role assign 3 @Moderators
/config role assign 4 @Senior-Mods
/config role assign 5 @Admins
```

### Large Server (1000+ members)

Full hierarchy with specialized roles:

- **Rank 0**: Everyone
- **Rank 1**: Trusted Members
- **Rank 2**: Trial Moderators
- **Rank 3**: Moderators
- **Rank 4**: Senior Moderators
- **Rank 5**: Head Moderators
- **Rank 6**: Administrators
- **Rank 7**: Head Admin

```
/config rank init
/config role assign 1 @Trusted
/config role assign 2 @Trial-Mods
/config role assign 3 @Moderators
/config role assign 4 @Senior-Mods
/config role assign 5 @Head-Mods
/config role assign 6 @Admins
```

## Permission Checks

### How Tux Checks Permissions

When someone runs a command:

1. Tux checks if the user has Discord's "Administrator" permission → **Allow**
2. Tux finds all Discord roles the user has
3. Tux looks up the permission rank for each role
4. Tux uses the **highest rank** found
5. Tux compares the user's rank to the command's required rank
6. If user rank ≥ required rank → **Allow**, otherwise → **Deny**

### Debugging Permission Issues

If a command doesn't work:

```
# View all role-to-rank assignments
/config role

# View all ranks in the server
/config rank

# Check command's requirement
/help command_name

# Check command-specific overrides
/config command
```

## Commands by Required Rank

### Rank 0 (Everyone)

- `/ping` - Check bot latency
- `/level` - View your XP/level
- `/avatar` - View user avatars
- `/info` - Get information
- `/snippet` - Use text snippets
- `/afk` - Set AFK status
- `/xkcd` - View XKCD comics
- `/random` - Random commands
- `/wiki` - Search Wikipedia
- And most utility/info commands

### Rank 1 (Trusted)

- Bookmarks (react with 🔖) - Save messages
- Advanced utility features

### Rank 2 (Junior Moderator)

- `/warn` - Warn users
- `/timeout` - Timeout users
- `/untimeout` - Remove timeouts
- `/jail` - Jail users
- `/unjail` - Unjail users
- `/clearafk` - Clear someone's AFK

### Rank 3 (Moderator)

- `/ban` - Ban users
- `/kick` - Kick users
- `/tempban` - Temporary ban
- `/pollban` - Poll ban
- `/snippetban` - Ban from snippets
- `/cases` - View moderation cases
- `/report` - Handle reports
- `/purge` - Purge messages
- `/slowmode` - Set slowmode

### Rank 4 (Senior Moderator)

- `/unban` - Unban users
- `/pollunban` - Poll unban
- `/snippetunban` - Unban from snippets
- Edit others' moderation cases

### Rank 5 (Administrator)

- `/config` - Server configuration
- `/config rank` - Manage permission ranks
- `/levels set` - Set user XP/level
- Feature configuration

### Rank 6 (Head Administrator)

- Advanced configuration
- Dangerous operations

### Rank 7 (Server Owner)

- Everything
- No restrictions

!!! note "Command List"
    This is a general guide. Check individual command pages for exact requirements, which may vary or be customized per server.

## Best Practices

### Security

- **Principle of Least Privilege**: Give users the minimum rank they need
- **Regular Audits**: Review rank assignments periodically
- **Test Changes**: Test permission changes with test accounts
- **Document Decisions**: Keep notes on why roles have certain ranks

### Structure

- **Clear Hierarchy**: Make sure ranks form a logical progression
- **Role Names**: Use clear, descriptive names for Discord roles
- **Consistent Naming**: Keep Tux rank names and Discord role names similar
- **Document for Team**: Write down your permission structure for your mod team

### Common Pitfalls

❌ **Don't** give everyone Rank 7 (defeats the purpose)

❌ **Don't** skip ranks (e.g., only use 0, 3, and 7)

❌ **Don't** make moderation commands too restrictive (Rank 2-3 should handle basic moderation)

❌ **Don't** forget to test after making changes

✅ **Do** use the full 0-7 range for large servers

✅ **Do** give trial mods lower ranks (2) before promoting to full mod (3)

✅ **Do** reserve Rank 5+ for actual administrators

✅ **Do** document your setup for your team

## Troubleshooting

### "Missing Permissions" Error

**Cause**: User's rank is too low for the command

**Solution**:

1. View role assignments: `/config role` to see all role-to-rank mappings
2. Check command requirement: `/help command_name`
3. If appropriate, assign higher rank to user's role

### Command Works for Some Mods But Not Others

**Cause**: Inconsistent role assignments

**Solution**:

1. List all role assignments: `/config role`
2. Check which roles each mod has in Discord
3. Ensure all mods have appropriate roles
4. Assign missing roles or adjust rank assignments

### Administrator Can't Use Command

**Cause**: Might be a bug or missing permission

**Solution**:

1. Verify they have Discord "Administrator" permission (should bypass all checks)
2. Try the command in different channels
3. Check bot's Discord permissions
4. Report if issue persists

### Rank Assignments Not Working

**Cause**: Ranks not initialized or roles not synced

**Solution**:

```
# Reinitialize ranks
/config rank init

# Assign roles to ranks
/config role assign <rank_number> @RoleName

# Verify
/config role
```

## FAQs

### Can I have more than 8 ranks?

No, Tux uses a fixed 0-7 system (8 ranks total). However, you can assign multiple Discord roles to the same rank.

### Can I remove default ranks?

No, all 8 ranks (0-7) always exist. You don't have to use all of them, though.

### Do rank names affect functionality?

No, rank names are purely cosmetic. The numbers (0-7) determine permissions.

### Can users have multiple ranks?

Users get one effective rank: the **highest** rank from all their Discord roles.

### How does this work with Discord's permission system?

Tux permissions are **additional** to Discord permissions. Users need both:

- **Discord permissions**: Bot-level permissions (e.g., can the user use slash commands?)
- **Tux permissions**: Command-level permissions (e.g., can the user use `/ban`?)

Both must be satisfied for a command to work.

### Can I export/import permission configs?

Not yet, but this is planned. For now, document your setup manually if migrating servers.

## Related Resources

- **[Configuration Commands](commands/config.md)** - Manage ranks with commands
- **[Moderation Commands](commands/moderation.md)** - Commands that require higher ranks
- **[Admin Guide](../admin-guide/configuration/permissions.md)** - Self-hosting permission setup

## Need Help?

- **[Discord Support](https://discord.gg/gpmSjcjQxg)** - Ask in #support
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs
- **[FAQ](../community/faq.md)** - Common questions

---

**Next Steps:**

- **[Set Up Your Server](commands/config.md)** - Configure Tux
- **[Browse Commands](commands/moderation.md)** - See what each rank can do
- **[Learn Features](features/xp-system.md)** - Explore Tux capabilities
