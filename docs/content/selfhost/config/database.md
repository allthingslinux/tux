# Database Setup

Tux requires PostgreSQL for data storage. This guide covers setting up the database.

## PostgreSQL Requirements

- **Version:** PostgreSQL 12+ (15+ recommended)
- **Storage:** 1GB minimum (more for large servers)
- **Encoding:** UTF-8
- **Collation:** C (for performance)

## Setup Options

### Option 1: Docker Compose (Easiest)

If using Docker Compose, PostgreSQL is included:

```bash
docker compose up -d tux-postgres
```

**That's it!** Database is automatically configured.

Connection details from `.env`:

- Host: `tux-postgres` (container name)
- Port: `5432`
- Database: `tuxdb`
- User: `tuxuser`
- Password: (set in `.env`)

### Option 2: Local PostgreSQL

#### Install PostgreSQL

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**

```bash
brew install postgresql@17
brew services start postgresql@17
```

**Arch Linux:**

```bash
sudo pacman -S postgresql
sudo -u postgres initdb -D /var/lib/postgres/data
sudo systemctl start postgresql
```

#### Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Or directly:
sudo -u postgres createdb tuxdb
sudo -u postgres createuser tuxuser

# Set password and permissions
sudo -u postgres psql << EOF
ALTER USER tuxuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE tuxdb TO tuxuser;
ALTER DATABASE tuxdb OWNER TO tuxuser;

-- For PostgreSQL 15+, grant schema privileges
\c tuxdb
GRANT ALL ON SCHEMA public TO tuxuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tuxuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tuxuser;
EOF
```

### Option 3: Managed Database

Use a cloud PostgreSQL service:

#### Supabase

1. Create project at [supabase.com](https://supabase.com)
2. Get connection string from project settings
3. Use in `.env` as `DATABASE_URL`

#### Railway

1. Add PostgreSQL plugin to your Railway project
2. Copy connection variables
3. Set in `.env`

#### DigitalOcean Managed Database

1. Create PostgreSQL cluster
2. Get connection details
3. Configure in `.env`

## Connection Configuration

### Using Individual Parameters

In `.env`:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password
```

### Using Connection URL

Alternatively, use a single DATABASE_URL:

```bash
DATABASE_URL=postgresql://tuxuser:password@localhost:5432/tuxdb
```

Connection URL format:

```
postgresql://user:password@host:port/database
```

## Verify Connection

### Test Connection

```bash
# Using psql
psql -h localhost -U tuxuser -d tuxdb

# You should see:
# tuxdb=#

# Exit with \q
```

### Using Tux CLI

```bash
# After configuring .env
uv run db health
```

Should show: "Database is healthy!"

## Initialize Database

### Run Migrations

After database is set up:

```bash
# Apply all migrations
uv run db push

# Or initialize fresh database
uv run db init
```

This creates all required tables.

### Verify Tables

```bash
# List all tables
uv run db tables

# Should show:
# - guilds
# - guild_config
# - cases
# - snippets
# - levels
# - And more...
```

## Database Configuration

### PostgreSQL Tuning

For better performance, edit `postgresql.conf`:

```conf
# Memory Settings
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 1GB          # 50% of RAM
work_mem = 16MB
maintenance_work_mem = 128MB

# Connection Settings
max_connections = 100

# Performance
random_page_cost = 1.1              # For SSD
effective_io_concurrency = 200      # For SSD
```

Restart PostgreSQL after changes:

```bash
sudo systemctl restart postgresql
```

### Connection Pooling

Tux uses connection pooling. Configure in code or environment:

```bash
# In .env (if using DATABASE_URL)
DATABASE_URL=postgresql://user:pass@host/db?pool_size=20&max_overflow=10
```

## Security

### Strong Password

Generate secure password:

```bash
# Generate 32-character password
openssl rand -base64 32
```

Use this for `POSTGRES_PASSWORD`.

### Network Access

**Local development:**

- PostgreSQL listens on localhost only (default)
- No external access needed

**Production:**

- Keep localhost-only if bot and DB are co-located
- Use SSL/TLS if database is remote
- Firewall PostgreSQL port (5432)

### Authentication

Edit `pg_hba.conf` for authentication:

```
# Allow local connections
local   all             all                                     peer
host    all             all             127.0.0.1/32            scrypt
```

## Troubleshooting

### Can't Connect to Database

**Check PostgreSQL is running:**

```bash
# Linux
sudo systemctl status postgresql

# macOS
brew services list | grep postgresql

# Docker
docker compose ps tux-postgres
```

**Check connection details:**

```bash
# Test with psql
psql -h localhost -U tuxuser -d tuxdb -c "SELECT version();"
```

### Authentication Failed

**Causes:**

- Wrong password
- User doesn't exist
- pg_hba.conf restrictions

**Solutions:**

```bash
# Reset password
sudo -u postgres psql -c "ALTER USER tuxuser PASSWORD 'new_password';"

# Check user exists
sudo -u postgres psql -c "\du"

# Check pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

### Permission Denied

**Cause:** User lacks database privileges

**Solution:**

```bash
sudo -u postgres psql << EOF
GRANT ALL PRIVILEGES ON DATABASE tuxdb TO tuxuser;
\c tuxdb
GRANT ALL ON SCHEMA public TO tuxuser;
EOF
```

### Database Doesn't Exist

**Cause:** Database not created

**Solution:**

```bash
sudo -u postgres createdb tuxdb
sudo -u postgres psql -c "ALTER DATABASE tuxdb OWNER TO tuxuser;"
```

## Backups

Set up regular backups from the start:

```bash
# Manual backup
pg_dump -h localhost -U tuxuser tuxdb > backup.sql

# Compressed
pg_dump -h localhost -U tuxuser tuxdb | gzip > backup.sql.gz
```

**[Full Backup Guide →](../database/backups.md)**

## For Different Environments

### Development

```bash
POSTGRES_HOST=localhost
POSTGRES_DB=tuxdb_dev
POSTGRES_PASSWORD=devpassword123
```

### Production

```bash
POSTGRES_HOST=your-db-host
POSTGRES_DB=tuxdb
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### Docker

```bash
POSTGRES_HOST=tux-postgres          # Container name
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=ChangeThisToAStrongPassword123!
```

## Next Steps

1. **[Configure Environment Variables](environment-variables.md)** - Set up `.env`
2. **[Run First Start](first-run.md)** - Start Tux for the first time
3. **[Database Migrations](../database/migrations.md)** - Learn migration management

---

**Next:** [Configure environment variables →](environment-variables.md)
