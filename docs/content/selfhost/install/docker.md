---
title: Docker Installation
tags:
  - selfhost
  - installation
  - docker
icon: lucide/container
---

# Docker Installation

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

!!! tip "Tip"
    You can use Podman instead of Docker.

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
git clone https://github.com/allthingslinux/tux.git /opt/tux
cd /opt/tux
```

### 2. Configure Environment

```bash
# Copy example configuration file and edit it
cp config/config.json.example config/config.json
nano config/config.json

# Copy example .env file and edit it
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

# Optional: Logging
LOG_LEVEL=INFO
DEBUG=false
```

!!! warning "Change Default Password"
    The default PostgreSQL password is insecure. Always set a strong `POSTGRES_PASSWORD` in your `.env` file.

### 3. Start Services

**Development (build from source, hot reload):**

```bash
docker compose --profile dev up -d

# With hot reload
docker compose --profile dev up --watch

# Using COMPOSE_PROFILES (https://docs.docker.com/compose/how-tos/profiles/)
COMPOSE_PROFILES=dev docker compose up -d

# With Adminer (DB UI)
docker compose --profile dev --profile adminer up -d
```

**Production (pre-built image, security hardening):**

```bash
docker compose --profile production up -d

# Or
COMPOSE_PROFILES=production docker compose up -d
```

Set `RESTART_POLICY=unless-stopped` in `.env` for production. To add Adminer: `--profile adminer`.

Profiles work as in [Docker Compose](https://docs.docker.com/compose/how-tos/profiles/): `tux-postgres` has no profile (always started); `tux` and `tux-dev` are behind `production` and `dev` so you must enable one. `adminer` is optional.

The Docker Compose setup includes:

- **tux-postgres** - PostgreSQL database (no profile; always started with Tux)
- **tux** (production) or **tux-dev** (development) - Tux Discord bot; use `--profile production` or `--profile dev`
- **tux-valkey** (optional) - Valkey cache for shared cache across restarts; use `--profile valkey`
- **tux-adminer** (optional) - Database management UI at `http://localhost:8080`; use `--profile adminer`

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

Adminer provides a web-based database management interface. Enable it with the `adminer` profile:

```bash
docker compose --profile dev --profile adminer up -d
# or
docker compose --profile production --profile adminer up -d
```

- Accessible at `http://localhost:8080` (default)
- Pre-configured to connect to PostgreSQL
- Auto-login enabled by default
- Useful for database inspection and management

Omit `--profile adminer` to run without Adminer.

### Valkey (optional cache)

Valkey provides a shared cache (guild config, jail status, prefix, permissions) that
persists across bot restarts. Without it, Tux uses in-memory cache (no extra container).

To use Valkey with Docker:

1. Start Valkey with the `valkey` profile:

   ```bash
   docker compose --profile dev --profile valkey up -d
   # or
   docker compose --profile production --profile valkey up -d
   ```

2. Set the Valkey host in `.env` so Tux can connect:

   ```env
   VALKEY_HOST=tux-valkey
   VALKEY_PORT=6379
   ```

Omit `--profile valkey` and leave `VALKEY_HOST` empty to run without Valkey.

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

# Bot owner, sysadmins, prefix: set in config/config.json; see [Configuration](../config/index.md)

# Logging
LOG_LEVEL=INFO
DEBUG=false

# Optional: Valkey (use with --profile valkey)
VALKEY_HOST=tux-valkey
VALKEY_PORT=6379

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
# Start all services (use --profile dev or --profile production)
docker compose --profile dev up -d

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

# Rebuild and restart (use --profile dev or --profile production)
docker compose down
docker compose --profile dev up -d --build

# Or rebuild without stopping
docker compose --profile dev up -d --build --no-deps tux
```

### Update Dependencies

If `pyproject.toml` or `uv.lock` changes:

```bash
# Rebuild container with new dependencies (use --profile dev or --profile production)
docker compose --profile dev build --no-cache tux
docker compose --profile dev up -d tux
```

### Database Migrations

Migrations run automatically on container startup. Migrations come from the Docker image by default - no source code required.

**For development or customization:**

If you're developing or have custom migrations, enable the migration mount:

Create `compose.override.yaml`:

```yaml
services:
  tux:
    volumes:
      # Mount migrations for faster development/customization iteration
      # Without this, migrations come from the Docker image (production behavior)
      - ./src/tux/database/migrations:/app/src/tux/database/migrations:ro
```

```bash
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
