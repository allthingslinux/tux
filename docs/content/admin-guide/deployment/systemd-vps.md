# VPS Deployment with Systemd

Deploy Tux on a VPS using systemd for process management.

!!! warning "Advanced"
    This guide assumes Linux system administration experience. For easier deployment, see [Docker Compose](docker-compose.md).

## Overview

This deployment method:

- Runs Tux directly on the host (no containers)
- Uses systemd for process management
- Requires manual PostgreSQL setup
- Gives full control over the environment

## Prerequisites

- **Linux VPS** (Ubuntu 22.04+, Debian 12+, or similar)
- **Root or sudo access**
- **Python 3.13+**
- **PostgreSQL 15+**
- **2GB+ RAM** recommended
- **SSH access**

## Installation Steps

### 1. System Update

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib git curl

# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 3. Set Up PostgreSQL

```bash
# Create database and user
sudo -u postgres createdb tuxdb
sudo -u postgres createuser tuxuser

# Set password and grant permissions
sudo -u postgres psql << EOF
ALTER USER tuxuser WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE tuxdb TO tuxuser;
ALTER DATABASE tuxdb OWNER TO tuxuser;
EOF
```

### 4. Create Service User

```bash
# Create dedicated user for running Tux
sudo useradd -r -m -s /bin/bash tux
sudo -u tux -i
```

### 5. Clone and Install Tux

```bash
# As tux user
cd ~
git clone https://github.com/allthingslinux/tux.git
cd tux

# Install dependencies
uv sync
```

### 6. Configure Environment

```bash
# Create .env file
cat > .env << 'EOF'
BOT_TOKEN=your_discord_bot_token
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password
ENVIRONMENT=production
DEBUG=false
EOF

# Secure permissions
chmod 600 .env
```

### 7. Run Migrations

```bash
uv run db push
```

### 8. Test Bot

```bash
# Test run
uv run tux start

# Should connect to Discord
# Press Ctrl+C to stop
```

### 9. Create Systemd Service

Exit the tux user shell and create service file:

```bash
# As root/sudo
sudo nano /etc/systemd/system/tux.service
```

Service file content:

```ini
[Unit]
Description=Tux Discord Bot
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=tux
Group=tux
WorkingDirectory=/home/tux/tux
Environment=PATH=/home/tux/tux/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/tux/tux/.venv/bin/python -m tux
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tux

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/tux/tux/data /home/tux/tux/logs
ProtectKernelTunables=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
```

### 10. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable tux

# Start service
sudo systemctl start tux

# Check status
sudo systemctl status tux
```

## Management Commands

### Service Control

```bash
# Start
sudo systemctl start tux

# Stop
sudo systemctl stop tux

# Restart
sudo systemctl restart tux

# Status
sudo systemctl status tux

# Enable (start on boot)
sudo systemctl enable tux

# Disable (don't start on boot)
sudo systemctl disable tux
```

### Logs

```bash
# View recent logs
sudo journalctl -u tux -n 100

# Follow logs
sudo journalctl -u tux -f

# Logs since boot
sudo journalctl -u tux -b

# Logs from last hour
sudo journalctl -u tux --since "1 hour ago"

# Search logs
sudo journalctl -u tux | grep ERROR
```

### Database Operations

```bash
# As tux user
sudo -u tux -i
cd ~/tux

# Run migrations
uv run db push

# Check health
uv run db health

# Backup database
pg_dump -h localhost -U tuxuser tuxdb > backup_$(date +%Y%m%d).sql
```

## Updating Tux

```bash
# As tux user
sudo -u tux -i
cd ~/tux

# Pull latest changes
git pull

# Update dependencies
uv sync

# Run new migrations
uv run db push

# Exit tux user
exit

# Restart service
sudo systemctl restart tux

# Check logs
sudo journalctl -u tux -f
```

## Monitoring

### Log Rotation

Create logrotate configuration:

```bash
sudo nano /etc/logrotate.d/tux
```

Content:

```text
/home/tux/tux/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 tux tux
    postrotate
        systemctl reload tux > /dev/null 2>&1 || true
    endscript
}
```

### Health Monitoring

Create health check script:

```bash
sudo nano /usr/local/bin/check-tux.sh
```

Content:

```bash
#!/bin/bash
if ! systemctl is-active --quiet tux; then
    echo "Tux is down! Restarting..."
    systemctl restart tux
    
    # Optional: Send alert
    # curl -X POST webhook_url -d "Tux restarted"
fi
```

Add to cron:

```bash
# Check every 5 minutes
*/5 * * * * /usr/local/bin/check-tux.sh
```

## Security

### Firewall

```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow PostgreSQL (only if needed externally)
# sudo ufw allow 5432/tcp

# Enable firewall
sudo ufw enable
```

### PostgreSQL Security

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/15/main/postgresql.conf

# Listen only on localhost
listen_addresses = 'localhost'

# Reload
sudo systemctl reload postgresql
```

### Service Hardening

The provided systemd service includes security features:

- `NoNewPrivileges` - Prevent privilege escalation
- `PrivateTmp` - Isolated /tmp
- `ProtectSystem` - Read-only system directories
- `ProtectHome` - Protected home directories

## Troubleshooting

### Service Won't Start

```bash
# Check status
sudo systemctl status tux

# Check logs
sudo journalctl -u tux -n 50

# Validate service file
systemd-analyze verify tux.service

# Test manually
sudo -u tux -i
cd ~/tux
uv run tux start
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R tux:tux /home/tux/tux

# Fix .env permissions
sudo -u tux chmod 600 /home/tux/tux/.env
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U tuxuser -d tuxdb

# Check pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

## Performance Tuning

### PostgreSQL

Edit `/etc/postgresql/15/main/postgresql.conf`:

```ini
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 1GB          # 50-75% of RAM
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### System Resources

Monitor with:

```bash
htop                                # Interactive process viewer
free -h                             # Memory usage
df -h                               # Disk usage
```

## Advantages & Disadvantages

### ✅ Advantages

- Maximum performance (no container overhead)
- Complete control
- Direct access to everything
- Easier debugging
- Lower resource usage

### ❌ Disadvantages

- More complex setup
- Manual dependency management
- Harder updates
- Requires Linux experience
- More maintenance

## Next Steps

1. **[Configure Tux](../configuration/index.md)** - Set up features
2. **[Set Up Backups](../database/backups.md)** - Protect your data
3. **[Configure Monitoring](../operations/monitoring.md)** - Watch for issues
4. **[Security Hardening](../security/best-practices.md)** - Lock it down

---

**Alternative:** Try [Docker Compose](docker-compose.md) for easier management.
