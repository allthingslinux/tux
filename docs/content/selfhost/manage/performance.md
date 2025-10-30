# Performance Optimization

Optimize Tux for your server size.

## Database Optimization

### PostgreSQL Tuning

Edit postgresql.conf:

```conf
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 1GB          # 50% of RAM
work_mem = 16MB
```

### Connection Pooling

Configure pool size based on load:

```bash
# For small servers
POSTGRES_MAX_CONNECTIONS=20

# For large servers
POSTGRES_MAX_CONNECTIONS=50
```

## Bot Optimization

### Resource Limits

In compose.yaml:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## Monitoring

```bash
# Resource usage
docker stats tux

# Database performance
uv run db queries
```

## Scaling

For large servers (1000+ members):

- Dedicated database server
- Increase connection pool
- Monitor and optimize queries
- Consider caching strategies

## Related

- **[Monitoring](monitoring.md)**
- **[PostgreSQL Setup](../database/postgres-setup.md)**

---

*Complete optimization guide in progress.*
