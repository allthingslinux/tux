---
title: Environment Configuration
tags:
  - selfhost
  - configuration
  - environment
---

# Environment Configuration

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Configure Tux using environment variables for different deployment scenarios.

!!! tip "Configuration Priority"
    Configuration is loaded in this priority order (highest to lowest):
    1. Environment variables
    2. `.env` file
    3. `config.toml` file
    4. `config.yaml` file
    5. `config.json` file
    6. Default values

    See the **[Complete ENV Reference](../../reference/env.md)** for all available variables.

## Core Configuration

### Discord Bot Settings

    # Required: Discord bot token
    BOT_TOKEN=your_bot_token_here

    # Bot prefix (default: $)
    BOT_INFO__PREFIX=$

    # Bot owner user ID
    USER_IDS__BOT_OWNER_ID=123456789012345678

    # System admin user IDs (comma-separated)
    USER_IDS__SYSADMINS=123456789012345678,987654321098765432

### Database Configuration

Tux uses PostgreSQL. You can configure it using individual variables or a connection URL:

#### Option 1: Individual PostgreSQL Variables (Recommended)

    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=tuxdb
    POSTGRES_USER=tuxuser
    POSTGRES_PASSWORD=your_secure_password_here

#### Option 2: Database URL Override

    # Custom database URL (overrides individual POSTGRES_* variables)
    DATABASE_URL=postgresql://user:password@localhost:5432/tuxdb

!!! warning "Security"
    Always use strong passwords for PostgreSQL. The default password is insecure and should be changed immediately.

## Logging Configuration

    # Log level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
    LOG_LEVEL=INFO

    # Enable debug mode
    DEBUG=false

## Bot Information

    # Bot display name
    BOT_INFO__BOT_NAME=Tux

    # Bot activities (JSON array)
    BOT_INFO__ACTIVITIES=[{"type": 0, "name": "with Linux"}]

    # Hide bot owner information
    BOT_INFO__HIDE_BOT_OWNER=false

## Feature Configuration

### XP System

    # XP cooldown in seconds
    XP_CONFIG__XP_COOLDOWN=1

    # XP blacklist channels (comma-separated channel IDs)
    XP_CONFIG__XP_BLACKLIST_CHANNELS=123456789012345678,987654321098765432

    # Show XP progress
    XP_CONFIG__SHOW_XP_PROGRESS=true

    # Enable XP cap
    XP_CONFIG__ENABLE_XP_CAP=false

### Snippets

    # Limit snippets to specific roles
    SNIPPETS__LIMIT_TO_ROLE_IDS=false

    # Snippet access role IDs (comma-separated)
    SNIPPETS__ACCESS_ROLE_IDS=123456789012345678

### Temporary Voice Channels

    # Temporary VC channel ID
    TEMPVC__TEMPVC_CHANNEL_ID=123456789012345678

    # Temporary VC category ID
    TEMPVC__TEMPVC_CATEGORY_ID=123456789012345678

### GIF Limiter

    # Recent GIF age limit (seconds)
    GIF_LIMITER__RECENT_GIF_AGE=60

    # Excluded channels from GIF limits (comma-separated)
    GIF_LIMITER__GIF_LIMIT_EXCLUDE=123456789012345678

## External Services

### Sentry (Error Tracking)

    EXTERNAL_SERVICES__SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

### GitHub Integration

    # GitHub App ID
    EXTERNAL_SERVICES__GITHUB_APP_ID=123456

    # GitHub Installation ID
    EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID=12345678

    # GitHub Private Key (base64 encoded or raw)
    EXTERNAL_SERVICES__GITHUB_PRIVATE_KEY=your_private_key_here

    # GitHub OAuth Client ID
    EXTERNAL_SERVICES__GITHUB_CLIENT_ID=your_client_id

    # GitHub OAuth Client Secret
    EXTERNAL_SERVICES__GITHUB_CLIENT_SECRET=your_client_secret

    # GitHub Repository URL
    EXTERNAL_SERVICES__GITHUB_REPO_URL=https://github.com/owner/repo

    # GitHub Repository Owner
    EXTERNAL_SERVICES__GITHUB_REPO_OWNER=owner

    # GitHub Repository Name
    EXTERNAL_SERVICES__GITHUB_REPO=repo

### InfluxDB (Metrics)

    EXTERNAL_SERVICES__INFLUXDB_URL=http://localhost:8086
    EXTERNAL_SERVICES__INFLUXDB_TOKEN=your_token
    EXTERNAL_SERVICES__INFLUXDB_ORG=your_org

### Other Services

    # Mailcow API
    EXTERNAL_SERVICES__MAILCOW_API_KEY=your_api_key
    EXTERNAL_SERVICES__MAILCOW_API_URL=https://mail.example.com/api/v1

    # Wolfram Alpha
    EXTERNAL_SERVICES__WOLFRAM_APP_ID=your_app_id

## Advanced Configuration

### System Administration

    # Allow sysadmins to use eval command
    ALLOW_SYSADMINS_EVAL=false

### Status Roles

    # Status to role mappings (JSON array)
    STATUS_ROLES__MAPPINGS=[{"status": "online", "role_id": 123456789012345678}]

### IRC Bridge

    # IRC bridge webhook IDs (comma-separated)
    IRC_CONFIG__BRIDGE_WEBHOOK_IDS=123456789012345678,987654321098765432

## Docker Configuration

### Docker Compose

    version: '3.8'
    services:
      tux:
        image: tux:latest
        environment:
          - BOT_TOKEN=${BOT_TOKEN}
          - POSTGRES_HOST=tux-postgres
          - POSTGRES_DB=tuxdb
          - POSTGRES_USER=tuxuser
          - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
          - LOG_LEVEL=INFO
        depends_on:
          - tux-postgres

### Docker Environment File

    # .env file for Docker
    BOT_TOKEN=your_bot_token_here
    POSTGRES_HOST=tux-postgres
    POSTGRES_DB=tuxdb
    POSTGRES_USER=tuxuser
    POSTGRES_PASSWORD=your_secure_password
    LOG_LEVEL=INFO

## Validation

### Check Configuration

    # Validate environment variables
    uv run config validate

    # Test database connection
    uv run db health

### Environment Testing

    # Load environment and test
    source .env
    uv run tux start --debug

## Troubleshooting

### Common Issues

**Missing required variables:**

- Check all required variables are set (`BOT_TOKEN`, database credentials)
- Verify variable names are correct (use `BOT_TOKEN`, not `DISCORD_TOKEN`)
- Check for typos in variable names

**Database connection errors:**

- Verify `POSTGRES_*` variables or `DATABASE_URL` format
- Check database server is running
- Test network connectivity
- Ensure database exists and user has proper permissions

**Permission errors:**

- Check file permissions on config files
- Verify user has access to directories
- Check systemd service permissions

**Nested configuration:**

- Use double underscore (`__`) for nested fields (e.g., `BOT_INFO__PREFIX`)
- Check the **[ENV Reference](../../reference/env.md)** for correct variable names

## Next Steps

After configuring environment variables:

- [Database Configuration](database.md) - Database setup
- [First Run Setup](../install/first-run.md) - Initial configuration
- [System Operations](../manage/operations.md) - Monitoring and maintenance

---

For a complete list of all environment variables, see the **[ENV Reference](../../reference/env.md)**.
