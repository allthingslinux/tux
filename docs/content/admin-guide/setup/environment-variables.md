# Environment Variables

Configure Tux using environment variables in your `.env` file.

## Creating .env File

The `.env` file stores sensitive configuration and is git-ignored for security.

### Generate Example

```bash
# Generate .env.example with all options
uv run config generate

# Copy to create your .env
cp .env.example .env

# Edit with your settings
nano .env
```

### File Permissions

Secure your `.env` file:

```bash
chmod 600 .env
```

## Required Variables

These variables are required for Tux to start:

### Discord

```bash
# Your Discord bot token (from Developer Portal)
BOT_TOKEN=your_discord_bot_token_here
```

**[How to get →](discord-bot-token.md)**

### Database

```bash
# PostgreSQL connection details
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=ChangeThisToAStrongPassword123!
```

**For Docker:** Use `POSTGRES_HOST=tux-postgres` (container name)

**Alternative:** Use single connection URL:

```bash
DATABASE_URL=postgresql://tuxuser:password@localhost:5432/tuxdb
```

## Optional Variables

### Bot Configuration

```bash
# Bot display name
BOT_INFO__BOT_NAME=Tux

# Command prefix (default: $)
BOT_INFO__PREFIX=$

# Hide bot owner in /info command
BOT_INFO__HIDE_BOT_OWNER=false

# Bot activities (rotating status messages)
BOT_INFO__ACTIVITIES=[]
```

### User IDs

```bash
# Bot owner Discord user ID
USER_IDS__BOT_OWNER_ID=123456789012345678

# System administrators (for eval command)
USER_IDS__SYSADMINS=[]
```

### Environment & Debug

```bash
# Environment name (development, staging, production)
ENVIRONMENT=production

# Enable debug logging
DEBUG=false

# Allow sysadmins to use eval command (dangerous!)
ALLOW_SYSADMINS_EVAL=false
```

## Feature Configuration

### XP System

```bash
# Channels where XP is disabled
XP_CONFIG__XP_BLACKLIST_CHANNELS=[]

# Role rewards at certain levels
XP_CONFIG__XP_ROLES=[]

# XP multipliers for certain roles
XP_CONFIG__XP_MULTIPLIERS=[]

# Cooldown between XP gains (seconds)
XP_CONFIG__XP_COOLDOWN=60

# Level difficulty curve
XP_CONFIG__LEVELS_EXPONENT=2.0

# Show XP progress messages
XP_CONFIG__SHOW_XP_PROGRESS=true

# Cap XP at max configured level
XP_CONFIG__ENABLE_XP_CAP=false
```

**Note:** XP_ROLES must be configured for XP system to work. Use config file (TOML/YAML/JSON) for complex structures.

### Status Roles

```bash
# Map Discord status to role IDs
STATUS_ROLES__MAPPINGS=[]
```

Example in config.toml:

```toml
[status_roles]
mappings = [
    { status = "online", role_id = 123456 },
    { status = "streaming", role_id = 789012 },
]
```

### Temp VC

```bash
# Creator channel ID
TEMPVC__TEMPVC_CHANNEL_ID=123456789

# Category for temp VCs
TEMPVC__TEMPVC_CATEGORY_ID=987654321
```

### GIF Limiter

```bash
# How recent a GIF must be to count (seconds)
GIF_LIMITER__RECENT_GIF_AGE=60

# Per-user GIF limits
GIF_LIMITER__GIF_LIMITS_USER={}

# Per-channel GIF limits
GIF_LIMITER__GIF_LIMITS_CHANNEL={}

# Channels/users to exclude
GIF_LIMITER__GIF_LIMIT_EXCLUDE=[]
```

### Snippets

```bash
# Limit snippet access to specific roles
SNIPPETS__LIMIT_TO_ROLE_IDS=false

# Role IDs that can access snippets
SNIPPETS__ACCESS_ROLE_IDS=[]
```

## External Services

### Sentry (Error Tracking)

```bash
EXTERNAL_SERVICES__SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

**[Get Sentry DSN →](https://sentry.io)**

### GitHub Integration

```bash
# GitHub App credentials
EXTERNAL_SERVICES__GITHUB_APP_ID=123456
EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID=789012
EXTERNAL_SERVICES__GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
EXTERNAL_SERVICES__GITHUB_CLIENT_ID=your_client_id
EXTERNAL_SERVICES__GITHUB_CLIENT_SECRET=your_secret

