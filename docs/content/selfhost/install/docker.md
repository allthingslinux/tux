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

Deploy Tux using Docker Compose for easy setup and management. Docker Compose handles PostgreSQL, Tux, and optional Adminer (database management UI).

Tux Docker images are optimized for production use with:

- Multi-stage builds for minimal image size (~400MB)
- Non-root user for security
- Read-only root filesystem
- Automatic health checks
- Production-ready configuration

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

**Development (recommended for testing):**

```bash
# Start all services in background
docker compose up -d

# Or build and start
docker compose up -d --build
```

**Production deployment:**

```bash
# Use production compose file (no source code bindings, uses pre-built images)
docker compose -f compose.production.yaml up -d
```

The Docker Compose setup includes:

- **tux-postgres** - PostgreSQL database
- **tux** - Tux Discord bot
- **tux-adminer** (optional) - Database management UI at `http://localhost:8080` (dev mode only)

## Services Overview

### Tux Bot Service

The main Tux container runs with:

- Automatic database migrations on startup
- Health checks to ensure bot is running
- Volume mounts for configuration, plugins, and assets
- Read-only root filesystem for security (production)
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

## Basic Service Management

### View Logs

```bash
# Follow all logs
docker compose logs -f

# Follow Tux logs only
docker compose logs -f tux

# Last 100 lines
docker compose logs --tail=100 tux
```

### Start/Stop Services

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart services
docker compose restart

# Check status
docker compose ps
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

## Related Documentation

- **[Docker Operations](../manage/docker.md)** - Detailed service management, backups, and operations
- **[Production Deployment](../../reference/docker-production.md)** - Production deployment guide
- **[Docker Troubleshooting](../../support/troubleshooting/docker.md)** - Common issues and solutions
- **[Building Docker Images](../../developer/guides/docker-images.md)** - Building and optimizing images
- **[Environment Configuration](../config/environment.md)** - Complete environment variable reference
- **[Database Setup](../config/database.md)** - Database configuration details
- **[First Run](first-run.md)** - Initial setup verification

---

**Next Steps:** After deploying with Docker, verify your installation with the [First Run Guide](first-run.md). For detailed operations, see the [Docker Operations](../manage/docker.md) guide.
