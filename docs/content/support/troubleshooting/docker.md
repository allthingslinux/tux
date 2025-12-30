---
title: Docker Troubleshooting
tags:
  - support
  - troubleshooting
  - docker
---

# Docker Troubleshooting

Common issues and solutions when running Tux with Docker.

## Bot Not Starting

### Check Logs

```bash
docker compose logs tux
```

### Common Causes

- Invalid `BOT_TOKEN` - Verify token is correct
- Database not ready - Wait for PostgreSQL health check
- Missing environment variables - Check `.env` file

### Verify Configuration

```bash
# Check environment variables are loaded
docker compose exec tux env | grep BOT_TOKEN

# Test database connection
docker compose exec tux uv run db health
```

## Database Connection Errors

### Check PostgreSQL is Running

```bash
docker compose ps tux-postgres
```

### Verify Connection

```bash
# Test PostgreSQL connection
docker compose exec tux-postgres pg_isready -U tuxuser

# Check database exists
docker compose exec tux-postgres psql -U tuxuser -d tuxdb -c "SELECT version();"
```

### Check Environment Variables

```bash
# Verify database credentials
docker compose exec tux env | grep POSTGRES
```

## Container Keeps Restarting

### Check Restart Reason

```bash
docker compose ps
docker compose logs tux --tail=50
```

### Common Issues

- Health check failing - Check bot token is set
- Database connection timeout - Verify PostgreSQL is healthy
- Configuration errors - Check `.env` file syntax

## Permission Errors

### Fix Volume Permissions

```bash
# Ensure files are readable
chmod -R 755 config assets src/tux/plugins
chmod 644 .env
```

### Check Container User

```bash
docker compose exec tux whoami
# Should show: nonroot

docker compose exec tux id
# Should show: uid=1001(nonroot) gid=1001(nonroot)
```

## Health Check Failures

### Manual Health Check

```bash
docker compose exec tux python -c "from tux.shared.config import CONFIG; print('Token set:', bool(CONFIG.BOT_TOKEN))"
```

### Check Health Status

```bash
docker inspect tux --format='{{json .State.Health}}' | jq
```

## View Container Resources

```bash
# Resource usage
docker stats tux tux-postgres

# Container details
docker compose exec tux ps aux
docker compose exec tux df -h
```

## Image Build Issues

### Build Fails with Permission Errors

```bash
# Check Docker context
docker build --no-cache -f Containerfile --target production -t tux:test . 2>&1 | grep -i "permission\|denied"
```

### Build Context Too Large

Check `.dockerignore` excludes unnecessary files:

```bash
# Verify .dockerignore
cat .dockerignore

# Test build context size (observe the "Sending build context" output when starting a build)
docker build -f Containerfile --target production . 2>&1 | head -5 | grep -E "Sending|context"
```

## Container Startup Issues

### Container Exits Immediately

```bash
# Check exit code
docker compose ps -a

# View exit logs
docker compose logs tux

# Run interactively to debug
docker compose run --rm tux sh
```

### Database Connection Timeout

The entrypoint script waits up to 60 seconds for PostgreSQL. If timeout occurs:

```bash
# Check PostgreSQL is healthy
docker compose ps tux-postgres

# Check network connectivity
docker compose exec tux ping -c 3 tux-postgres

# Verify environment variables
docker compose exec tux env | grep POSTGRES
```

## Related Documentation

- **[Docker Installation](../../selfhost/install/docker.md)** - Installation guide
- **[Docker Operations](../../selfhost/manage/docker.md)** - Service management
- **[Building Docker Images](../../developer/guides/docker-images.md)** - Image building guide
