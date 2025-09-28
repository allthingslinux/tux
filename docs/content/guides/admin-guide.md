# Administrator Guide

This guide covers deployment, configuration, and administration of Tux for server administrators and
self-hosters.

## Deployment Options

### Docker Deployment (Recommended)

**Prerequisites:**

- Docker and Docker Compose installed
- PostgreSQL database (local or hosted)
- Discord bot token

**Quick Start:**

```bash
# Clone the repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Start with Docker Compose
docker-compose up -d
```

**Docker Compose Configuration:**

```yaml
version: '3.8'
services:
  tux:
    build: .
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    restart: unless-stopped
    depends_on:
      - postgres
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=tux
      - POSTGRES_USER=tux
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Production Considerations:**

- Use external PostgreSQL for production
- Configure proper logging and monitoring
- Set up automated backups
- Use secrets management for sensitive data

### Cloud Platform Deployment

**Note:** These are general deployment patterns. Specific platform configurations may vary and
should be tested.

**Railway:**

1. Fork the Tux repository
2. Connect Railway to your GitHub account
3. Deploy from your forked repository
4. Configure environment variables in Railway dashboard
5. Add PostgreSQL plugin

**Heroku:**

1. Create new Heroku app
2. Add Heroku Postgres addon
3. Configure environment variables
4. Deploy using Git or GitHub integration

**DigitalOcean App Platform:**

1. Create new app from GitHub repository
2. Configure build and run commands
3. Add managed PostgreSQL database
4. Set environment variables

### VPS Deployment

**System Requirements:**

- Ubuntu 20.04+ or similar Linux distribution
- 1GB+ RAM (2GB+ recommended)
- Python 3.13+
- PostgreSQL 12+

**Installation Steps:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip postgresql postgresql-contrib git -y

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
nano .env

# Set up database
sudo -u postgres createdb tux
sudo -u postgres createuser tux
sudo -u postgres psql -c "ALTER USER tux PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tux TO tux;"

# Run database migrations
uv run db migrate-push

# Create systemd service
sudo nano /etc/systemd/system/tux.service
```

**Systemd Service Configuration:**

```ini
[Unit]
Description=Tux Discord Bot
After=network.target postgresql.service

[Service]
Type=simple
User=tux
WorkingDirectory=/home/tux/tux
Environment=PATH=/home/tux/tux/.venv/bin
ExecStart=/home/tux/tux/.venv/bin/python -m tux
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start Service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable tux
sudo systemctl start tux
sudo systemctl status tux
```

### Self-Hosting Considerations

**Security:**

- Use strong passwords for database
- Keep system and dependencies updated
- Configure firewall (UFW recommended)
- Use HTTPS for any web interfaces
- Regular security audits

**Backup Strategy:**

- Database backups (automated daily)
- Configuration file backups
- Log rotation and archival
- Disaster recovery plan

**Monitoring:**

- System resource monitoring
- Application health checks
- Error rate monitoring
- Performance metrics

## Configuration

### Environment Variables

**Required Variables:**

```bash
# Discord Configuration
DISCORD_TOKEN=<your_discord_token>

# Database Configuration  
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=secure_password

# Optional: Debug mode
DEBUG=true
```

**Optional Variables:**

```bash
# Error Tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Environment
ENVIRONMENT=production  # development, staging, production

# Performance
MAX_WORKERS=4
POOL_SIZE=20

# Features
ENABLE_METRICS=true
ENABLE_TRACING=false
```

### Database Configuration

**PostgreSQL Setup:**

```sql
-- Create database and user
CREATE DATABASE tux;
CREATE USER tux WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE tux TO tux;

-- Configure connection limits (optional)
ALTER USER tux CONNECTION LIMIT 20;
```

**Connection Pool Settings:**

```python
# In production, configure connection pooling
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30
```

**Database Maintenance:**

```bash
# Run migrations
uv run db migrate-push

# Check database health
uv run db health

# Backup database
pg_dump -h localhost -U tux tux > backup_$(date +%Y%m%d).sql

# Restore database
psql -h localhost -U tux tux < backup_20240101.sql
```

### Discord Bot Configuration

