# Configuration Files

Tux supports multiple configuration file formats: TOML, YAML, and JSON.

## Why Use Config Files?

While `.env` is great for secrets and simple values, config files are better for:

- Complex structures (arrays, nested objects)
- Feature configuration (XP roles, status mappings)
- Commented configuration
- Version control (non-sensitive settings)
- Readability

## Generating Config Files

### Auto-Generate

```bash
# Generate all formats
uv run config generate

# Generate specific format
uv run config generate --format toml
uv run config generate --format yaml
uv run config generate --format json
```

Creates:

- `config/config.toml.example`
- `config/config.yaml.example`
- `config/config.json.example`

### Create Your Config

```bash
# Copy example
cp config/config.toml.example config/config.toml

# Edit
nano config/config.toml
```

## Supported Formats

### TOML (Recommended)

**File:** `config/config.toml`

```toml
# Bot settings
debug = false

[bot_info]
bot_name = "Tux"
prefix = "$"
hide_bot_owner = false
activities = [
    "with Linux",
    "Helping the community",
]

[xp]
xp_cooldown = 60
levels_exponent = 2.0
show_xp_progress = true
enable_xp_cap = false

# XP role rewards
xp_roles = [
    { level = 5, role_id = 1234567890 },
    { level = 10, role_id = 2345678901 },
    { level = 25, role_id = 3456789012 },
]

# XP multipliers for boosters/donors
xp_multipliers = [
    { role_id = 5678901234, multiplier = 1.5 },
]

xp_blacklist_channels = [9876543210]

[status_roles]
mappings = [
    { status = "online", role_id = 1111222233 },
    { status = "streaming", role_id = 2222333344 },
]

[external_services]
sentry_dsn = "https://your-sentry-dsn@sentry.io/project"
wolfram_app_id = "YOUR-WOLFRAM-ID"
```

### YAML

**File:** `config/config.yaml`

```yaml
debug: false

bot_info:
  bot_name: Tux
  prefix: "$"
  activities:
    - with Linux
    - Helping the community

xp:
  xp_cooldown: 60
  levels_exponent: 2.0
  xp_roles:
    - level: 5
      role_id: 1234567890
    - level: 10
      role_id: 2345678901

status_roles:
  mappings:
    - status: online
      role_id: 1111222233
```

### JSON

**File:** `config/config.json`

```json
{
  "debug": false,
  "bot_info": {
    "bot_name": "Tux",
    "prefix": "$",
    "activities": ["with Linux"]
  },
  "xp": {
    "xp_cooldown": 60,
    "xp_roles": [
      {"level": 5, "role_id": 1234567890},
      {"level": 10, "role_id": 2345678901}
    ]
  }
}
```

## Configuration Priority

When multiple config sources exist:

1. **Environment variables** (.env) - Highest priority
2. Config file (config.toml/yaml/json)
3. Default values - Lowest priority

Example:

- `.env` has `BOT_INFO__PREFIX=!`
- `config.toml` has `prefix = "$"`
- Result: Bot uses `!` (env var wins)

## Which Format to Choose?

### TOML (Recommended)

✅ **Use if:**

- You want comments in config
- Prefer human-readable format
- Need nested structures
- Standard for Python projects

### YAML

✅ **Use if:**

- Familiar with YAML from Docker/K8s
- Want minimal syntax
- Prefer indentation-based structure

### JSON

✅ **Use if:**

- Need machine-readable format
- Integrating with other systems
- Want strict structure validation

**All formats work equally well** - choose based on preference!

## Common Configuration

### XP System

```toml
[xp]
xp_cooldown = 60                    # Seconds between XP gains
levels_exponent = 2.0               # Level difficulty curve
show_xp_progress = false            # Don't spam level-up messages
enable_xp_cap = true                # Stop XP at max level

# Role rewards
xp_roles = [
    { level = 5, role_id = 1234567890 },
    { level = 10, role_id = 2345678901 },
    { level = 25, role_id = 3456789012 },
    { level = 50, role_id = 4567890123 },
]

# Booster bonus
xp_multipliers = [
    { role_id = 5678901234, multiplier = 1.5 },  # 50% bonus for boosters
]

# Disable XP in spam channels
xp_blacklist_channels = [9876543210, 1234567890]
```

