# Bot Settings

Configure bot-wide settings like prefix, name, and activities.

## Bot Information

Configure in `config.toml` or `.env`:

```toml
[bot_info]
bot_name = "Tux"                    # Bot display name
prefix = "$"                        # Default command prefix
hide_bot_owner = false              # Show owner in /info
activities = [                      # Rotating status messages
    "with Linux",
    "Helping the community",
]
```

## Command Prefix

**Default:** `$`

**Configure:**

- Globally: `BOT_INFO__PREFIX` in `.env`
- Per-server: `/config wizard` or database

## Bot Activities

Rotating status messages shown under bot's name.

Supports placeholders:

- `{guilds}` - Number of servers
- `{users}` - Total user count  
- `{prefix}` - Current prefix

Example:

```toml
activities = [
    "with {users} Linux users",
    "in {guilds} servers",
    "Type {prefix}help",
]
```

## Related

- **[Environment Variables](../setup/environment-variables.md)**
- **[Config Files](../setup/config-files.md)**

---

*Full documentation in progress. See [Configuration Reference](../../reference/configuration.md) for all options.*
