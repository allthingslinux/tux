---
title: Database Configuration
---

# Database Configuration

Tux uses PostgreSQL 17+ as its database. This guide covers setting up PostgreSQL using Docker Compose (recommended) or manually.

!!! tip "Quick Start"
    If you're using Docker Compose, the database is configured automatically. Just set your `POSTGRES_PASSWORD` in `.env` and start services.

## Database Requirements

**PostgreSQL Version:** 17.0 or higher

**Why PostgreSQL 17?**

- Modern features and performance improvements
- Better async support for Discord bot workloads
- Enhanced JSON and array handling
- Improved connection pooling

## Docker Compose Setup (Recommended)

The easiest way to run Tux's database is with Docker Compose. It handles PostgreSQL, connections, and migrations automatically.

### Quick Setup

1. **Configure Environment Variables**

Add to your `.env` file:

```env
# Database Configuration
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432
```

!!! danger "Change Default Password"
    The default password (`ChangeThisToAStrongPassword123!`) is insecure. **Always set a strong password** in production.

!!! tip "Automatic Database Creation"
    Docker Compose automatically creates the PostgreSQL user and database based on these environment variables. No manual database setup required!

2. **Start Database**

```bash
# Start PostgreSQL service
docker compose up -d tux-postgres

# Verify it's running
docker compose ps tux-postgres
```

3. **Start Tux**

The bot will automatically connect and run migrations:

```bash
docker compose up -d tux
```

### Configuration Details

The `compose.yaml` includes a PostgreSQL service (`tux-postgres`) using `postgres:17-alpine` with optimized settings (256MB shared buffers, 100 max connections, UTC timezone). Connection details:

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

**Manual Migration Control:**

```env
# Force migration on startup (use with caution)
# When true, stamps database as head without running migrations
FORCE_MIGRATE=true
```

!!! warning "Force Migration Warning"
    `FORCE_MIGRATE=true` bypasses normal migration execution and stamps the database as "head". Only use this if you understand the risks and have data backups.

!!! tip "Migration Files"
    In Docker, migration files are automatically mounted from `./src/tux/database/migrations` into the container. No additional configuration needed.

For manual migration management, see [Database Management](../manage/database.md).

## Manual PostgreSQL Setup

!!! info "Docker Users Skip This"
    **If you're using Docker Compose, skip this section entirely.** Docker automatically creates the user and database based on your environment variables (`POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`). You only need this section if you're running PostgreSQL manually outside of Docker.

If you prefer to run PostgreSQL manually (not in Docker), follow these steps.

### Installation

**Ubuntu:**

PostgreSQL is included in Ubuntu by default, but for PostgreSQL 17+, use the official PostgreSQL Apt repository:

#### Automated Repository Setup (Recommended)

```bash
# Install PostgreSQL common utilities
sudo apt install -y postgresql-common

# Configure PostgreSQL Apt repository automatically
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Install PostgreSQL 17
sudo apt install postgresql-17

# Start PostgreSQL service
sudo systemctl enable --now postgresql
```

#### Manual Repository Setup

```bash
# Import the repository signing key
sudo apt install curl ca-certificates
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc

# Create the repository configuration file
. /etc/os-release
sudo sh -c "echo 'deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $VERSION_CODENAME-pgdg main' > /etc/apt/sources.list.d/pgdg.list"

# Update package lists
sudo apt update

# Install PostgreSQL 17
sudo apt install postgresql-17

# Start PostgreSQL service
sudo systemctl enable --now postgresql
```

### Database Creation

When running PostgreSQL manually, you need to create the user and database yourself:

1. **Create Database User and Database**

```bash
sudo -u postgres psql
```

```sql
-- Create user
CREATE USER tuxuser WITH PASSWORD 'your_secure_password_here';

-- Create database
CREATE DATABASE tuxdb OWNER tuxuser;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tuxdb TO tuxuser;

-- Exit
\q
```

!!! tip "Why Manual Setup?"
    Unlike Docker (which auto-creates via environment variables), manual PostgreSQL installations require you to create users and databases yourself. This is standard PostgreSQL behavior.

2. **Configure Connection**

Add to your `.env` file:

```env
# Manual PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password_here
```

3. **Test Connection**

```bash
# Test database connection
uv run db health

# Should show: Database connection healthy
```

### PostgreSQL Configuration

For manual installations, optimize PostgreSQL for Tux:

**Edit `/etc/postgresql/17/main/postgresql.conf`:**

```conf
# Connection settings
max_connections = 100
shared_buffers = 256MB
work_mem = 16MB
maintenance_work_mem = 128MB

# Logging
log_statement = 'ddl'
log_min_duration_statement = 1000
log_lock_waits = on
track_io_timing = on

# Timezone
timezone = 'UTC'
```

**Restart PostgreSQL:**

```bash
sudo systemctl restart postgresql
```

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

# Reset (WARNING: destroys data!) or force migration
uv run db reset
FORCE_MIGRATE=true docker compose up -d tux
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
