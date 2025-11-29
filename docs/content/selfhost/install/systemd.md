---
title: Systemd
tags:
  - selfhost
  - installation
  - systemd
---

# Systemd Installation

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

This guide provides information on installing and managing Tux using systemd on a Linux system.

## Prerequisites

Before deploying with systemd, ensure you have:

- **Linux system** with systemd (most modern distributions)
- **Python 3.13+** installed
- **PostgreSQL 17+** database running
- **Discord bot token** from the [Discord Developer Portal](https://discord.com/developers/applications)
- **Root or sudo access** for systemd service creation

## Installation Steps

### 1. Create System User and Install uv

Create a dedicated user for running Tux (recommended for security):

```bash
sudo useradd -m -d /home/tux -s /bin/bash tux
```

Once you are done, install `uv` using the instructions from the [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/). Make sure to run the installation as the `tux` user or install it system-wide.

### 2. Clone Repository

!!! info "Installation Directory"
    We will be using the `/opt/tux` directory in this guide however you can use other directories and adjust the steps.

Clone the Tux repository directly to the installation directory:

```bash
# Clone repository as tux user
sudo git clone https://github.com/allthingslinux/tux.git /opt

# Set ownership
sudo chown -R tux:tux /opt/tux
```

### 3. Install Dependencies

Install Tux dependencies using uv:

```bash
# Switch to tux user and install dependencies
sudo -u tux bash -c "cd /opt/tux && uv sync"

# Generate configuration files
sudo -u tux bash -c "cd /opt/tux && uv run config generate"

# Create .env file
sudo -u tux cp /opt/tux/.env.example /opt/tux/.env

# Optional: Adjust file permissions so only tux user can read/write .env
# sudo chmod 600 /opt/tux/.env
```

### 4. Configure Environment

Edit the `.env` file and setup necessary environment variables:

```bash
# Edit .env file
sudo -u tux nano /opt/tux/.env
```

!!! note "Alternative: Systemd Environment File"
    You can also use a separate systemd environment file at `/etc/tux/environment` if you prefer to separate system-level configuration from application configuration. If using this approach, add `EnvironmentFile=/etc/tux/environment` to the systemd service file.

### 5. Set Up Database

For PostgreSQL installation and database setup instructions, see [Database Installation](database.md). If you don't want to manage the database yourself, consider using a managed PostgreSQL service such as [Supabase](https://supabase.com/).

### 6. Create Systemd Service File

Create the systemd service unit:

```bash
sudo nano /etc/systemd/system/tux.service
```

Use this configuration (remove `postgresql.service` from `After` if not using local database):

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
ExecStart=uv run tux start
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tux

[Install]
WantedBy=multi-user.target
```

### 7. Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot and start immediately
sudo systemctl enable tux --now

# Check status after 15 seconds
sleep 15
sudo systemctl status tux
```

## Managing the Service

### Update Environment Variables

```bash
# Edit .env file
sudo -u tux nano /opt/tux/.env

# Reload service to apply changes
sudo systemctl daemon-reload
sudo systemctl restart tux
```

### Update Tux Installation

!!! warning "Backups"
    We heavily recommend backing up your installation and database before performing updates.

```bash
# Stop service
sudo systemctl stop tux

# Update code
cd /opt/tux
sudo -u tux git pull origin main

# Update dependencies
sudo -u tux uv sync

# Restart service (migrations run automatically on startup)
sudo systemctl restart tux

# Verify status
sleep 15
sudo systemctl status tux
```

## Troubleshooting

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

echo "Restarting Tux (migrations run automatically)..."
sudo systemctl restart tux

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
