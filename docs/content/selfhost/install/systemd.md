---
title: Installation via Systemd
---

# Installation via Systemd

Install Tux directly on your system without Docker. This guide covers both quick start for development and production deployment with systemd.

## Quick Start (Development)

For quick testing or development, you can run Tux directly:

```bash
# Clone repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Install dependencies
uv sync

# Generate configuration files
uv run config generate

# Copy and edit .env
cp .env.example .env
nano .env

# Run migrations
uv run db push

# Start bot
uv run tux start
```

For production deployment, continue with the systemd setup below.

## Production Deployment with Systemd

### Prerequisites

Before deploying with systemd, ensure you have:

- **Linux system** with systemd (most modern distributions)
- **Python 3.13+** installed
- **[uv](https://docs.astral.sh/uv/)** package manager installed
- **PostgreSQL 13+** database running
- **Discord bot token** from [Discord Developer Portal](https://discord.com/developers/applications)
- **Root or sudo access** for systemd service creation

### Installation Steps

#### 1. Create System User

Create a dedicated user for running Tux (recommended for security):

```bash
# Create system user with home directory at /opt/tux
sudo useradd -r -s /bin/bash -d /opt/tux -m tux

# Or create system user without home directory (if preferred)
# sudo useradd -r -s /usr/bin/nologin -d /opt/tux tux
```

#### 2. Clone Repository to /opt/tux

Clone the Tux repository directly to the installation directory:

```bash
# Clone repository as tux user
sudo -u tux git clone https://github.com/allthingslinux/tux.git /opt/tux

# Set ownership (ensure tux user owns everything)
sudo chown -R tux:tux /opt/tux

# Set appropriate permissions
sudo chmod 755 /opt/tux
```

#### 3. Install Dependencies

Install Tux dependencies using uv:

```bash
# Switch to tux user and install dependencies
sudo -u tux bash -c "cd /opt/tux && uv sync"

# Generate configuration files
sudo -u tux bash -c "cd /opt/tux && uv run config generate"

# Protect .env file if it exists
if [ -f /opt/tux/.env ]; then
    sudo chmod 600 /opt/tux/.env
    sudo chown tux:tux /opt/tux/.env
fi
```

#### 4. Configure Environment

Tux automatically reads environment variables from `.env` file in the working directory. Create or edit the `.env` file:

```bash
# Create or edit .env file
sudo -u tux nano /opt/tux/.env
```

Add your configuration:

```env
# Discord Bot Token (required)
BOT_TOKEN=your_bot_token_here

# Database Configuration (required)
# Option 1: Use individual PostgreSQL variables
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tux
POSTGRES_USER=tux_user
POSTGRES_PASSWORD=your_secure_password_here

# Option 2: Or use DATABASE_URL override
# DATABASE_URL=postgresql://tux_user:password@localhost:5432/tux

# Optional: Logging
LOG_LEVEL=INFO
DEBUG=false

# Optional: Bot Configuration
USER_IDS__BOT_OWNER_ID=123456789012345678
BOT_INFO__PREFIX=$

# Optional: External Services
EXTERNAL_SERVICES__SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

Set secure permissions:

```bash
sudo chmod 600 /opt/tux/.env
sudo chown tux:tux /opt/tux/.env
```

!!! note "Alternative: Systemd Environment File"
    You can also use a separate systemd environment file at `/etc/tux/environment` if you prefer to separate system-level configuration from application configuration. If using this approach, add `EnvironmentFile=/etc/tux/environment` to the systemd service file.

#### 5. Configure Database

Ensure PostgreSQL is configured and accessible:

```bash
# Create database user (if not exists)
sudo -u postgres createuser -P tux_user

# Create database
sudo -u postgres createdb -O tux_user tux

# Run migrations
cd /opt/tux
sudo -u tux uv run db push
```

#### 6. Find uv Installation Path

Before creating the service file, find where `uv` is installed:

```bash
# Find uv executable
which uv

# Common locations:
# - /usr/local/bin/uv (standalone installer)
# - /usr/bin/uv (package manager)
# - ~/.cargo/bin/uv (cargo installation)
# - ~/.local/bin/uv (pip --user)
```

If `uv` is not in a system path, you can either:

1. **Create a symlink** (recommended):

   ```bash
   sudo ln -s $(which uv) /usr/local/bin/uv
   ```

2. **Use full path** in the service file (replace `/usr/local/bin/uv` with your path)

#### 7. Create Systemd Service File

Create the systemd service unit:

```bash
sudo nano /etc/systemd/system/tux.service
```

Use this configuration (adjust the `uv` path if needed):

```ini
[Unit]
Description=Tux Discord Bot
Documentation=https://tux.atl.dev
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=tux
Group=tux
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

#### 8. Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable tux

# Start the service
sudo systemctl start tux

# Check status
sudo systemctl status tux
```

## Service Management

### Basic Commands

```bash
# Start service
sudo systemctl start tux

# Stop service
sudo systemctl stop tux

# Restart service
sudo systemctl restart tux

# Reload service (sends HUP signal)
sudo systemctl reload tux

# Enable on boot
sudo systemctl enable tux

# Disable on boot
sudo systemctl disable tux

# Check status
sudo systemctl status tux

# View logs
sudo journalctl -u tux -f

# View recent logs
sudo journalctl -u tux -n 100

# View logs since boot
sudo journalctl -u tux -b

# View logs for specific time period
sudo journalctl -u tux --since "1 hour ago"
sudo journalctl -u tux --since "2024-01-01 00:00:00" --until "2024-01-02 00:00:00"
```

### Advanced Logging

```bash
# Follow logs in real-time
sudo journalctl -u tux -f

# Filter by log level
sudo journalctl -u tux -p err
sudo journalctl -u tux -p warning

# Search logs
sudo journalctl -u tux | grep ERROR
sudo journalctl -u tux | grep "database"

# Export logs
sudo journalctl -u tux --since "1 day ago" > tux-logs.txt

# View logs with timestamps
sudo journalctl -u tux --since "1 hour ago" --no-pager
```

## Configuration Updates

### Updating Environment Variables

```bash
# Edit .env file
sudo -u tux nano /opt/tux/.env

# Reload service to apply changes
sudo systemctl daemon-reload
sudo systemctl restart tux
```

### Updating Tux Code

```bash
# Stop service
sudo systemctl stop tux

# Backup current installation
sudo cp -r /opt/tux /opt/tux.backup.$(date +%Y%m%d)

# Update code
cd /opt/tux
sudo -u tux git pull origin main

# Update dependencies
sudo -u tux uv sync

# Run database migrations
sudo -u tux uv run db push

# Start service
sudo systemctl start tux

# Verify status
sudo systemctl status tux
```

## Monitoring

### Health Checks

```bash
# Check service status
sudo systemctl is-active tux
sudo systemctl is-enabled tux

# Check if bot is responding
# In Discord, use /ping command

# Check database connection
sudo -u tux uv run db health

# Check resource usage
systemctl status tux | grep -A 5 "Memory\|CPU"
```

### Resource Monitoring

```bash
# Monitor resource usage
sudo systemctl status tux

# View detailed resource usage
systemd-cgtop

# Check memory usage
ps aux | grep tux

# Monitor disk usage
df -h /opt/tux
```

## Troubleshooting

### Service Won't Start

**Check service status:**

```bash
sudo systemctl status tux
```

**Common issues:**

1. **Permission errors:**

   ```bash
   # Check file ownership
   ls -la /opt/tux
   sudo chown -R tux:tux /opt/tux
   ```

2. **Missing dependencies:**

   ```bash
   # Verify uv is installed
   which uv
   
   # Check Python version
   python3 --version
   ```

3. **Database connection issues:**

   ```bash
   # Test database connection
   sudo -u tux uv run db health
   
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   ```

4. **Invalid bot token:**

   ```bash
   # Check .env file
   sudo cat /opt/tux/.env | grep BOT_TOKEN
   ```

### Service Crashes Repeatedly

**Check logs for errors:**

```bash
sudo journalctl -u tux -n 100 --no-pager
```

**Common causes:**

- Invalid configuration
- Database connection failures
- Missing environment variables
- Permission issues
- Resource exhaustion

**Check restart count:**

```bash
systemctl show tux | grep NRestarts
```

### Logs Not Appearing

**Verify logging configuration:**

```bash
# Check journald is working
sudo journalctl -u tux -n 10

# Check service output
sudo systemctl status tux

# Verify log directory permissions
ls -la /var/log/tux
```

### Permission Denied Errors

**Fix ownership:**

```bash
sudo chown -R tux:tux /opt/tux
sudo chown tux:tux /var/log/tux
```

**Check service user:**

```bash
# Verify service runs as correct user
systemctl show tux | grep User
```

### Database Connection Issues

**Test connection manually:**

```bash
# As tux user
sudo -u tux bash -c "cd /opt/tux && uv run db health"

# Check PostgreSQL is accessible
sudo -u postgres psql -c "SELECT version();"
```

**Verify environment:**

```bash
# Check DATABASE_URL or POSTGRES_* variables are set
sudo cat /opt/tux/.env | grep -E "DATABASE_URL|POSTGRES_"
```

## Security Best Practices

### File Permissions

```bash
# Protect .env file
sudo chmod 600 /opt/tux/.env
sudo chown tux:tux /opt/tux/.env

# Protect configuration files
sudo chmod 600 /opt/tux/config/config.toml
sudo chown tux:tux /opt/tux/config/config.toml
```

### Network Security

```bash
# If using firewall, allow Discord connections
# Discord uses ports 443 (HTTPS) and 80 (HTTP)
# No special firewall rules needed for outbound connections
```

## Advanced Configuration

### Custom Working Directory

If installing to a different location:

```ini
[Service]
WorkingDirectory=/home/tux/tux
ExecStart=/usr/local/bin/uv run tux start
```

!!! note "Finding uv Path"
    Use `which uv` to find the correct path to the `uv` executable on your system.

### Debug Mode

Enable debug logging:

```bash
# Edit .env file
sudo -u tux nano /opt/tux/.env

# Add or modify:
DEBUG=true
LOG_LEVEL=DEBUG

# Restart service
sudo systemctl restart tux
```

### Resource Limits

Adjust resource limits in service file:

```ini
[Service]
# Memory limit (512MB)
MemoryMax=512M

# CPU limit (50% of one core)
CPUQuota=50%

# I/O limits
IOWeight=100
```

## Maintenance

### Regular Updates

Create update script (`/usr/local/bin/update-tux.sh`):

```bash
#!/bin/bash
set -e

echo "Stopping Tux..."
sudo systemctl stop tux

echo "Backing up installation..."
sudo cp -r /opt/tux /opt/tux.backup.$(date +%Y%m%d)

echo "Updating Tux..."
cd /opt/tux
sudo -u tux git pull origin main

echo "Updating dependencies..."
sudo -u tux uv sync

echo "Running migrations..."
sudo -u tux uv run db push

echo "Starting Tux..."
sudo systemctl start tux

echo "Update complete!"
```

Make executable:

```bash
sudo chmod +x /usr/local/bin/update-tux.sh
```

### Backup Strategy

```bash
# Backup script
#!/bin/bash
BACKUP_DIR=/backup/tux
DATE=$(date +%Y%m%d_%H%M%S)

# Stop service
sudo systemctl stop tux

# Backup database
sudo -u postgres pg_dump tux > $BACKUP_DIR/db_$DATE.sql

# Backup configuration
sudo tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/tux /opt/tux/.env /opt/tux/config

# Start service
sudo systemctl start tux

echo "Backup complete: $BACKUP_DIR"
```

## Related Documentation

- **[Environment Configuration](../config/environment.md)** - Environment variable reference
- **[Database Setup](../config/database.md)** - Database configuration
- **[System Operations](../manage/operations.md)** - Monitoring and maintenance
- **[First Run](first-run.md)** - Initial setup verification

---

**Next Steps:** After deploying with systemd, verify your installation with the [First Run Guide](first-run.md).
