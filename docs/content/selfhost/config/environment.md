# Environment Variables

Configure Tux using environment variables for different deployment scenarios.

## Core Configuration

### Discord Bot Settings

```env
# Required: Discord bot token
DISCORD_TOKEN=your_bot_token_here

# Bot prefix for commands (default: !)
BOT_PREFIX=!

# Owner user ID for admin commands
BOT_OWNER_ID=123456789012345678
```

### Database Configuration

```env
# PostgreSQL (recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/tux

# SQLite (development only)
DATABASE_URL=sqlite:///tux.db

# Redis (for caching, optional)
REDIS_URL=redis://localhost:6379/0
```

## Feature Configuration

### Logging

```env
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Log file path
LOG_FILE=/var/log/tux/tux.log

# Enable Sentry error reporting
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### Performance

```env
# Maximum concurrent tasks
MAX_CONCURRENT_TASKS=100

# Command cooldown (seconds)
COMMAND_COOLDOWN=1

# Enable debug mode
DEBUG=false
```

## Security Configuration

### API Keys

```env
# External API keys (if needed)
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
```

### Rate Limiting

```env
# Rate limit per user (commands per minute)
RATE_LIMIT_PER_USER=60

# Rate limit per guild (commands per minute)
RATE_LIMIT_PER_GUILD=1000
```

## Development Settings

### Development Mode

```env
# Enable development features
DEV_MODE=true

# Hot reload enabled
HOT_RELOAD=true

# Debug logging
DEBUG_LOGGING=true
```

### Testing

```env
# Test database URL
TEST_DATABASE_URL=sqlite:///test.db

# Test mode
TEST_MODE=false
```

## Production Settings

### Monitoring

```env
# Enable metrics collection
METRICS_ENABLED=true

# Metrics port
METRICS_PORT=9090

# Health check endpoint
HEALTH_CHECK_PORT=8080
```

### Backup

```env
# Backup configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
```

## Docker Configuration

### Docker Compose

```yaml
version: '3.8'
services:
  tux:
    image: tux:latest
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - DATABASE_URL=postgresql://postgres:password@db:5432/tux
      - LOG_LEVEL=INFO
    depends_on:
      - db
      - redis
```

### Docker Environment File

```env
# .env file for Docker
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://postgres:password@db:5432/tux
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
```

## Systemd Configuration

### Environment File

Create `/etc/tux/environment`:

```env
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://tux:password@localhost:5432/tux
LOG_FILE=/var/log/tux/tux.log
LOG_LEVEL=INFO
```

### Systemd Service

```ini
[Unit]
Description=Tux Discord Bot
After=network.target

[Service]
Type=simple
User=tux
WorkingDirectory=/opt/tux
EnvironmentFile=/etc/tux/environment
ExecStart=/opt/tux/venv/bin/tux run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Validation

### Check Configuration

```bash
# Validate environment variables
tux config validate

# Test database connection
tux db test

# Check bot token
tux bot test
```

### Environment Testing

```bash
# Load environment and test
source .env
tux run --dry-run
```

## Troubleshooting

### Common Issues

**Missing required variables**:

- Check all required variables are set
- Verify variable names are correct
- Check for typos

**Database connection errors**:

- Verify DATABASE_URL format
- Check database server is running
- Test network connectivity

**Permission errors**:

- Check file permissions on config files
- Verify user has access to directories
- Check systemd service permissions

## Next Steps

After configuring environment variables:

- [Database Configuration](database.md) - Database setup
- [First Run Setup](../install/first-run.md) - Initial configuration
- [Monitoring Setup](../ops/monitoring.md) - Production monitoring
