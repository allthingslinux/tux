# Docker Security Guide

This document outlines the security practices implemented in the Tux Docker setup.

## Security Features Implemented

### 🔒 **Container Security**

1. **Non-root User Execution**
   - All containers run as non-root user (UID 1001)
   - Explicit user creation with fixed UID/GID for consistency
   - Applied to both development and production stages

2. **Read-only Root Filesystem**
   - Production containers use read-only root filesystem
   - Temporary filesystems mounted for `/tmp` and `/var/tmp` for system temp files
   - Dedicated writable volume mounted at `/app/temp` for application temp files
   - Prevents runtime file system modifications outside designated areas

3. **Security Options**
   - `no-new-privileges:true` prevents privilege escalation
   - Containers cannot gain additional privileges at runtime

4. **Resource Limits**
   - Memory and CPU limits prevent resource exhaustion attacks
   - Different limits for development (1GB/1CPU) and production (512MB/0.5CPU)

### 🛡️ **Build Security**

1. **Multi-stage Builds**
   - Separate build and runtime stages
   - Build tools and dependencies not included in final image
   - Minimal attack surface in production

2. **Dependency Management**
   - Poetry with locked dependencies (`poetry.lock`)
   - Explicit package versions and integrity checks
   - No cache directories in final image

3. **Vulnerability Scanning**
   - Docker Scout integration in CI/CD
   - Automated scanning for critical/high vulnerabilities
   - Policy evaluation for security compliance

### 📦 **Image Security**

1. **Base Image**
   - Official Python slim image (regularly updated)
   - Minimal package installation with `--no-install-recommends`
   - Sorted package lists for maintainability

2. **Layer Optimization**
   - Combined RUN commands to reduce layers
   - Package cache cleanup in same layer
   - Efficient Dockerfile caching strategy

## Environment-Specific Configurations

### Development (`docker-compose.dev.yml`)

- Higher resource limits for development tools
- Volume mounts for live code reloading
- Non-root user still enforced for security

### Production (`docker-compose.yml`)

- Strict resource limits
- Read-only volume mounts for config/assets
- Writable volumes for cache and temporary files
- Health checks for monitoring
- Named volumes for data persistence

## Security Checklist

- [ ] Environment variables via `.env` file (never in Dockerfile)
- [ ] Regular base image updates
- [ ] Vulnerability scanning in CI/CD
- [ ] Non-root user execution
- [ ] Read-only root filesystem
- [ ] Resource limits configured
- [ ] Health checks implemented
- [ ] Minimal package installation

## Monitoring and Alerts

1. **Health Checks**
   - Basic Python import test
   - 30-second intervals with 3 retries
   - 40-second startup grace period

2. **Logging**
   - JSON structured logging
   - Log rotation (10MB max, 3 files)
   - No sensitive data in logs

## File System Access

### Temporary File Handling

For Discord bot eval scripts and temporary file operations:

1. **Application Temp Directory**
   - Use `/app/temp` for application-specific temporary files
   - Mounted as named volume with proper ownership (nonroot:nonroot)
   - Survives container restarts but isolated per environment

2. **System Temp Directories**
   - `/tmp` and `/var/tmp` available as tmpfs (in-memory)
   - Cleared on container restart
   - Use for short-lived temporary files

3. **Security Considerations**
   - Temp files are writable but execution is not restricted (needed for eval)
   - Named volumes provide isolation between environments
   - Monitor temp directory size to prevent disk exhaustion

### Recommended Usage Pattern

```python
import tempfile
import os

# For persistent temp files (across container restarts)
TEMP_DIR = "/app/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# For ephemeral temp files (cleared on restart)
with tempfile.NamedTemporaryFile(dir="/tmp") as tmp_file:
    # Use tmp_file for short-lived operations
    pass
```

## Best Practices

1. **Secrets Management**
   - Use Docker secrets or external secret management
   - Never embed secrets in images
   - Use `.env` files for local development only

2. **Network Security**
   - Use Docker networks for service communication
   - Expose only necessary ports
   - Consider using reverse proxy for production

3. **Updates and Maintenance**
   - Regular base image updates
   - Automated vulnerability scanning
   - Monitor security advisories for dependencies

## Compliance

This setup follows:

- Docker security best practices
- CIS Docker Benchmark recommendations
- OWASP Container Security guidelines
- Production security standards

## Emergency Procedures

1. **Security Incident Response**
   - Stop affected containers immediately
   - Preserve logs for analysis
   - Update and rebuild images
   - Review access logs

2. **Vulnerability Response**
   - Assess vulnerability impact
   - Update affected dependencies
   - Rebuild and redeploy images
   - Document remediation steps
