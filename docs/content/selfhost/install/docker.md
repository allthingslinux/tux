---
title: Docker Installation
tags:
  - selfhost
  - installation
  - docker
---

# Docker Installation

!!! tip "Tip"
    You can use Podman instead of Docker.

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Deploy Tux using Docker Compose for easy setup and management. Docker Compose handles PostgreSQL, Tux, and optional Adminer (database management UI).

## Prerequisites

Before deploying with Docker, ensure you have:

- **Docker Engine** 20.10+ installed
- **Docker Compose** 2.0+ installed (or `docker compose` plugin)
- **Git** installed
- **Discord bot token** from [Discord Developer Portal](https://discord.com/developers/applications)

### Install Docker Engine

Follow the official Docker installation guide for your OS: [Install Docker Engine](https://docs.docker.com/engine/install/).

### Install uv

Tux uses `uv` as its package manager. Install it using the standalone installer:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

!!! tip "Add to PATH"
    Follow the corresponding command for your shell that the command outputs to add `uv` to your PATH.

!!! tip "Alternative Installation Methods"
    If you prefer, you can install uv via `pipx` (`pipx install uv`) or download binaries directly from [GitHub Releases](https://github.com/astral-sh/uv/releases).

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/allthingslinux/tux.git /opt
cd /opt/tux
```

### 2. Configure Environment

```bash
# Generate configuration files
uv run config generate

# Copy and edit .env file
cp .env.example .env
nano .env
```

**Required environment variables:**

```env
# Discord Bot Token (required)
BOT_TOKEN=your_bot_token_here

# Database Configuration (optional - defaults provided)
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432

# Optional: Bot Configuration
USER_IDS__BOT_OWNER_ID=123456789012345678
BOT_INFO__PREFIX=$

# Optional: Logging
LOG_LEVEL=INFO
DEBUG=false
```

!!! warning "Change Default Password"
    The default PostgreSQL password is insecure. Always set a strong `POSTGRES_PASSWORD` in your `.env` file.

### 3. Start Services

```bash
# Start all services in background
docker compose up -d

# Or build and start
docker compose up -d --build
```

The Docker Compose setup includes:

- **tux-postgres** - PostgreSQL database
- **tux** - Tux Discord bot
- **tux-adminer** (optional) - Database management UI at `http://localhost:8080`

## Services Overview

### Tux Bot Service

The main Tux container runs with:

- Automatic database migrations on startup
- Health checks to ensure bot is running
- Volume mounts for configuration, plugins, and assets
- Read-only root filesystem for security
- Automatic restart on failure

### PostgreSQL Service

PostgreSQL container provides:

- Persistent data storage in Docker volume
- Health checks for startup coordination
- Configurable database name, user, and password
- Port mapping for external access (optional)

### Adminer Service (Optional)

Adminer provides a web-based database management interface:

- Accessible at `http://localhost:8080` (default)
- Pre-configured to connect to PostgreSQL
- Auto-login enabled by default
- Useful for database inspection and management

To disable Adminer, comment out the `tux-adminer` service in `compose.yaml` or set `ADMINER_PORT` to empty.

## Configuration

### Environment Variables

Docker Compose reads from `.env` file. Key variables:

```env
# Required
BOT_TOKEN=your_bot_token_here

# Database (optional - uses defaults if not set)
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432

# Bot Configuration
USER_IDS__BOT_OWNER_ID=123456789012345678
BOT_INFO__PREFIX=$

# Logging
LOG_LEVEL=INFO
DEBUG=false

# Optional: External Services
EXTERNAL_SERVICES__SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

!!! note "Docker-Specific Configuration"
    The `compose.yaml` automatically sets `POSTGRES_HOST=tux-postgres` for the Tux container, so you don't need to configure this in `.env`.

### Volume Mounts

The Docker setup mounts several directories:

- `./config` → `/app/config` (read-only) - Configuration files
- `./src/tux/plugins` → `/app/tux/plugins` (read-only) - Custom plugins
- `./assets` → `/app/assets` (read-only) - Bot assets

**Note:** Migration files are **not mounted by default** - they come from the Docker image. For development or customization, see [Docker Migration Setup](../../developer/concepts/database/migrations.md#-docker-migration-setup).

Persistent volumes:

- `tux_postgres_data` - PostgreSQL data
- `tux_cache` - Application cache
- `tux_temp` - Temporary files
- `tux_user_home` - User home directory

## Service Management

### View Logs

```bash
# Follow all logs
docker compose logs -f

# Follow Tux logs only
docker compose logs -f tux

# Last 100 lines
docker compose logs --tail=100 tux

# Since timestamp
docker compose logs --since "1 hour ago" tux
```

### Start Services

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d tux
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop services (keep volumes)
docker compose stop

# Stop and remove volumes (⚠️ deletes database)
docker compose down -v
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart tux
```

### Check Status

```bash
# View running containers
docker compose ps

# View detailed status
docker compose ps -a

# Check service health
docker compose ps --format json | jq '.[] | {name: .Name, status: .State, health: .Health}'
```

## Updates

### Update Tux

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build

# Or rebuild without stopping
docker compose up -d --build --no-deps tux
```

### Update Dependencies

If `pyproject.toml` or `uv.lock` changes:

```bash
# Rebuild container with new dependencies
docker compose build --no-cache tux
docker compose up -d tux
```

### Database Migrations

Migrations run automatically on container startup. Migrations come from the Docker image by default - no source code required.

**For development or customization:**

If you're developing or have custom migrations, enable the migration mount:

```bash
# Copy override example
cp compose.override.yaml.example compose.override.yaml

# Restart services
docker compose restart tux
```

See [Docker Migration Setup](../../developer/concepts/database/migrations.md#-docker-migration-setup) for details.

## Development Mode

Docker Compose supports development mode with hot reload:

```bash
# Start with watch mode (hot reload)
docker compose watch

# Watch specific service
docker compose watch tux
```

Watch mode automatically:

- Syncs Python source code changes
- Syncs configuration changes
- Syncs plugin changes
- Rebuilds on dependency changes
- Restarts on environment changes

## Adminer (Database Management)

Access Adminer at `http://localhost:8080`:

- **System**: PostgreSQL
- **Server**: `tux-postgres`
- **Username**: Value from `POSTGRES_USER` (default: `tuxuser`)
- **Password**: Value from `POSTGRES_PASSWORD`
- **Database**: Value from `POSTGRES_DB` (default: `tuxdb`)

To change Adminer port:

```env
ADMINER_PORT=9000
```

To disable Adminer, comment out the service in `compose.yaml` or remove it.

## Troubleshooting

### Bot Not Starting

**Check logs:**

```bash
docker compose logs tux
```

**Common causes:**

- Invalid `BOT_TOKEN` - Verify token is correct
- Database not ready - Wait for PostgreSQL health check
- Missing environment variables - Check `.env` file

**Verify configuration:**

```bash
# Check environment variables are loaded
docker compose exec tux env | grep BOT_TOKEN

# Test database connection
docker compose exec tux uv run db health
```

### Database Connection Errors

**Check PostgreSQL is running:**

```bash
docker compose ps tux-postgres
```

**Verify connection:**

```bash
# Test PostgreSQL connection
docker compose exec tux-postgres pg_isready -U tuxuser

# Check database exists
docker compose exec tux-postgres psql -U tuxuser -d tuxdb -c "SELECT version();"
```

**Check environment variables:**

```bash
# Verify database credentials
docker compose exec tux env | grep POSTGRES
```

### Container Keeps Restarting

**Check restart reason:**

```bash
docker compose ps
docker compose logs tux --tail=50
```

**Common issues:**

- Health check failing - Check bot token is set
- Database connection timeout - Verify PostgreSQL is healthy
- Configuration errors - Check `.env` file syntax

### Permission Errors

**Fix volume permissions:**

```bash
# Ensure files are readable
chmod -R 755 config assets src/tux/plugins
chmod 644 .env
```

**Check container user:**

```bash
docker compose exec tux whoami
# Should show: nonroot
```

### Health Check Failures

**Manual health check:**

```bash
docker compose exec tux python -c "from tux.shared.config import CONFIG; print('Token set:', bool(CONFIG.BOT_TOKEN))"
```

**Check health status:**

```bash
docker inspect tux --format='{{json .State.Health}}' | jq
```

### View Container Resources

```bash
# Resource usage
docker stats tux tux-postgres

# Container details
docker compose exec tux ps aux
docker compose exec tux df -h
```

## Advanced Configuration

### Custom Image

Use a custom Tux image:

```env
TUX_IMAGE=ghcr.io/allthingslinux/tux
TUX_IMAGE_TAG=v0.1.0
```

### Development Overrides

```env
# Enable debug mode
DEBUG=true
LOG_LEVEL=DEBUG

# Use local migrations
USE_LOCAL_MIGRATIONS=true

# Force migrations
FORCE_MIGRATE=true
```

### Startup Configuration

```env
# Maximum startup attempts
MAX_STARTUP_ATTEMPTS=5

# Delay between attempts (seconds)
STARTUP_DELAY=10
```

### Database Port Mapping

Expose PostgreSQL port to host:

```env
POSTGRES_PORT=5432
```

Access from host: `postgresql://tuxuser:password@localhost:5432/tuxdb`

### Disable Adminer

Comment out or remove the `tux-adminer` service in `compose.yaml`, or set:

```env
ADMINER_PORT=
```

## Backup and Restore

### Backup Database

```bash
# Create backup
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup_$(date +%Y%m%d).sql

# Or using Adminer
# Navigate to http://localhost:8080 → Export → SQL
```

### Restore Database

```bash
# Restore from backup
docker compose exec -T tux-postgres psql -U tuxuser -d tuxdb < backup_20240101.sql
```

### Backup Volumes

```bash
# List volumes
docker volume ls | grep tux

# Backup volume
docker run --rm -v tux_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Related Documentation

- **[Environment Configuration](../config/environment.md)** - Complete environment variable reference
- **[Database Setup](../config/database.md)** - Database configuration details
- **[First Run](first-run.md)** - Initial setup verification
- **[System Operations](../manage/operations.md)** - Monitoring and maintenance

---

**Next Steps:** After deploying with Docker, verify your installation with the [First Run Guide](first-run.md).