### Status Roles

```toml
[status_roles]
mappings = [
    { status = "online", role_id = 1111222233 },
    { status = "idle", role_id = 2222333344 },
    { status = "dnd", role_id = 3333444455 },
    { status = "streaming", role_id = 4444555566 },
]
```

### Bot Activities

```toml
[bot_info]
activities = [
    "with Linux users",
    "Moderating servers",
    "Helping the community",
    "Type /help for commands",
]
```

Bot will rotate through these status messages.

## Secrets vs Configuration

### Put in .env (Secrets)

- BOT_TOKEN
- POSTGRES_PASSWORD
- SENTRY_DSN
- API keys
- Anything sensitive

### Put in config file (Settings)

- XP roles and configuration
- Status role mappings
- Bot activities
- Feature enable/disable
- Non-sensitive settings

## Validation

Tux validates configuration on startup:

- Type checking (integers, strings, booleans)
- Required fields
- Value ranges
- Format validation

Check logs for validation errors:

```bash
docker compose logs tux | grep -i error
```

## Tips

!!! tip "Start with Examples"
    Generate examples with `uv run config generate` and customize from there.

!!! tip "Comment Your Config"
    TOML and YAML support comments - document why you chose certain values!

!!! tip "Version Control Config Structure"
    Commit `config.toml` (without secrets) to share configuration structure with your team.

!!! warning "Don't Commit Secrets"
    Even in config files, don't commit sensitive values. Use environment variables for those.

## Troubleshooting

### Config Not Loading

**Causes:**

- Syntax error in config file
- File not in `config/` directory
- Wrong file extension

**Solutions:**

- Validate TOML/YAML/JSON syntax
- Place in `config/` folder
- Check file name matches expected

### Values Not Applied

**Cause:** Environment variable override

**Solution:**

Environment variables have higher priority. Check `.env` for overrides.

### Complex Structures Not Working

**Cause:** Can't express in env vars

**Solution:**

Use config files for arrays and nested objects:

```toml
# ✅ Works in TOML
xp_roles = [
    { level = 5, role_id = 123 },
]

# ❌ Can't do this cleanly in .env
```

## Example Configurations

### Minimal (Development)

```toml
[bot_info]
prefix = "$"
bot_name = "Tux Dev"

[xp]
xp_cooldown = 30
```

### Full (Production)

```toml
debug = false

[bot_info]
bot_name = "Tux"
prefix = "$"
hide_bot_owner = false
activities = [
    "with Linux",
    "Type /help",
    "Moderating {guilds} servers",
]

[user_ids]
bot_owner_id = 123456789012345678
sysadmins = []

[xp]
xp_cooldown = 60
levels_exponent = 2.0
show_xp_progress = true
enable_xp_cap = true

xp_roles = [
    { level = 5, role_id = 1001 },
    { level = 10, role_id = 1002 },
    { level = 25, role_id = 1003 },
    { level = 50, role_id = 1004 },
    { level = 100, role_id = 1005 },
]

xp_multipliers = [
    { role_id = 2001, multiplier = 1.5 },
]

xp_blacklist_channels = [3001, 3002]

[status_roles]
mappings = [
    { status = "streaming", role_id = 4001 },
]

[gif_limiter]
recent_gif_age = 60

[external_services]
sentry_dsn = "https://xxx@sentry.io/123"
wolfram_app_id = "APPID"
```

## Related Documentation

- **[Environment Variables](environment-variables.md)** - .env configuration
- **[Configuration Reference](../../reference/configuration.md)** - All options documented
- **[Features Configuration](../configuration/features.md)** - Feature-specific setup

---

**Next:** [First run guide →](first-run.md)
