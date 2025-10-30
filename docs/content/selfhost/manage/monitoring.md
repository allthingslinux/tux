# Monitoring

Monitor Tux health and performance.

## Health Checks

### Bot Status

```bash
# Check if running
docker compose ps tux

# Check health status  
docker inspect tux --format='{{.State.Health.Status}}'
```

### Database Health

```bash
# Via CLI
docker compose exec tux uv run db health

# Direct check
docker compose exec tux-postgres pg_isready -U tuxuser
```

### Discord Connection

Check bot shows online in Discord.

## Metrics

### Resource Usage

```bash
# Docker stats
docker stats tux tux-postgres

# System resources
htop
free -h
df -h
```

### Bot Metrics

```
/ping                               # API latency, uptime, resources
```

## Alerting

Set up alerts for:

- Bot offline
- High error rate
- Database connection issues
- Resource exhaustion

## Optional: Sentry

Configure Sentry for automatic error tracking:

```bash
EXTERNAL_SERVICES__SENTRY_DSN=your_dsn
```

## Optional: InfluxDB

Time-series metrics:

```bash
EXTERNAL_SERVICES__INFLUXDB_URL=http://influxdb:8086
EXTERNAL_SERVICES__INFLUXDB_TOKEN=token
EXTERNAL_SERVICES__INFLUXDB_ORG=org
```

## Related

- **[Logging](logging.md)**
- **[Performance](performance.md)**
- **[Troubleshooting](troubleshooting.md)**

---

*Complete monitoring guide in progress.*
