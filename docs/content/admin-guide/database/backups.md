# Database Backups

Protect your data with regular backups.

## Backup Strategies

### Manual Backup

```bash
# Docker Compose
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup_$(date +%Y%m%d).sql

# With compression
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb | gzip > backup_$(date +%Y%m%d).sql.gz

# Local PostgreSQL
pg_dump -h localhost -U tuxuser tuxdb > backup.sql
```

### Automated Backups

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb | gzip > "$BACKUP_DIR/tux_$DATE.sql.gz"

# Keep only last 30 days
find "$BACKUP_DIR" -name "tux_*.sql.gz" -mtime +30 -delete

# Optional: Upload to cloud storage
# rclone copy "$BACKUP_DIR/tux_$DATE.sql.gz" remote:backups/
```

**Add to cron:**

```bash
# Daily at 2 AM
0 2 * * * /path/to/backup.sh
```

## Restore

```bash
# From SQL file
docker compose exec -T tux-postgres psql -U tuxuser tuxdb < backup.sql

# From gzip
gunzip < backup.sql.gz | docker compose exec -T tux-postgres psql -U tuxuser tuxdb

# Or
docker compose exec tux-postgres psql -U tuxuser tuxdb < backup.sql
```

## Best Practices

- Backup daily (minimum)
- Test restore procedures regularly
- Store backups off-site
- Encrypt sensitive backups
- Keep multiple backup generations
- Document restore process

## Related

- **[Database Setup](../setup/database.md)**
- **[Operations](../operations/monitoring.md)**

---

*Complete backup strategy documentation in progress.*
