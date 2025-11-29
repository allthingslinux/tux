---
title: Database Installation
tags:
  - selfhost
  - installation
  - database
---

# Database Installation

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Tux uses PostgreSQL 17+ as its database. This guide covers installing PostgreSQL using Docker Compose (recommended) or manually.

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

## Manual PostgreSQL Setup

!!! warning "Docker Users Skip This"
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

## Next Steps

After installing your database:

- [Database Configuration](../config/database.md) - Configure database connection settings
- [Bot Token Setup](../config/bot-token.md) - Configure Discord bot token
- [First Run](first-run.md) - Initial setup and testing
