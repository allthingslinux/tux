# Getting Started - For Self-Hosters

This guide will help you deploy and run your own Tux instance.

## Prerequisites

Before you begin, ensure you have:

- **Discord Bot Application** - [Create one](../admin-guide/setup/discord-bot-token.md)
- **PostgreSQL Database** - Local or hosted (Supabase, Railway, etc.)
- **Python 3.13+** OR **Docker** - For running Tux
- **Git** - For cloning the repository

## Quick Start (Recommended: Docker)

The fastest way to get Tux running is with Docker Compose:

###

 1. Clone the Repository

```bash
git clone https://github.com/allthingslinux/tux.git
cd tux
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

Required settings:

```bash
# Discord Configuration
BOT_TOKEN=your_discord_bot_token

# Database (using Docker's postgres service)
POSTGRES_HOST=tux-postgres
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=ChangeThisToAStrongPassword123!
```

### 3. Start Services

```bash
# Start Tux and PostgreSQL
docker compose up -d

# View logs
docker compose logs -f tux
```

That's it! Tux should now be running.

## What's Running?

The Docker Compose setup includes:

- **Tux Bot** - The main Discord bot
- **PostgreSQL** - Database for storing data
- **Adminer** - Web UI for database management (port 8080)

Access Adminer at `http://localhost:8080` to inspect your database.

## Next Steps

### 1. Verify Tux is Running

Check the logs:

```bash
docker compose logs -f tux
```

You should see startup messages and "Bot is ready!"

### 2. Invite Tux to Your Server

Use the OAuth2 URL Generator in the Discord Developer Portal:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to OAuth2 → URL Generator
4. Select scopes: `bot`, `applications.commands`
5. Select permissions (see [Discord Bot Setup](../admin-guide/setup/discord-bot-token.md))
6. Copy and visit the generated URL

### 3. Run Setup Wizard

In your Discord server, run:

```
/config wizard
```

This will guide you through initial configuration.

### 4. Configure Your Instance

Learn about configuration options:

- **[Environment Variables](../admin-guide/setup/environment-variables.md)** - Core settings
- **[Config Files](../admin-guide/setup/config-files.md)** - TOML/YAML/JSON configuration
- **[Guild Setup](../admin-guide/configuration/guild-setup.md)** - Per-server configuration
- **[Features](../admin-guide/configuration/features.md)** - Enable/disable features

## Alternative Deployment Methods

### Local Development

For development or testing without Docker:

```bash
# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
nano .env

# Run database migrations
uv run db push

# Start Tux
uv run tux start
```

**[Full development setup →](../developer-guide/getting-started/development-setup.md)**

### VPS Deployment

Deploy on a VPS with systemd:

**[VPS Deployment Guide →](../admin-guide/deployment/systemd-vps.md)**

### Cloud Platforms

Deploy on Railway, DigitalOcean, or other platforms:

**[Cloud Deployment Guide →](../admin-guide/deployment/cloud-platforms.md)**

## Essential Admin Tasks

### Managing the Database

```bash
# Run migrations
docker compose exec tux uv run db push

# Check database health
docker compose exec tux uv run db health

# List tables
docker compose exec tux uv run db tables
```

**[Database Management →](../admin-guide/database/migrations.md)**

### Viewing Logs

```bash
# Follow all logs
docker compose logs -f

# Tux logs only
docker compose logs -f tux

# Last 100 lines
docker compose logs --tail=100 tux
```

**[Logging Guide →](../admin-guide/operations/logging.md)**

### Updating Tux

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose up -d --build

# Run any new migrations
docker compose exec tux uv run db push
```

**[Update Guide →](../admin-guide/operations/updating.md)**

### Backing Up

```bash
# Backup database
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup_$(date +%Y%m%d).sql

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env config/
```

**[Backup Guide →](../admin-guide/database/backups.md)**

## Common Issues

### Bot Won't Start

1. Check logs: `docker compose logs tux`
2. Verify bot token in `.env`
3. Ensure database is running: `docker compose ps`
4. Check database connection settings

**[Troubleshooting Guide →](../admin-guide/operations/troubleshooting.md)**

### Database Connection Failed

1. Ensure PostgreSQL is running: `docker compose ps tux-postgres`
2. Check `POSTGRES_HOST=tux-postgres` in `.env`
3. Verify credentials match `compose.yaml` settings

### Permission Errors in Discord

1. Re-invite bot with correct permissions
2. Check bot role hierarchy (should be above moderated roles)
3. Verify channel-specific permissions

## Getting Help

### Documentation

- **[Admin Guide](../admin-guide/)** - Complete administration docs
- **[Deployment Guide](../admin-guide/deployment/)** - Detailed deployment options
- **[Configuration Guide](../admin-guide/configuration/)** - All configuration options

### Community Support

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask in #support
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs

## Security Checklist

Before going to production:

- [ ] Change default database password
- [ ] Set up regular backups
- [ ] Configure firewall (if VPS)
- [ ] Enable Sentry for error tracking (optional)
- [ ] Set up log rotation
- [ ] Use secure `.env` file permissions (600)
- [ ] Never commit `.env` to version control

**[Security Best Practices →](../admin-guide/security/best-practices.md)**

## What's Next?

### Essential Reading

- **[Configuration Overview](../admin-guide/configuration/)** - Understand all options
- **[Database Management](../admin-guide/database/)** - Migrations and backups
- **[Operations](../admin-guide/operations/)** - Monitoring and maintenance

### Optional Features

- **[Sentry Integration](../admin-guide/configuration/advanced.md#sentry)** - Error tracking
- **[InfluxDB Metrics](../admin-guide/configuration/advanced.md#influxdb)** - Performance metrics
- **[Plugins](../admin-guide/configuration/advanced.md#plugins)** - Custom functionality

### Advanced Topics

- **[Performance Optimization](../admin-guide/operations/performance.md)** - Tuning for large servers
- **[Scaling](../admin-guide/deployment/docker-compose.md#scaling)** - Handle more load
- **[Monitoring](../admin-guide/operations/monitoring.md)** - Health checks and alerts

Ready to configure? Head to the **[Admin Guide](../admin-guide/)** for detailed documentation!
