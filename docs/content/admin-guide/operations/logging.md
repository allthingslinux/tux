# Logging

Log management and configuration.

## Log Output

Tux uses **Loguru** for structured logging.

### Docker Compose

```bash
# View logs
docker compose logs -f tux

# Last 100 lines
docker compose logs --tail=100 tux

# Since timestamp
docker compose logs --since 2024-01-01T00:00:00 tux
```

### Systemd

```bash
# Follow logs
sudo journalctl -u tux -f

# Last hour
sudo journalctl -u tux --since "1 hour ago"

# Search for errors
sudo journalctl -u tux | grep ERROR
```

## Log Levels

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

## Log Rotation

Docker Compose includes log rotation by default:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
    compress: "true"
```

## Related

- **[Monitoring](monitoring.md)**
- **[Troubleshooting](troubleshooting.md)**

---

*Complete logging documentation in progress.*
