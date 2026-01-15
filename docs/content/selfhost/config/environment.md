---
title: Environment Configuration
tags:
  - selfhost
  - configuration
  - environment
---

# Environment Configuration

Configure Tux using environment variables for different deployment scenarios.

!!! tip "Configuration Priority"
    Configuration loads in this priority order (highest to lowest):
    1. Environment variables
    2. `.env` file
    3. `config/config.toml` or `config.toml` file
    4. `config/config.yaml` or `config.yaml` file
    5. `config/config.json` or `config.json` file
    6. Default values

    See the **[Complete ENV Reference](../../reference/env.md)** for all available variables.

## Core Configuration

### Discord Bot Settings

Set your Discord bot token and basic bot settings:

    ```env
    # Required: Discord bot token
    BOT_TOKEN=your_bot_token_here

    # Bot prefix (default: $)
    BOT_INFO__PREFIX=$

    # Bot owner user ID
    USER_IDS__BOT_OWNER_ID=123456789012345678

    # System admin user IDs (JSON array)
    USER_IDS__SYSADMINS=[123456789012345678,987654321098765432]
    ```

### Database Configuration

Tux uses PostgreSQL. Configure it using individual variables or a connection URL:

#### Option 1: Individual PostgreSQL Variables (Recommended)

    ```env
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=tuxdb
    POSTGRES_USER=tuxuser
    POSTGRES_PASSWORD=your_secure_password_here
    ```

#### Option 2: Database URL Override

    ```env
    # Custom database URL (overrides individual POSTGRES_* variables)
    DATABASE_URL=postgresql://user:password@localhost:5432/tuxdb
    ```

!!! warning "Security"
    Always use strong passwords for PostgreSQL. Change the default password immediately in production.

See [Database Configuration](database.md) for detailed database setup.

### Logging Configuration

Control logging behavior:

    ```env
    # Log level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
    LOG_LEVEL=INFO

    # Enable debug mode
    DEBUG=false
    ```

### Bot Information

Configure bot display settings:

    ```env
    # Bot display name
    BOT_INFO__BOT_NAME=Tux

    # Bot activities (JSON array)
    BOT_INFO__ACTIVITIES=[{"type":"playing","name":"with Linux"}]

    # Hide bot owner information
    BOT_INFO__HIDE_BOT_OWNER=false
    ```

## Feature Configuration

### XP System

Configure the experience point system:

    ```env
    # XP cooldown in seconds
    XP_CONFIG__XP_COOLDOWN=1

    # XP blacklist channels (JSON array)
    XP_CONFIG__XP_BLACKLIST_CHANNELS=[123456789012345678,987654321098765432]

    # Show XP progress
    XP_CONFIG__SHOW_XP_PROGRESS=true

    # Enable XP cap
    XP_CONFIG__ENABLE_XP_CAP=false
    ```

### Snippets

Configure snippet access:

    ```env
    # Limit snippets to specific roles
    SNIPPETS__LIMIT_TO_ROLE_IDS=false

    # Snippet access role IDs (JSON array)
    SNIPPETS__ACCESS_ROLE_IDS=[123456789012345678]
    ```

### Temporary Voice Channels

Set up temporary voice channels:

    ```env
    # Temporary VC channel ID
    TEMPVC__TEMPVC_CHANNEL_ID=123456789012345678

    # Temporary VC category ID
    TEMPVC__TEMPVC_CATEGORY_ID=123456789012345678
    ```

### GIF Limiter

Configure GIF rate limiting:

    ```env
    # Recent GIF age limit (seconds)
    GIF_LIMITER__RECENT_GIF_AGE=60

    # Excluded channels from GIF limits (JSON array)
    GIF_LIMITER__GIF_LIMIT_EXCLUDE=[123456789012345678]
    ```

## External Services

### Sentry (Error Tracking)

Enable error tracking with Sentry:

    ```env
    EXTERNAL_SERVICES__SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
    ```

### GitHub Integration

Configure GitHub integration:

    ```env
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
    ```

### InfluxDB (Metrics)

Configure metrics collection with InfluxDB:

    ```env
    EXTERNAL_SERVICES__INFLUXDB_URL=http://localhost:8086
    EXTERNAL_SERVICES__INFLUXDB_TOKEN=your_token
    EXTERNAL_SERVICES__INFLUXDB_ORG=your_org
    ```

### Other Services

Configure additional external services:

    ```env
    # Mailcow API
    EXTERNAL_SERVICES__MAILCOW_API_KEY=your_api_key
    EXTERNAL_SERVICES__MAILCOW_API_URL=https://mail.example.com/api/v1

    # Wolfram Alpha
    EXTERNAL_SERVICES__WOLFRAM_APP_ID=your_app_id
    ```

## Advanced Configuration

### System Administration

Configure system administration features:

    ```env
    # Allow sysadmins to use eval command
    ALLOW_SYSADMINS_EVAL=false
    ```

### Status Roles

Configure status-based role assignments:

    ```env
    # Status to role mappings (JSON array)
    STATUS_ROLES__MAPPINGS=[{"status": "online", "role_id": 123456789012345678}]
    ```

### IRC Bridge

Configure IRC bridge webhooks:

    ```env
    # IRC bridge webhook IDs (JSON array)
    IRC_CONFIG__BRIDGE_WEBHOOK_IDS=[123456789012345678,987654321098765432]
    ```

## Docker Configuration

When using Docker Compose, set environment variables in your `.env` file. Docker Compose automatically loads variables from `.env`:

    ```env
    # .env file for Docker
    BOT_TOKEN=your_bot_token_here
    POSTGRES_HOST=tux-postgres
    POSTGRES_DB=tuxdb
    POSTGRES_USER=tuxuser
    POSTGRES_PASSWORD=your_secure_password
    LOG_LEVEL=INFO
    ```

The `compose.yaml` file references these variables using `${VARIABLE_NAME}` syntax. See [Docker Installation](../install/docker.md) for complete Docker setup instructions.

## Validation

### Check Configuration

Validate your configuration:

    ```bash
    # Validate environment variables
    uv run config validate

    # Test database connection
    uv run db health
    ```

### Environment Testing

Test your configuration:

    ```bash
    # Start Tux with debug mode (automatically loads .env file)
    uv run tux start --debug
    ```

!!! note "Automatic .env Loading"
    Tux automatically loads the `.env` file when it starts. You don't need to manually source it.

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

**Configuration not loading:**

- Verify configuration file paths (`config/config.toml`, not just `config.toml`)
- Check file permissions and encoding (must be UTF-8)
- Run `uv run config validate` to see which files are loaded

## Next Steps

After you configure environment variables:

- [Database Configuration](database.md) - Database setup
- [First Run Setup](../install/first-run.md) - Initial configuration
- [System Operations](../manage/operations.md) - Monitoring and maintenance

For a complete list of all environment variables, see the **[ENV Reference](../../reference/env.md)**.
