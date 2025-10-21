# PostgreSQL Setup

PostgreSQL configuration and optimization for Tux.

## Initial Setup

See **[Database Setup](../setup/database.md)** for initial installation.

## Configuration

### postgresql.conf

Tux includes optimized PostgreSQL configuration at `docker/postgres/postgresql.conf`.

**For Docker:**  
Configuration is automatically applied.

**For Manual Installation:**  
Edit `/etc/postgresql/15/main/postgresql.conf`

## Performance Tuning

Based on your server resources:

```conf
# Memory (adjust based on available RAM)
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 1GB          # 50-75% of RAM
work_mem = 16MB                     # Per operation
maintenance_work_mem = 128MB        # For VACUUM, CREATE INDEX

# Connections
max_connections = 100               # Adjust based on needs

# SSD Optimization
random_page_cost = 1.1
effective_io_concurrency = 200

# Write-Ahead Log
wal_buffers = 16MB
```

## Monitoring

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Database size
SELECT pg_size_pretty(pg_database_size('tuxdb'));
```

## Related

- **[Database Setup](../setup/database.md)**
- **[Migrations](migrations.md)**
- **[Backups](backups.md)**

---

*Full PostgreSQL optimization guide in progress.*
