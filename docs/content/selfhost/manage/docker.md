---
title: Docker Operations
tags:
  - selfhost
  - operations
  - docker
---

# Docker Operations

Detailed guide for managing and operating Tux Docker containers.

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

# Filter logs
docker compose logs tux | grep -i "error\|warning"
```

### Start Services

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d tux

# Start with build
docker compose up -d --build
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

# Restart with recreation
docker compose up -d --force-recreate tux
```

### Check Status

```bash
# View running containers
docker compose ps

# View detailed status
docker compose ps -a

# Check service health
docker compose ps --format json | jq '.[] | {name: .Name, status: .State, health: .Health}'

# View resource usage
docker stats tux tux-postgres
```

## Adminer (Database Management)

Adminer provides a web-based database management interface for PostgreSQL.

### Accessing Adminer

Access Adminer at `http://localhost:8080`:

- **System**: PostgreSQL
- **Server**: `tux-postgres`
- **Username**: Value from `POSTGRES_USER` (default: `tuxuser`)
- **Password**: Value from `POSTGRES_PASSWORD`
- **Database**: Value from `POSTGRES_DB` (default: `tuxdb`)

### Configuration

To change Adminer port:

```env
ADMINER_PORT=9000
```

To disable Adminer:

- Development: Comment out the service in `compose.yaml` or set `ADMINER_PORT=` to empty
- Production: Adminer is disabled by default. Enable with `--profile dev` if needed:

```bash
docker compose -f compose.production.yaml --profile dev up -d adminer
```

### Using Adminer

**Common operations:**

1. **Browse tables**: Click on database name → Select table
2. **Run SQL queries**: Click "SQL command" → Enter query → Execute
3. **Export data**: Navigate to table → Click "Export" → Select format (SQL, CSV, etc.)
4. **Import data**: Click "Import" → Select file → Execute

## Backup and Restore

### Backup Database

**Using pg_dump (recommended):**

```bash
# Create backup with timestamp
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup_$(date +%Y%m%d_%H%M%S).sql

# Create backup with custom format (smaller, faster)
docker compose exec tux-postgres pg_dump -U tuxuser -Fc tuxdb > backup_$(date +%Y%m%d).dump

# Compressed backup
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Using Adminer:**

1. Navigate to `http://localhost:8080`
2. Select database
3. Click "Export" → Choose format (SQL recommended)
4. Click "Save output"

### Restore Database

**From SQL file:**

```bash
# Restore from backup
docker compose exec -T tux-postgres psql -U tuxuser -d tuxdb < backup_20240101.sql

# Restore with error checking
docker compose exec -T tux-postgres psql -U tuxuser -d tuxdb -v ON_ERROR_STOP=1 < backup_20240101.sql
```

**From custom format:**

```bash
docker compose exec -T tux-postgres pg_restore -U tuxuser -d tuxdb < backup_20240101.dump
```

**Using Adminer:**

1. Navigate to `http://localhost:8080`
2. Select database
3. Click "SQL command"
4. Paste SQL content or upload file
5. Click "Execute"

### Backup Volumes

**List volumes:**

```bash
docker volume ls | grep tux
```

**Backup volume:**

```bash
# Backup PostgreSQL data volume (using lightweight utility container)
docker run --rm \
  -v tux_postgres_data:/data \
  -v $(pwd):/backup \
  alpine:latest tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz -C /data .

# Backup all volumes (using lightweight utility container)
docker run --rm \
  -v tux_postgres_data:/data \
  -v tux_cache:/cache \
  -v tux_temp:/temp \
  -v tux_user_home:/home \
  -v $(pwd):/backup \
  alpine:latest sh -c "tar czf /backup/volumes_backup_$(date +%Y%m%d).tar.gz /data /cache /temp /home"
```

!!! note "Utility Container"
    The `alpine:latest` image is used here as a lightweight utility container for running tar commands. It's not related to the Tux application image, which uses `python:3.13.8-slim` (Debian-based).

**Restore volume:**

```bash
# Stop services first
docker compose down

# Restore volume (using lightweight utility container)
docker run --rm \
  -v tux_postgres_data:/data \
  -v $(pwd):/backup \
  alpine:latest sh -c "cd /data && tar xzf /backup/postgres_backup_20240101.tar.gz"

# Start services
docker compose up -d
```

## Monitoring

### Container Health

```bash
# Check health status
docker inspect tux --format='{{json .State.Health}}' | jq

# Check all health statuses
docker compose ps --format json | jq '.[] | {name: .Name, health: .Health}'
```

### Resource Usage

```bash
# Real-time stats
docker stats tux tux-postgres

# Container details
docker compose exec tux ps aux
docker compose exec tux df -h

# Memory usage
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

### Database Health

```bash
# Via CLI
docker compose exec tux uv run db health

# Direct PostgreSQL check
docker compose exec tux-postgres pg_isready -U tuxuser

# Check database size
docker compose exec tux-postgres psql -U tuxuser -d tuxdb -c "SELECT pg_size_pretty(pg_database_size('tuxdb'));"

# Check table sizes
docker compose exec tux-postgres psql -U tuxuser -d tuxdb -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Maintenance

### Clean Up

```bash
# Remove stopped containers
docker compose rm

# Remove unused images
docker image prune

# Remove unused volumes (⚠️ careful!)
docker volume prune

# Full cleanup (removes unused containers, networks, images, build cache)
docker system prune -a
```

### Update Images

```bash
# Pull latest images
docker compose pull

# Rebuild and restart
docker compose up -d --build

# Update specific service
docker compose pull tux
docker compose up -d tux
```

### View Container Information

```bash
# Inspect container
docker inspect tux

# View container logs location
docker inspect tux --format='{{.LogPath}}'

# View network configuration
docker network inspect tux_default

# View volume details
docker volume inspect tux_postgres_data
```

## Related Documentation

- **[Docker Installation](../install/docker.md)** - Initial setup and installation
- **[Production Deployment](../../reference/docker-production.md)** - Production deployment guide
- **[Docker Troubleshooting](../../support/troubleshooting/docker.md)** - Common issues and solutions