# Repository info
EXTERNAL_SERVICES__GITHUB_REPO_URL=https://github.com/org/repo
EXTERNAL_SERVICES__GITHUB_REPO_OWNER=org
EXTERNAL_SERVICES__GITHUB_REPO=repo
```

### Wolfram Alpha

```bash
EXTERNAL_SERVICES__WOLFRAM_APP_ID=your_wolfram_app_id
```

**[Get App ID →](https://developer.wolframalpha.com/)**

### InfluxDB Metrics

```bash
EXTERNAL_SERVICES__INFLUXDB_TOKEN=your_token
EXTERNAL_SERVICES__INFLUXDB_URL=http://influxdb:8086
EXTERNAL_SERVICES__INFLUXDB_ORG=your_org
```

### Mailcow (ATL-specific)

```bash
EXTERNAL_SERVICES__MAILCOW_API_KEY=your_key
EXTERNAL_SERVICES__MAILCOW_API_URL=https://mail.example.com
```

## Variable Naming Convention

Tux uses double underscore (`__`) for nested configuration:

```bash
# Translates to: BOT_INFO.PREFIX
BOT_INFO__PREFIX=$

# Translates to: EXTERNAL_SERVICES.SENTRY_DSN
EXTERNAL_SERVICES__SENTRY_DSN=...
```

This is pydantic-settings convention for nested models.

## Configuration Priority

Environment variables have **highest priority**:

1. **Environment variables** (.env file) ← Highest
2. Config file (config.toml/yaml/json)
3. Default values ← Lowest

Variables in `.env` override everything else.

## Example Complete .env

```bash
### Required Configuration
BOT_TOKEN=MTE...your_token_here
POSTGRES_HOST=tux-postgres
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=SuperSecurePassword123!

### Optional Configuration
ENVIRONMENT=production
DEBUG=false
BOT_INFO__PREFIX=$
BOT_INFO__BOT_NAME=Tux
USER_IDS__BOT_OWNER_ID=123456789012345678

### External Services (Optional)
EXTERNAL_SERVICES__SENTRY_DSN=https://xxx@sentry.io/123
EXTERNAL_SERVICES__WOLFRAM_APP_ID=YOUR-APP-ID

### Features (Configure in config.toml instead)
# XP_CONFIG__XP_COOLDOWN=60
# XP_CONFIG__LEVELS_EXPONENT=2.0
```

## Best Practices

### Security

✅ **Do:**

- Use strong database passwords
- Never commit `.env` to Git
- Set file permissions to 600
- Rotate secrets regularly
- Use different passwords per environment

❌ **Don't:**

- Share .env files
- Use default passwords in production
- Commit secrets to version control
- Reuse passwords across services

### Organization

- Group related variables together
- Comment complex settings
- Use meaningful values
- Document custom settings

### Multi-Environment

For multiple environments (dev/staging/prod):

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production

# Copy appropriate file
cp .env.production .env
```

## Troubleshooting

### Variables Not Loading

**Cause:** Syntax error in .env

**Solution:**

- No spaces around `=`
- Quote values with special characters
- One variable per line
- No comments on same line as variable

### Nested Variables Not Working

**Cause:** Wrong separator

**Solution:**

Use double underscore:

```bash
BOT_INFO__PREFIX=$              # ✅ Correct
BOT_INFO.PREFIX=$               # ❌ Wrong
BOT_INFO_PREFIX=$               # ❌ Wrong
```

### Complex Values

For arrays/objects, use config files instead:

```toml
# config.toml
[xp_config]
xp_roles = [
    { level = 5, role_id = 123456 },
    { level = 10, role_id = 789012 },
]
```

## Generating .env.example

The `.env.example` is auto-generated:

```bash
uv run config generate
```

This creates `.env.example` with all available options from the pydantic models.

## Related Documentation

- **[Config Files](config-files.md)** - TOML/YAML/JSON configuration
- **[Configuration Reference](../../reference/configuration.md)** - All options
- **[Security](../security/token-security.md)** - Securing secrets

---

**Next:** [Configure with config files →](config-files.md)