**Bot Permissions:**
Required permissions for full functionality:

- Read Messages/View Channels
- Send Messages
- Send Messages in Threads
- Embed Links
- Attach Files
- Read Message History
- Use External Emojis
- Add Reactions
- Manage Messages (for moderation)
- Kick Members (for moderation)
- Ban Members (for moderation)
- Moderate Members (for timeouts)
- Manage Roles (for jail system)

**OAuth2 Scopes:**

- `bot` - Basic bot functionality
- `applications.commands` - Slash commands

**Invite URL Template:**

```text
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=1099511627775&scope=bot%20applications.commands
```

### External Services

**Sentry (Error Tracking):**

1. Create Sentry project
2. Get DSN from project settings
3. Add `SENTRY_DSN` to environment variables
4. Configure error sampling rates

**Logging Services:**

- **Local Files**: Configure log rotation
- **Centralized Logging**: Use services like Papertrail, Loggly
- **ELK Stack**: For advanced log analysis

## Monitoring & Maintenance

### Health Checks

**Application Health:**

```bash
# Check bot status
uv run tux status

# Database connectivity
uv run db health

# System resources
htop
df -h
free -h
```

**Automated Health Checks:**

```bash
#!/bin/bash
# health_check.sh
if ! systemctl is-active --quiet tux; then
    echo "Tux service is down, restarting..."
    systemctl restart tux
    # Send alert notification
fi
```

### Logging

**Log Levels:**

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures

**Log Rotation:**

```bash
# /etc/logrotate.d/tux
/var/log/tux/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 tux tux
    postrotate
        systemctl reload tux
    endscript
}
```

### Performance Monitoring

**Key Metrics:**

- Response time for commands
- Database query performance
- Memory usage
- CPU utilization
- Error rates

**Monitoring Tools:**

- **System**: htop, iotop, netstat
- **Application**: Built-in metrics endpoint
- **Database**: PostgreSQL stats
- **External**: Grafana, Prometheus

### Backup & Recovery

**Database Backups:**

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U tux tux | gzip > /backups/tux_$DATE.sql.gz

# Keep only last 30 days
find /backups -name "tux_*.sql.gz" -mtime +30 -delete
```

**Configuration Backups:**

```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

**Recovery Procedures:**

1. Stop the application
2. Restore database from backup
3. Restore configuration files
4. Start application
5. Verify functionality

### Troubleshooting

**Common Issues:**

**Bot Won't Start:**

1. Check environment variables
2. Verify database connectivity
3. Check Discord token validity
4. Review application logs

**Database Connection Issues:**

1. Verify PostgreSQL is running
2. Check connection string format
3. Verify user permissions
4. Check network connectivity

**Permission Errors:**

1. Verify bot permissions in Discord
2. Check role hierarchy
3. Verify OAuth2 scopes
4. Re-invite bot if necessary

**Performance Issues:**

1. Check system resources
2. Analyze database query performance
3. Review error rates
4. Consider scaling options

**Log Analysis:**

```bash
# View recent errors
journalctl -u tux --since "1 hour ago" | grep ERROR

# Monitor real-time logs
journalctl -u tux -f

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Scaling Considerations

**Vertical Scaling:**

- Increase CPU and memory
- Optimize database configuration
- Tune connection pools

**Horizontal Scaling:**

- Multiple bot instances (sharding)
- Load balancing
- Distributed database setup

**Database Optimization:**

- Index optimization
- Query performance tuning
- Connection pooling
- Read replicas for analytics

## Security Best Practices

### Access Control

**System Security:**

- Use non-root user for bot process
- Configure firewall rules
- Regular security updates
- SSH key authentication only

**Application Security:**

- Secure environment variable storage
- Regular dependency updates
- Input validation and sanitization
- Rate limiting

### Data Protection

**Sensitive Data:**

- Encrypt database connections
- Secure backup storage
- Regular security audits
- GDPR compliance considerations

**Bot Token Security:**

- Never commit tokens to version control
- Use environment variables or secrets management
- Rotate tokens regularly
- Monitor for token leaks

This guide provides comprehensive information for deploying and maintaining Tux in production
environments. For development-specific information, see the Developer Guide.
