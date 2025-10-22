# Docker Compose Deployment

Deploy Tux using Docker Compose - the recommended method for most users.

## Overview

Docker Compose deployment includes:

- **Tux Bot** - Main Discord bot container
- **PostgreSQL** - Database (postgres:17-alpine)
- **Adminer** - Web-based database management UI

All services are pre-configured and ready to use.

## Prerequisites

### Required

- **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** - Usually included with Docker Desktop
- **Git** - For cloning repository
- **Discord Bot Token** - [How to get one](../setup/discord-bot-token.md)

### Verify Installation

```bash
docker --version                    # Should show Docker 20.10+
docker compose version              # Should show Compose 2.0+
git --version                       # Should show Git 2.0+
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/allthingslinux/tux.git
cd tux
```

### 2. Configure Environment

```bash
# Generate example config
uv run config generate

# Or manually copy
cp config/config.toml.example config/config.toml
```

Create `.env` file (it's git-ignored):

```bash
cat > .env << 'EOF'
# Discord Configuration
BOT_TOKEN=your_discord_bot_token_here

# Database Configuration (defaults are fine for Docker)
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=ChangeThisToAStrongPassword123!

# Environment
ENVIRONMENT=production
DEBUG=false

# Optional: Sentry
# SENTRY_DSN=https://your-sentry-dsn

# Optional: InfluxDB
# EXTERNAL_SERVICES__INFLUXDB_URL=http://influxdb:8086
# EXTERNAL_SERVICES__INFLUXDB_TOKEN=your_token
# EXTERNAL_SERVICES__INFLUXDB_ORG=your_org
EOF
```

Edit the `.env` file with your actual bot token.

### 3. Start Services

```bash
# Start all services in detached mode
docker compose up -d

# View logs
docker compose logs -f tux
```

### 4. Verify Running

```bash
# Check service status
docker compose ps

# Should show:
# tux           running
# tux-postgres  running (healthy)
# tux-adminer   running
```

### 5. Invite Bot

Invite Tux to your Discord server using your bot's OAuth2 URL.

### 6. Run Setup Wizard

In your Discord server:

```text
/config wizard
```

Done! Tux is now running.

## Services

### Tux Bot

Main Discord bot service:

- **Container:** `tux`
- **Image:** `ghcr.io/allthingslinux/tux:latest` (or builds locally)
- **Ports:** None (Discord connection only)
- **Volumes:**
  - `config/` - Configuration files (read-only)
  - `assets/` - Images and assets (read-only)
  - `src/tux/plugins/` - Custom plugins (read-only)
  - `src/tux/database/migrations/` - Database migrations
  - `tux_cache` - Cache data
  - `tux_temp` - Temporary files
  - `tux_user_home` - User home directory

**Health Check:** Runs every 30s, checks config and bot token

**Restart Policy:** `unless-stopped` (always restart except manual stop)

### PostgreSQL

Database service:

- **Container:** `tux-postgres`
- **Image:** `postgres:17-alpine`
- **Port:** `5432` (exposed to host)
- **Volume:** `tux_postgres_data` (persistent storage)
- **Configuration:** Custom `postgresql.conf` for optimization

**Health Check:** `pg_isready` every 10s

**Restart Policy:** `no` (manual restart only)

### Adminer

Web-based database administration:

- **Container:** `tux-adminer`
- **Image:** `adminer:latest`
- **Port:** `8080` (default, configurable via `ADMINER_PORT`)
- **URL:** `http://localhost:8080`
- **Theme:** Dracula

**Auto-login:** Enabled by default (development only!)

## Docker Compose Commands

### Starting Services

```bash
# Start all services
docker compose up -d

# Start and view logs
docker compose up

# Start specific service
docker compose up -d tux
```

### Stopping Services

```bash
# Stop all services
docker compose down

# Stop but keep data
docker compose stop

# Stop and remove volumes (WARNING: deletes data!)
docker compose down -v
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f tux
docker compose logs -f tux-postgres

# Last N lines
docker compose logs --tail=100 tux

# Since timestamp
docker compose logs --since 2024-01-01T00:00:00 tux
```

### Updating

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build

# Run new migrations
docker compose exec tux uv run db push
```

### Database Operations

```bash
# Run migrations
docker compose exec tux uv run db push

# Check database health
docker compose exec tux uv run db health

# List tables
docker compose exec tux uv run db tables

# Access psql
docker compose exec tux-postgres psql -U tuxuser -d tuxdb
```

### Debugging

```bash
# Execute command in container
docker compose exec tux uv run tux version

# Open shell in container
docker compose exec tux /bin/bash

# View container details
docker compose ps
docker inspect tux
```

## Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Required
BOT_TOKEN=your_token

# Database (defaults work for Docker)
POSTGRES_HOST=tux-postgres          # Container name
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=strong_password

# Optional
DEBUG=false                         # Enable debug logging
ENVIRONMENT=production              # Environment name
USE_LOCAL_MIGRATIONS=true           # Use local migration files
FORCE_MIGRATE=false                 # Force migration on startup
```

### Custom Configuration

Place config files in `config/`:

- `config/config.toml` - TOML configuration
- `config/config.yaml` - YAML configuration
- `config/config.json` - JSON configuration

These are mounted read-only into the container.

### Volumes Explained

**Configuration Volumes (Read-Only):**

- `./config:/app/config:ro` - Your config files
- `./assets:/app/assets:ro` - Bot assets (images, etc.)
- `./src/tux/plugins:/app/tux/plugins:ro` - Custom plugins

**Data Volumes (Persistent):**

- `tux_postgres_data` - PostgreSQL data
- `tux_cache` - Bot cache
- `tux_temp` - Temporary files
- `tux_user_home` - Container user home

## Development Mode

Docker Compose includes development features:

### File Watching

```bash
# Start with file watching (hot-reload)
docker compose watch

# Code changes sync automatically
# Bot reloads on change (if hot-reload enabled in code)
```

**What's watched:**

- `./src` - Source code (syncs)
- `./config` - Config files (syncs)
- `./assets` - Assets (syncs)
- `pyproject.toml` - Rebuild on change
- `.env` - Restart on change

### Development vs Production

**Development:**

```bash
# Use watch mode
docker compose watch

# Or with debug logging
DEBUG=true docker compose up
```

**Production:**

```bash
# Standard detached mode
docker compose up -d

# Use prebuilt image
TUX_IMAGE=ghcr.io/allthingslinux/tux TUX_IMAGE_TAG=v1.0.0 docker compose up -d
```

## Adminer Web UI

Access database via web interface:

### Accessing Adminer

1. **Open browser:** `http://localhost:8080`
2. **Auto-login enabled** (development)
3. **Or manual login:**
   - System: PostgreSQL
   - Server: tux-postgres
   - Username: tuxuser
   - Password: (from your .env)
   - Database: tuxdb

### Features

- Browse tables
- Run SQL queries
- Export/import data
- View table structure
- Edit data directly

### Security Warning

!!! danger "Disable Auto-Login in Production"
    The default configuration has auto-login enabled for development convenience.
    For production, set `ADMINER_AUTO_LOGIN=false` in `.env`.

### Customization

Change Adminer port:

```bash
# In .env
ADMINER_PORT=9090
```

Then access at `http://localhost:9090`

## Production Deployment

### Security Hardening

1. **Change Default Password:**

   ```bash
   POSTGRES_PASSWORD="$(openssl rand -base64 32)"
   ```

2. **Disable Adminer Auto-Login:**

   ```bash
   ADMINER_AUTO_LOGIN=false
   ```

3. **Don't Expose Ports:**

   ```yaml
   # In compose.yaml, comment out port mappings:
   # ports: ['${POSTGRES_PORT:-5432}:5432']
   ```

4. **Use Secrets:**

   ```bash
   chmod 600 .env
   ```

### Resource Limits

Add resource limits to `compose.yaml`:

```yaml
services:
  tux:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Logging

Configure log rotation:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
    compress: "true"
```

Already configured in the default `compose.yaml`.

## Backups

### Database Backup

```bash
# Create backup
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup_$(date +%Y%m%d).sql

# With compression
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb | gzip > backup_$(date +%Y%m%d).sql.gz

# Automated daily backup script
cat > backup.sh << 'EOF'
#!/bin/bash
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb | gzip > backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
find backups/ -name "backup_*.sql.gz" -mtime +30 -delete
EOF
chmod +x backup.sh
```

### Restore Backup

```bash
# From SQL file
docker compose exec -T tux-postgres psql -U tuxuser tuxdb < backup.sql

# From gzip
gunzip < backup.sql.gz | docker compose exec -T tux-postgres psql -U tuxuser tuxdb
```

**[Full Backup Guide →](../database/backups.md)**

## Monitoring

### Health Checks

```bash
# Check container health
docker compose ps

# View health status
docker inspect tux --format='{{.State.Health.Status}}'

# Check logs for errors
docker compose logs --tail=100 tux | grep ERROR
```

### Resource Usage

```bash
# View resource usage
docker stats

# Specific container
docker stats tux
```

## Troubleshooting

### Services Won't Start

```bash
# Check for errors
docker compose logs

# Validate compose.yaml
docker compose config

# Check Docker daemon
systemctl status docker             # Linux
```

### Database Connection Failed

```bash
# Check postgres is healthy
docker compose ps tux-postgres

# Check logs
docker compose logs tux-postgres

# Verify environment variables
docker compose exec tux env | grep POSTGRES
```

### Permission Errors

```bash
# Check file permissions
ls -la .env config/

# Fix if needed
chmod 600 .env
chmod -R 644 config/
```

### Port Conflicts

```bash
# Check what's using port
sudo lsof -i :5432                  # PostgreSQL
sudo lsof -i :8080                  # Adminer

# Change ports in .env
POSTGRES_PORT=5433
ADMINER_PORT=8081
```

## Advanced Topics

### Custom Image

Build from specific tag:

```bash
git checkout v1.0.0
docker compose build
docker compose up -d
```

### Network Configuration

Containers communicate via Docker network:

- Network name: `tux_default`
- Internal DNS: Container names resolve
- Isolation: Not accessible from host except exposed ports

### Volumes Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect tux_postgres_data

# Backup volume
docker run --rm -v tux_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm -v tux_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## Migration from Other Deployments

### From VPS to Docker

1. Backup current database
2. Clone repository
3. Set up `.env` with same settings
4. Start Docker Compose
5. Restore database backup
6. Stop old deployment

### From One Server to Another

1. Backup database and config
2. Set up new server with Docker Compose
3. Copy `.env` and `config/`
4. Restore database
5. Start services

## Performance Tuning

### PostgreSQL Configuration

Custom `postgresql.conf` included at `docker/postgres/postgresql.conf`.

Key settings:

- `shared_buffers` - Memory for caching
- `work_mem` - Memory per operation
- `max_connections` - Connection limit

### Bot Performance

Environment variables:

```bash
# In .env
POSTGRES_MAX_CONNECTIONS=20         # Connection pool size
```

## Security

### Production Checklist

- [ ] Change default database password
- [ ] Disable Adminer auto-login
- [ ] Don't expose PostgreSQL port publicly
- [ ] Use strong `.env` permissions (600)
- [ ] Enable firewall (UFW or similar)
- [ ] Set up log monitoring
- [ ] Configure backup automation
- [ ] Use HTTPS for Adminer (reverse proxy)

### Firewall

```bash
# Allow only necessary ports
sudo ufw allow 8080/tcp comment 'Adminer (dev only)'
# Don't allow 5432 publicly!
```

## Useful Commands Reference

```bash
# Lifecycle
docker compose up -d                # Start
docker compose down                 # Stop
docker compose restart              # Restart
docker compose stop tux             # Stop specific service

# Logs
docker compose logs -f              # Follow all logs
docker compose logs -f tux          # Follow bot logs
docker compose logs --tail=100 tux  # Last 100 lines

# Updates
git pull                            # Get latest code
docker compose pull                 # Pull latest images
docker compose up -d --build        # Rebuild and restart

# Database
docker compose exec tux uv run db push      # Migrations
docker compose exec tux uv run db health    # Health check
docker compose exec tux-postgres psql -U tuxuser tuxdb  # psql shell

# Debugging
docker compose exec tux /bin/bash   # Shell in container
docker compose ps                   # Service status
docker stats                        # Resource usage
```

## Next Steps

After deployment:

1. **[Configure Bot](../configuration/index.md)** - Set up features and settings
2. **[Run Migrations](../database/migrations.md)** - Ensure database is up to date
3. **[Set Up Monitoring](../operations/monitoring.md)** - Watch for issues
4. **[Configure Backups](../database/backups.md)** - Protect your data

## Getting Help

- **[Troubleshooting](../operations/troubleshooting.md)** - Common issues
- **[Discord Support](https://discord.gg/gpmSjcjQxg)** - Ask #self-hosting
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs

---

**Next:** [Configure Your Instance](../configuration/index.md) or try [VPS Deployment](systemd-vps.md).
