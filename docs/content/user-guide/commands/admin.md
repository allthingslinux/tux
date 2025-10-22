# Admin & Dev Commands

Administrative and development commands for bot management.

!!! danger "Dangerous Commands"
    These commands can affect bot behavior and should only be used by trusted administrators and developers.

## Development Commands

### Dev

Group command for development operations.

**Usage:**

```text
/dev
$dev
```

**Aliases:** `d`

**Permission:** Rank 7 (Server Owner) or Bot Owner

**Subcommands:**

- `sync_tree` - Sync slash commands with Discord
- And other dev operations

---

### Dev Sync Tree

Sync slash commands with Discord's command tree.

**Usage:**

```text
/dev sync_tree
$dev sync_tree
```

**Aliases:** `st`, `sync`, `s`

**Permission:** Rank 7 (Server Owner) or Bot Owner

**When to Use:**

- After adding new slash commands
- Commands not showing in Discord
- After bot update
- Fixing command registration issues

**Notes:**

- Takes a few moments to propagate
- Updates global and guild commands
- Should not be needed frequently

---

### Eval

Execute Python code (for bot owners).

**Usage:**

```text
$eval print("test")
```

**Aliases:** `e`

**Permission:** Bot Owner only (restricted by ALLOW_SYSADMINS_EVAL)

**Security:**

- **Extremely dangerous** - can execute arbitrary code
- Only bot owner can use
- Can break the bot
- Use with extreme caution

**Note:** Prefix-only command

---

## Permission Requirements

| Command      | Minimum Rank | Additional Requirements |
|-------------|-------------|--------------------------|
| dev         | 7           | Server Owner or Bot Owner |
| dev sync_tree| 7          | Server Owner or Bot Owner |
| eval        | -           | Bot Owner only           |

## Security Notes

!!! danger "Eval Security"
    The `eval` command can execute arbitrary Python code and has full access to the bot's internals. **Only the bot owner should ever have access to this command.**

!!! warning "Sync Tree Sparingly"
    Don't spam sync_tree - Discord has rate limits. Only use when necessary.

!!! info "Development Mode"
    These commands are primarily for development and debugging. Regular users should never need them.

## When to Use These Commands

### Sync Tree

Use after:

- Bot update with new commands
- Command changes
- Slash commands not appearing
- Manual sync requested by developer

**Don't use:**

- Randomly or frequently
- Without reason
- During normal operation

### When to Use Eval

Use for:

- Emergency debugging
- Quick database queries
- Testing code snippets
- Inspecting bot state

**Don't use:**

- For normal operations
- If you don't understand the code
- Without backups
- In production (unless emergency)

## Troubleshooting

### Sync Tree Not Working

**Cause:** Discord API issues or rate limits

**Solution:**

- Wait 1 hour and try again
- Check Discord API status
- Restart bot
- Check bot token permissions

### Eval Permission Denied

**Cause:** Not the bot owner

**Solution:**

- Only bot owner can use eval
- Set `ALLOW_SYSADMINS_EVAL=true` to allow sysadmins (not recommended)
- Use proper development practices instead

## For Bot Owners

If you're self-hosting:

- **Be Careful with Eval** - Can break your bot
- **Sync Tree After Updates** - When adding/changing commands
- **Monitor Bot Logs** - Watch for issues after using these commands
- **Have Backups** - Before eval-ing risky code

## Related Documentation

- **[Developer Guide](../../developer-guide/index.md)** - Full development docs
- **[Self-Hosting](../../admin-guide/index.md)** - Admin documentation

---

**That's all commands!** Check out the [Features](../features/xp-system.md) section to learn about Tux's capabilities.
