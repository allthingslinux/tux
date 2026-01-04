---
title: Bare Metal Installation
tags:
  - selfhost
  - installation
  - baremetal
  - systemd
  - postgresql
---

# Bare Metal Installation

This guide provides instructions for installing Tux directly on a Linux system using systemd and a manual PostgreSQL installation.

!!! tip "Docker Recommended"
    For most users, we recommend the [Docker Installation](docker.md) as it handles dependencies and database setup automatically.

## Prerequisites

Before starting the installation, ensure your system meets the following requirements:

- **Linux system** with systemd (Ubuntu 22.04+ recommended)
- **Python 3.13+** installed
- **Git** installed
- **Discord bot token** from the [Discord Developer Portal](https://discord.com/developers/applications)
- **Root or sudo access**

## 1. Install PostgreSQL 17

Tux requires PostgreSQL 17 or higher. On Ubuntu/Debian systems, you can install it using the official PostgreSQL repository.

### Automated Repository Setup

```bash
# Install PostgreSQL common utilities
sudo apt install -y postgresql-common

# Configure PostgreSQL Apt repository automatically
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Install PostgreSQL 17
sudo apt install -y postgresql-17

# Start and enable PostgreSQL
sudo systemctl enable --now postgresql
```

### Database and User Creation

After installing PostgreSQL, create a database and user for Tux:

```bash
# Access PostgreSQL prompt
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

!!! danger "Security Note"
    Always use a strong, unique password for your database user.

## 2. Install uv

Tux uses `uv` for dependency management. Install it system-wide:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

!!! note "Update PATH"
    Ensure `uv` is in your PATH. You may need to source your shell profile or add it to your PATH manually.

## 3. Install Tux

### Clone Repository

Install Tux to `/opt/tux`:

```bash
# Clone repository
sudo git clone https://github.com/allthingslinux/tux.git /opt/tux
cd /opt/tux
```

### Install Dependencies

```bash
# Install dependencies
sudo uv sync

# Generate configuration files
sudo uv run config generate

# Create .env file from example
sudo cp .env.example .env
```

## 4. Configuration

Edit the `/opt/tux/.env` file to configure your bot token and database connection:

```bash
sudo nano /opt/tux/.env
```

**Required variables for bare metal setup:**

```env
# Discord Bot Token
BOT_TOKEN=your_bot_token_here

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password_here
```

### Verify Database Connection

Before setting up the service, test the database connection:

```bash
cd /opt/tux
sudo uv run db health
```

## 5. Systemd Service Setup

### Create Service File

Create the systemd service unit at `/etc/systemd/system/tux.service`:

```bash
sudo nano /etc/systemd/system/tux.service
```

Paste the following configuration:

```ini
[Unit]
Description=Tux Discord Bot
Documentation=https://tux.atl.dev
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/tux
ExecStart=/usr/local/bin/uv run tux start
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tux

[Install]
WantedBy=multi-user.target
```

!!! note "uv Path"
    If `uv` was installed in a different location, update the `ExecStart` path accordingly. You can find it with `which uv`.

### Start and Enable Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable tux --now

# Verify status
sudo systemctl status tux
```

## Maintenance

### Updating Tux

To update Tux to the latest version:

```bash
# Stop service
sudo systemctl stop tux

# Update code and dependencies
cd /opt/tux
sudo git pull origin main
sudo uv sync

# Restart service (migrations run automatically)
sudo systemctl start tux
```

### Viewing Logs

Use `journalctl` to view the bot's logs:

```bash
# View last 100 lines
sudo journalctl -u tux -n 100 --no-pager

# Follow logs in real-time
sudo journalctl -u tux -f
```

## Troubleshooting

### Common Issues

- **Database Connection Refused**: Ensure PostgreSQL is running (`systemctl status postgresql`) and the database exists. Check PostgreSQL authentication settings in `pg_hba.conf`.
- **uv: command not found**: Ensure the full path to `uv` is used in the service file. Check the path with `which uv`.
- **Permission Denied**: Ensure the service has read access to `/opt/tux` and write access to any data directories.

---

**Next Steps:** After completing the installation, follow the [First Run Guide](first-run.md) to verify the bot is working correctly.
