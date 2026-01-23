---
title: Self-Host Configuration
tags:
  - selfhost
  - configuration
---

# Self-Host Configuration

Configure your Tux self-hosted instance to match your server's needs. This section covers all configuration aspects from bot tokens to database settings.

## Configuration Overview

Tux uses a flexible configuration system that supports multiple sources:

1. **Environment Variables** - Highest priority, loaded from `.env` or system environment
2. **JSON Configuration** - `config/config.json` or `config.json` for structured settings
3. **File Secrets** - Docker secrets or mounted secret files
4. **Defaults** - Built-in defaults when no other source provides a value

See [Environment Configuration](environment.md) for details on configuration priority and loading order.

## Essential Configuration

### [Bot Token](bot-token.md)

Configure your Discord bot token and permissions. This is required for Tux to connect to Discord.

**Quick Setup:**

1. Get token from [Discord Developer Portal](https://discord.com/developers/applications)
2. Add to `.env`: `BOT_TOKEN=your_token_here`
3. Invite bot to your server with appropriate permissions

### [Database Configuration](database.md)

Configure PostgreSQL connection settings. Tux requires PostgreSQL 17+.

**Quick Setup:**

- **Docker**: Set `POSTGRES_PASSWORD` in `.env` - database configures automatically
- **Bare Metal**: Configure `POSTGRES_*` variables or use `DATABASE_URL`

### [Environment Variables](environment.md)

Complete guide to environment variable configuration, including:

- Configuration priority and loading order
- Essential variables
- Docker-specific configuration
- Validation and testing

## Configuration Files

### `.env` File

Primary configuration file for environment variables:

```env
# Required
BOT_TOKEN=your_bot_token_here

# Database (optional - defaults provided)
POSTGRES_PASSWORD=your_secure_password_here

# Optional
LOG_LEVEL=INFO
DEBUG=false
USER_IDS__BOT_OWNER_ID=123456789012345678
```

### `config/config.json`

JSON configuration file for structured settings:

```json
{
  "BOT_INFO": {
    "BOT_NAME": "Tux",
    "PREFIX": "$"
  },
  "BOT_INTENTS": {
    "presences": true,
    "members": true,
    "message_content": true
  }
}
```

Generate example files:

```bash
uv run config generate
```

## Configuration Validation

Always validate your configuration before starting:

```bash
# Validate configuration
uv run config validate

# Test database connection
uv run db health
```

## Configuration Priority

Configuration is loaded in this order (highest to lowest priority):

1. **Init settings** - Programmatic overrides
2. **Environment variables** - System environment
3. **`.env` file** - Local environment file
4. **`config/config.json`** or **`config.json`** - JSON configuration
5. **File secrets** - Docker secrets (`/run/secrets`)
6. **Defaults** - Built-in default values

## Common Configuration Tasks

### Change Bot Prefix

```env
# In .env
BOT_INFO__PREFIX=!
```

Or in `config/config.json`:

```json
{
  "BOT_INFO": {
    "PREFIX": "!"
  }
}
```

### Configure Bot Intents

```json
{
  "BOT_INTENTS": {
    "presences": true,
    "members": true,
    "message_content": true
  }
}
```

All three privileged intents are required for full functionality:

- **presences**: Required for status_roles feature
- **members**: Required for on_member_join, jail, tty_roles
- **message_content**: Required for prefix commands and most features

### Set Log Level

```env
# In .env
LOG_LEVEL=DEBUG
```

Valid levels: `TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, `CRITICAL`

### Configure HTTP Client

For high-latency environments, Tux automatically configures the HTTP client with appropriate timeouts and connection settings. No manual configuration needed.

## Docker-Specific Configuration

When using Docker Compose:

- Variables in `.env` are automatically loaded
- `compose.yaml` sets `POSTGRES_HOST=tux-postgres` automatically
- Use profiles (`--profile dev` or `--profile production`) to select deployment mode
- See [Docker Installation](../install/docker.md) for details

## Troubleshooting

### Configuration Not Loading

```bash
# Check what's being loaded
uv run config validate

# Verify file paths
ls -la .env config/config.json

# Check file encoding (must be UTF-8)
file .env
```

### Environment Variables Not Working

- Use `__` (double underscore) for nested keys: `BOT_INFO__PREFIX`
- Check variable names match exactly (case-insensitive)
- Verify `.env` file is in the correct location
- For Docker, ensure variables are in `.env` file

### Database Configuration Issues

- Verify `POSTGRES_*` variables or `DATABASE_URL` is set
- Check database is running and accessible
- Test connection: `uv run db health`
- For Docker, `POSTGRES_HOST` is set automatically

## Related Documentation

- [Environment Variables](environment.md) - Complete environment variable guide
- [Database Configuration](database.md) - Database setup and configuration
- [Bot Token Setup](bot-token.md) - Obtaining and configuring bot token
- [ENV Reference](../../reference/env.md) - Auto-generated reference for all variables
- [Docker Installation](../install/docker.md) - Docker-specific configuration
- [First Run Setup](../install/first-run.md) - Initial configuration verification
