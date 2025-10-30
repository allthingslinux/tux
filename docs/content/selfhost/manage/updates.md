# Updates

Keep your Tux installation up to date with the latest features and security patches.

## Update Methods

### Docker Updates

#### Using Docker Compose

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

#### Using Docker Images

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

### Bare Metal Updates

#### Manual Update

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

#### Automated Update Script

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

## Update Types

### Minor Updates

- Bug fixes
- Performance improvements
- New features
- Usually safe to update immediately

### Major Updates

- Breaking changes
- Database schema changes
- Configuration changes
- Review changelog before updating

### Security Updates

- Critical security patches
- Update immediately
- May require immediate restart

## Pre-Update Checklist

### Backup

- [ ] Database backup
- [ ] Configuration files
- [ ] Custom modifications
- [ ] Bot data

### Testing

- [ ] Test in development environment
- [ ] Verify compatibility
- [ ] Check breaking changes
- [ ] Review migration notes

### Preparation

- [ ] Schedule maintenance window
- [ ] Notify users
- [ ] Prepare rollback plan
- [ ] Monitor system resources

## Database Migrations

### Automatic Migrations

```bash
# Run migrations automatically
tux db migrate
```

### Manual Migrations

```bash
# Check migration status
tux db status

# Apply specific migration
tux db migrate --version 20231201_001

# Rollback migration
tux db rollback --version 20231201_001
```

## Rollback Procedures

### Docker Rollback

```bash
# Stop current container
docker-compose down

# Restore previous image
docker tag tux:previous tux:latest

# Start with previous version
docker-compose up -d
```

### Bare Metal Rollback

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

## Update Monitoring

### Health Checks

```bash
# Check bot status
tux status

# Check logs
tux logs --tail 100

# Test commands
tux test-commands
```

### Monitoring Commands

```bash
# Monitor resource usage
htop

# Check disk space
df -h

# Monitor logs
tail -f /var/log/tux/tux.log
```

## Troubleshooting Updates

### Common Issues

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

## Update Schedule

### Recommended Schedule

- **Security updates**: Immediate
- **Minor updates**: Weekly
- **Major updates**: Monthly
- **Maintenance**: Quarterly

### Notification Setup

- Subscribe to release notifications
- Monitor GitHub releases
- Set up automated alerts
- Join community channels

## Next Steps

After updating:

- [Monitoring Setup](monitoring.md) - Monitor update success
- [Performance Tuning](performance.md) - Optimize after updates
- [Backup Verification](backups.md) - Verify backup procedures
- [Security Review](security.md) - Review security implications
