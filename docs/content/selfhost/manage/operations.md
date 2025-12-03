---
title: System Operations
tags:
  - selfhost
  - operations
---

# System Operations

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Monitor, maintain, and optimize your Tux installation.

## Monitoring

Monitor Tux health and performance.

### Health Checks

#### Bot Status

```bash
# Check if running
docker compose ps tux

# Check health status
docker inspect tux --format='{{.State.Health.Status}}'
```

#### Database Health

```bash
# Via CLI
docker compose exec tux uv run db health

# Direct check
docker compose exec tux-postgres pg_isready -U tuxuser
```

#### Discord Connection

Check bot shows online in Discord.

### Metrics

#### Resource Usage

```bash
# Docker stats
docker stats tux tux-postgres

# System resources
htop
free -h
df -h
```

#### Bot Metrics

```text
/ping                               # API latency, uptime, resources
```

### Alerting

Set up alerts for:

- Bot offline
- High error rate
- Database connection issues
- Resource exhaustion

### Optional: Sentry

Configure Sentry for automatic error tracking:

```bash
EXTERNAL_SERVICES__SENTRY_DSN=your_dsn
```

### Optional: InfluxDB

Time-series metrics:

```bash
EXTERNAL_SERVICES__INFLUXDB_URL=http://influxdb:8086
EXTERNAL_SERVICES__INFLUXDB_TOKEN=token
EXTERNAL_SERVICES__INFLUXDB_ORG=org
```

## Performance Optimization

Optimize Tux for your server size.

### Database Optimization

#### PostgreSQL Tuning

Edit postgresql.conf:

```conf
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 1GB          # 50% of RAM
work_mem = 16MB
```

#### Connection Pooling

Configure pool size based on load:

```bash
# For small servers
POSTGRES_MAX_CONNECTIONS=20

# For large servers
POSTGRES_MAX_CONNECTIONS=50
```

### Bot Optimization

#### Resource Limits

In compose.yaml:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

### Monitoring Performance

```bash
# Resource usage
docker stats tux

# Database performance
uv run db queries
```

### Scaling

For large servers (1000+ members):

- Dedicated database server
- Increase connection pool
- Monitor and optimize queries
- Consider caching strategies

## Logging

Log management and configuration.

### Log Output

Tux uses **Loguru** for structured logging.

#### Docker Compose

```bash
# View logs
docker compose logs -f tux

# Last 100 lines
docker compose logs --tail=100 tux

# Since timestamp
docker compose logs --since 2024-01-01T00:00:00 tux
```

#### Systemd

```bash
# Follow logs
sudo journalctl -u tux -f

# Last hour
sudo journalctl -u tux --since "1 hour ago"

# Search for errors
sudo journalctl -u tux | grep ERROR
```

### Log Levels

Configure via `DEBUG` environment variable:

```bash
DEBUG=false                         # INFO level (production)
DEBUG=true                          # DEBUG level (development)
```

**Levels:**

- DEBUG - Detailed diagnostic info
- INFO - General operational messages
- WARNING - Warning messages
- ERROR - Error messages
- CRITICAL - Critical failures

### Log Rotation

Docker Compose includes log rotation by default:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
    compress: "true"
```

## Updates

Keep your Tux installation up to date with the latest features and security patches.

### Update Methods

#### Docker Updates

##### Using Docker Compose

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

##### Using Docker Images

```bash
# Pull latest image
docker pull tux:latest

# Stop current container
docker stop tux

# Remove old container
docker rm tux

# Start new container
docker run -d --name tux tux:latest
```

#### Bare Metal Updates

##### Manual Update

```bash
# Stop the bot
sudo systemctl stop tux

# Backup current installation
cp -r /opt/tux /opt/tux.backup.$(date +%Y%m%d)

# Pull latest changes
cd /opt/tux
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -e .

# Run database migrations
tux db migrate

# Start the bot
sudo systemctl start tux
```

##### Automated Update Script

```bash
#!/bin/bash
# update-tux.sh

set -e

echo "Stopping Tux..."
sudo systemctl stop tux

echo "Backing up current installation..."
sudo cp -r /opt/tux /opt/tux.backup.$(date +%Y%m%d)

echo "Updating Tux..."
cd /opt/tux
sudo -u tux git pull origin main

echo "Updating dependencies..."
sudo -u tux bash -c "source venv/bin/activate && pip install -e ."

echo "Running database migrations..."
sudo -u tux bash -c "source venv/bin/activate && tux db migrate"

echo "Starting Tux..."
sudo systemctl start tux

echo "Update complete!"
```

### Update Types

#### Minor Updates

- Bug fixes
- Performance improvements
- New features
- Usually safe to update immediately

#### Major Updates

- Breaking changes
- Database schema changes
- Configuration changes
- Review changelog before updating

#### Security Updates

- Critical security patches
- Update immediately
- May require immediate restart

### Pre-Update Checklist

#### Backup

- [ ] Database backup
- [ ] Configuration files
- [ ] Custom modifications
- [ ] Bot data

#### Testing

- [ ] Test in development environment
- [ ] Verify compatibility
- [ ] Check breaking changes
- [ ] Review migration notes

#### Preparation

- [ ] Schedule maintenance window
- [ ] Notify users
- [ ] Prepare rollback plan
- [ ] Monitor system resources

### Database Migrations

#### Automatic Migrations

```bash
# Run migrations automatically
tux db migrate
```

#### Manual Migrations

```bash
# Check migration status
tux db status

# Apply specific migration
tux db migrate --version 20231201_001

# Rollback migration
tux db rollback --version 20231201_001
```

### Rollback Procedures

#### Docker Rollback

```bash
# Stop current container
docker-compose down

# Restore previous image
docker tag tux:previous tux:latest

# Start with previous version
docker-compose up -d
```

#### Bare Metal Rollback

```bash
# Stop bot
sudo systemctl stop tux

# Restore backup
sudo rm -rf /opt/tux
sudo mv /opt/tux.backup.20231201 /opt/tux

# Restore database (if needed)
sudo -u postgres psql tux < backup.sql

# Start bot
sudo systemctl start tux
```

### Update Monitoring

#### Health Checking

```bash
# Check bot status
tux status

# Check logs
tux logs --tail 100

# Test commands
tux test-commands
```

#### Monitoring Commands

```bash
# Monitor resource usage
htop

# Check disk space
df -h

# Monitor logs
tail -f /var/log/tux/tux.log
```

### Troubleshooting Updates

#### Common Issues

**Bot won't start after update**:

- Check logs for errors
- Verify configuration compatibility
- Check database migrations
- Restore from backup if needed

**Database migration errors**:

- Check database connectivity
- Verify migration files
- Manual migration if needed
- Contact support for complex issues

**Performance issues**:

- Monitor resource usage
- Check for memory leaks
- Review configuration changes
- Consider rollback

### Update Schedule

#### Recommended Schedule

- **Security updates**: Immediate
- **Minor updates**: Weekly
- **Major updates**: Monthly
- **Maintenance**: Quarterly

#### Notification Setup

- Subscribe to release notifications
- Monitor GitHub releases
- Set up automated alerts
- Join community channels

## Security

Security considerations for your Tux installation.

*Security documentation in progress. Basic recommendations:*

- Keep dependencies updated
- Use strong passwords
- Limit database access
- Monitor for unusual activity
- Regular security audits

## Related

- **[Database Management](database.md)**

---

*Complete system operations guide consolidated from individual topic files.*
