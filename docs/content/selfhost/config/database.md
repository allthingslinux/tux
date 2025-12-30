---
title: Database Configuration
tags:
  - selfhost
  - configuration
  - database
---

# Database Configuration

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Configure database connection settings for Tux. For installation instructions, see [Bare Metal Installation](../install/baremetal.md).

!!! tip "Quick Start"
    If you're using Docker Compose, the database is configured automatically. Just set your `POSTGRES_PASSWORD` in `.env` and start services.

## Configuration Details

The `compose.yaml` includes a PostgreSQL service (`tux-postgres`) using the Alpine-based `postgres:17-alpine` image with optimized settings (256MB shared buffers, 100 max connections, UTC timezone). Connection details:

!!! note "Base Images"
    The Tux application uses `python:3.13.8-slim` (Debian-based), while PostgreSQL uses `postgres:17-alpine` (Alpine-based) for a smaller database image size.

- **Host:** `tux-postgres` (Docker network)
- **Database:** `tuxdb` (from `POSTGRES_DB`)
- **User:** `tuxuser` (from `POSTGRES_USER`)
- **Password:** From `POSTGRES_PASSWORD` environment variable
- **Port:** `5432` (configurable via `POSTGRES_PORT`)

Configure via environment variables in `.env`:

```env
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432
POSTGRES_HOST=tux-postgres
```

!!! tip "Configuration Priority"
    Environment variables override defaults. See [Environment Variables](environment.md) for full configuration options.

### Database Migrations

Migrations run automatically on Tux startup. The bot:

1. Waits for PostgreSQL to be healthy
2. Checks current database revision
3. Applies any pending migrations
4. Starts normally

!!! tip "Migration Files"
    In Docker, migration files are automatically mounted from `./src/tux/database/migrations` into the container. No additional configuration needed.

For manual migration management, see [Database Management](../manage/database.md).

## Connection Configuration

Tux supports two configuration methods:

**Individual Variables (Recommended):**

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_password
```

**Database URL Override:**

```env
# Custom database URL (overrides POSTGRES_* variables)
DATABASE_URL=postgresql://tuxuser:password@localhost:5432/tuxdb
```

!!! warning "URL Override"
    When `DATABASE_URL` is set, all `POSTGRES_*` variables are ignored. Use one method or the other.

### External Database Services

Tux works with managed PostgreSQL services (AWS RDS, DigitalOcean, Railway, Supabase, etc.). Use `DATABASE_URL` format:

```env
# Example: AWS RDS
DATABASE_URL=postgresql://tuxuser:password@your-instance.region.rds.amazonaws.com:5432/tuxdb?sslmode=require

# Example: DigitalOcean
DATABASE_URL=postgresql://tuxuser:password@your-host.db.ondigitalocean.com:25060/tuxdb?sslmode=require
```

!!! tip "SSL Connections"
    Most managed databases require SSL. Add `?sslmode=require` to your connection URL.

## Security Best Practices

**Password Security:**

- Use strong passwords (minimum 16 characters, mix of letters, numbers, symbols)
- Never commit passwords to version control
- Rotate passwords periodically
- Consider secrets management tools (`pass`, `1Password`, cloud secrets)

**Network Security:**

- **Docker:** Database only accessible within Docker network (no external port exposure needed)
- **Manual:** Configure `pg_hba.conf` to restrict access, use firewall rules, consider SSL/TLS

**Example `pg_hba.conf` for manual setup:**

```conf
# Local connections only
host    tuxdb    tuxuser    127.0.0.1/32    scram-sha-256
```

**Backup Security:**

- Encrypt backups before storing
- Use secure backup storage (encrypted volumes, cloud storage)
- Test restore procedures regularly

See [Database Management](../manage/database.md) for backup strategies.

## Database Health Checks

Verify your database setup:

```bash
# Check database connection
uv run db health

# Check migration status and history
uv run db status
uv run db history

# List tables and validate schema
uv run db tables
uv run db schema

# Docker-specific checks
docker compose ps tux-postgres
docker compose logs tux-postgres
docker compose exec tux-postgres psql -U tuxuser -d tuxdb
```

## Troubleshooting

**Connection Errors:**

```bash
# Check PostgreSQL is running
docker compose ps tux-postgres  # Docker
sudo systemctl status postgresql  # Manual

# Verify connection and network
uv run db health
docker compose exec tux ping tux-postgres  # Docker
telnet localhost 5432  # Manual
```

- **"Authentication failed":** Verify `POSTGRES_PASSWORD` matches, check `POSTGRES_USER` exists
- **"Database does not exist":** `docker compose exec tux-postgres psql -U postgres -c "CREATE DATABASE tuxdb;"`

**Migration Issues:**

```bash
# Check status and view details
uv run db status
uv run db show head

# Reset (WARNING: destroys data!)
uv run db reset
docker compose up -d tux
```

**Performance Issues:**

```bash
# Check long-running queries
uv run db queries
docker compose exec tux-postgres psql -U tuxuser -d tuxdb -c "SELECT * FROM pg_stat_activity;"
```

- Adjust `shared_buffers` in PostgreSQL config, reduce `max_connections`, monitor with `docker stats tux-postgres`

**Docker-Specific:**

- **Volume permissions:** `docker compose down && sudo chown -R 999:999 ./docker/postgres/data && docker compose up -d tux-postgres`
- **Port conflicts:** Change `POSTGRES_PORT` in `.env` and restart services

See [Database Management](../manage/database.md) for detailed troubleshooting.

## Adminer Web UI

Access your database through Adminer (included with Docker Compose):

**Access:** `http://localhost:8080`

**Auto-login enabled by default** (development only). Credentials:

- **System:** PostgreSQL
- **Server:** `tux-postgres`
- **Username:** `tuxuser`
- **Password:** (from your `.env`)
- **Database:** `tuxdb`

!!! danger "Production Security"
    **Disable auto-login in production:**
    Add `ADMINER_AUTO_LOGIN=false` to your `.env` file.
    Also ensure Adminer is not publicly accessible. Use SSH tunnels or VPN.

See [Database Management](../manage/database.md) for Adminer usage details.

## Next Steps

After configuring your database:

- [Bot Token Setup](bot-token.md) - Configure Discord bot token
- [Environment Variables](environment.md) - Complete configuration
- [First Run](../install/first-run.md) - Initial setup and testing
- [Database Management](../manage/database.md) - Backups, migrations, administration

---

For database management commands, see the [Database Management Guide](../manage/database.md).
