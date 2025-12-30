---
title: Building Docker Images
tags:
  - developer
  - docker
  - guides
---

# Building Docker Images

Guide for building, optimizing, and customizing Tux Docker images.

## Building Images Locally

For development or custom builds:

```bash
# Build production image
docker build -f Containerfile --target production -t tux:local .

# Build development image (with dev dependencies)
docker build -f Containerfile --target dev -t tux:dev .

# Build with version info
docker build -f Containerfile --target production \
  --build-arg VERSION=v1.0.0 \
  --build-arg GIT_SHA=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  -t tux:local .

# Test the image
docker run --rm tux:local --help
```

## Build Stages

The Containerfile uses multi-stage builds:

- `common` - Shared base setup (labels, user, env vars)
- `base` - Common + build dependencies
- `build` - Application build and dependency installation
- `dev` - Development stage with dev dependencies
- `production` - Optimized production image (~400MB)

## Image Optimization

### Image Size

The production image is optimized for size (~400MB):

- Multi-stage builds to exclude build dependencies
- Dependency group exclusion (dev, test, docs, types)
- Removed unnecessary files (tests, documentation, cache)
- Compiled Python bytecode for faster startup

**Verify image size:**

```bash
docker images tux --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

### Build Optimization Tips

#### 1. Use BuildKit Cache

```bash
DOCKER_BUILDKIT=1 docker build -f Containerfile --target production -t tux:local .
```

#### 2. Multi-Platform Builds

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Containerfile --target production \
  -t tux:multiarch .
```

#### 3. Layer Caching

Dependencies are cached separately from source code, so dependency changes don't invalidate the entire build.

### Image Inspection

**Analyze image layers:**

```bash
# Using dive (install: https://github.com/wagoodman/dive)
dive tux:latest

# Using docker history
docker history tux:latest --human --format "table {{.CreatedBy}}\t{{.Size}}"
```

**Check image contents:**

```bash
# Explore filesystem
docker run --rm -it tux:latest sh

# Check installed packages
docker run --rm tux:latest uv pip list

# Verify security
docker scout cves tux:latest
```

## Build Troubleshooting

### Image Build Issues

**Build fails with permission errors:**

```bash
# Check Docker context
docker build --no-cache -f Containerfile --target production -t tux:test . 2>&1 | grep -i "permission\|denied"
```

**Build context too large:**

Check `.dockerignore` excludes unnecessary files:

```bash
# Verify .dockerignore
cat .dockerignore

# Test build context size (observe the "Sending build context" output when starting a build)
docker build -f Containerfile --target production . 2>&1 | head -5 | grep -E "Sending|context"
```

### Container Startup Issues

**Container exits immediately:**

```bash
# Check exit code
docker compose ps -a

# View exit logs
docker compose logs tux

# Run interactively to debug
docker compose run --rm tux sh
```

**Database connection timeout:**

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
- **[Production Deployment](../../reference/docker-production.md)** - Production deployment
- **[Docker Troubleshooting](../../support/troubleshooting/docker.md)** - Common issues
