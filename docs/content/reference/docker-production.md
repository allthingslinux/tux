---
title: Docker Production Deployment
tags:
  - reference
  - docker
  - production
---

# Docker Production Deployment

Reference guide for deploying Tux in production using Docker.

## Production Compose File

For production deployments, use `compose.production.yaml` which:

- Removes development features (source code volume bindings, hot reload)
- Uses pre-built images from GitHub Container Registry (GHCR)
- Optimized for security and performance
- No Adminer service (optional via `dev` profile)

### Usage

```bash
# Deploy production configuration
docker compose -f compose.production.yaml up -d

# With specific image version
TUX_IMAGE=ghcr.io/allthingslinux/tux TUX_IMAGE_TAG=v1.0.0 \
  docker compose -f compose.production.yaml up -d

# Enable Adminer for debugging (if needed)
docker compose -f compose.production.yaml --profile dev up -d adminer
```

### Differences from Development

| Feature | Development (`compose.yaml`) | Production (`compose.production.yaml`) |
|---------|------------------------------|----------------------------------------|
| Source code bindings | ✅ Mounted from host | ❌ Included in image |
| Hot reload | ✅ Enabled with `watch` | ❌ Disabled |
| Build from source | ✅ Local build | ❌ Pre-built image |
| Adminer | ✅ Enabled by default | ❌ Disabled (optional) |
| Image source | Local build | GHCR registry |

## Using Pre-Built Images

Tux images are published to GitHub Container Registry:

```env
# Use official image
TUX_IMAGE=ghcr.io/allthingslinux/tux
TUX_IMAGE_TAG=latest

# Or use specific version
TUX_IMAGE_TAG=v1.0.0
```

### Pull and Verify

```bash
# Pull latest image
docker pull ghcr.io/allthingslinux/tux:latest

# Verify image
docker images ghcr.io/allthingslinux/tux

# Check image details
docker inspect ghcr.io/allthingslinux/tux:latest
```

## Advanced Configuration

### Custom Image Registry

```env
# Custom registry
TUX_IMAGE=my-registry.com/tux
TUX_IMAGE_TAG=v1.0.0

# Local build
TUX_IMAGE=tux:local
TUX_IMAGE_TAG=latest
```

### Development Overrides

```env
# Enable debug mode
DEBUG=true
LOG_LEVEL=DEBUG

# Use local migrations
USE_LOCAL_MIGRATIONS=true
```

### Startup Configuration

```env
# Maximum startup attempts
MAX_STARTUP_ATTEMPTS=5

# Delay between attempts (seconds)
STARTUP_DELAY=10
```

### Database Port Mapping

Expose PostgreSQL port to host:

```env
POSTGRES_PORT=5432
```

Access from host: `postgresql://tuxuser:password@localhost:5432/tuxdb`

### Disable Adminer

Comment out or remove the `tux-adminer` service in `compose.yaml`, or set:

```env
ADMINER_PORT=
```

## Security Features

Tux Docker images include several security best practices:

### Non-Root User

The container runs as `nonroot` user (UID/GID 1001):

```bash
# Verify user
docker compose exec tux whoami
# Output: nonroot

docker compose exec tux id
# Output: uid=1001(nonroot) gid=1001(nonroot)
```

### Read-Only Root Filesystem

The production image uses a read-only root filesystem with writable tmpfs mounts:

```yaml
read_only: true
tmpfs:
  - /tmp:size=100m
  - /var/tmp:size=50m
```

### Security Options

```yaml
security_opt:
  - no-new-privileges:true  # Prevents privilege escalation
```

### Minimal Base Image

Uses `python:3.13.8-slim` with:

- Minimal system packages
- Pinned base image digest for reproducibility
- Optimized for size and security
- Regular security updates

## Related Documentation

- **[Docker Installation](../selfhost/install/docker.md)** - Initial setup
- **[Docker Operations](../selfhost/manage/docker.md)** - Service management
- **[Building Docker Images](../developer/guides/docker-images.md)** - Custom image builds
