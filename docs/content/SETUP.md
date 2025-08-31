# Tux Setup Guide

This guide explains how to set up Tux using the new simplified environment system.

## Quick Start

### For Developers

1. **Clone and setup:**
   ```bash
   git clone https://github.com/allthingslinux/tux.git
   cd tux
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your bot tokens and database URLs
   ```

3. **Start the bot:**
   ```bash
   # Auto-detects environment (defaults to development)
   make start
   
   # Or explicitly set environment
   make dev
   ```

### For Self-Hosters

1. **Clone and setup:**
   ```bash
   git clone https://github.com/allthingslinux/tux.git
   cd tux
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your production bot token and database URL
   ```

3. **Start with Docker:**
   ```bash
   make docker-prod
   ```

## Configuration System

The bot uses a simplified configuration system that works the same everywhere:

### Context Detection

The bot automatically detects its context:

1. **Docker container** - Automatically detected as production
2. **Local development** - When running outside Docker
3. **Testing** - When running tests

### Configuration Sources

Configuration is loaded in this priority order:

1. **Environment variables** (highest priority)
2. **Environment variables** (`.env` file)
3. **Pydantic model defaults** (fallback values)
4. **Hardcoded defaults** (lowest priority)

## Configuration Files

### .env File

The `.env` file contains environment-specific settings:

```bash
# Bot Configuration
BOT_TOKEN=your_bot_token

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/tux
```

### Environment Variables

The configuration is now handled through environment variables and a `.env` file:

```yaml
BOT_INFO:
  PREFIX: "~"
  BOT_NAME: "Tux"

USER_IDS:
  BOT_OWNER: 123456789012345679
  SYSADMINS: [123456789012345679]
```

## Docker Usage

### Development Environment

```bash
# Start development environment
make docker-dev

# With file watching
make docker-dev WATCH=1

# In background
make docker-dev DETACH=1
```

### Production Environment

```bash
# Start production environment
make docker-prod

# In background
make docker-prod DETACH=1
```

### Custom Environment

```bash
# Start the bot
make prod
```

## Database Management

### Automatic Environment Detection

Database operations automatically use the correct database for your environment:

```bash
# Upgrade database (uses current environment)
make db-upgrade

# Create new migration
make db-revision

# Check database status
make db-current
```

### Database Operations

```bash
# Upgrade database
make db-upgrade

# Create new migration
make db-revision
```

### Database Lifecycle & Migrations

For comprehensive information about database management, migrations, and the complete lifecycle, see [Database Lifecycle Guide](docs/database-lifecycle.md) and [Database Optimization Guide](docs/database-optimization.md).

**Key Points:**
- **Automatic migrations**: Bot runs migrations automatically on startup in production
- **New server support**: Bot automatically initializes database when joining new Discord servers
- **Update process**: Database schema updates automatically when you update Tux
- **Safety features**: All migrations run in transactions with automatic rollback on failure

## Common Commands

### Development

```bash
make dev              # Start in development mode
make test             # Run tests
make lint             # Check code quality
make format           # Format code
make type-check       # Check types
```

### Production

```bash
make prod             # Start in production mode
make docker-prod      # Start production Docker environment
```

### Database

```bash
make db-upgrade       # Upgrade database
make db-revision      # Create migration
make db-current       # Show current version
make db-reset         # Reset database (WARNING: destroys data)
```

### Docker

```bash
make docker-dev       # Start development Docker environment
make docker-prod      # Start production Docker environment
make docker-logs      # Show logs
make docker-ps        # List containers
```

## Troubleshooting

### Environment Detection Issues

If the environment isn't being detected correctly:

1. **Check .env file:**
   ```bash
   cat .env
   ```

2. **Start the bot:**
   ```bash
   make start
   ```

3. **Check detection method:**
   ```bash
   python -c "from tux.shared.config.environment import get_environment_info; print(get_environment_info())"
   ```

### Database Issues

If you encounter database problems:

1. **Check database status:**
   ```bash
   make db-current
   make db-health
   ```

2. **Verify migrations:**
   ```bash
   make db-history
   make db-upgrade
   ```

3. **Check bot logs for migration errors:**
   ```bash
   docker compose logs tux
   # or for local: check your terminal output
   ```

4. **Common database scenarios:**
   - **New server join**: Bot automatically initializes database
   - **After updates**: Migrations run automatically on startup
   - **Migration failures**: Check logs and database permissions

For detailed database troubleshooting, see [Database Lifecycle Guide](docs/database-lifecycle.md) and [Database Optimization Guide](docs/database-optimization.md).

### Configuration Issues

If configuration isn't loading:

1. **Check file permissions:**
   ```bash
   ls -la .env*
   ls -la .env
   ```

2. **Validate configuration:**
   ```bash
   python -c "from tux.shared.config import CONFIG; print('Configuration loaded successfully')"
   ```

3. **Check environment variables:**
   ```bash
   env | grep TUX
   env | grep DEV_
   env | grep PROD_
   ```

### Docker Issues

If Docker isn't working:

1. **Check Docker Compose config:**
   ```bash
   docker-compose config
   ```

2. **Validate environment variables:**
   ```bash
   docker-compose config | grep -A 5 -B 5 ENV
   ```

3. **Check container logs:**
   ```bash
   make docker-logs
   ```

## Migration from Old System

If you're upgrading from the old system:

1. **Remove old environment variables:**
   ```bash
   # Remove these from your .env file:
   # MODE=dev
   # MODE=prod
   ```

2. **Update your .env file:**
   ```bash
        # Use these direct variables:
     BOT_TOKEN=your_token
     DATABASE_URL=postgresql://...
   ```

3. **Update your scripts:**
   ```bash
   # Old: MODE=prod make start
   # New: make prod
   
   # Old: MODE=dev make start
   # New: make dev
   ```

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Check the [GitHub issues](https://github.com/allthingslinux/tux/issues)
4. Join our [Discord server](https://discord.gg/linux) for support
