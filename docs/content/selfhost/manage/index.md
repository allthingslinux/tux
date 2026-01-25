---
title: Self-Host Management
tags:
  - selfhost
  - operations
icon: lucide/sliders-horizontal
---

# Self-Host Management

Essential information for ongoing maintenance and operations of your Tux self-hosted instance.

## Management Guides

### [Database Management](database.md)

Comprehensive guide for managing your Tux database:

- **Backups** - Manual and automated backup strategies
- **Migrations** - Managing database schema changes
- **Troubleshooting** - Fixing migration and sequence issues
- **Adminer** - Web-based database administration
- **Sequence Fixes** - Fixing PostgreSQL sequence synchronization

### [Docker Operations](docker.md)

Detailed guide for managing Docker containers:

- **Service Management** - Start, stop, restart services
- **Log Management** - Viewing and filtering logs
- **Backups** - Database backup procedures
- **Updates** - Updating containers and images
- **Troubleshooting** - Common Docker issues

### [System Operations](operations.md)

Monitor, maintain, and optimize your Tux installation:

- **Monitoring** - Health checks and metrics
- **Performance** - Optimization strategies
- **Logging** - Log management and configuration
- **Updates** - Update procedures and rollback
- **Security** - Security best practices

## Quick Reference

### Health Checks

```bash
# Database health
uv run db health

# Bot status (Docker)
docker compose ps tux

# Bot status (systemd)
sudo systemctl status tux
```

### Common Tasks

```bash
# View logs
docker compose logs -f tux          # Docker
sudo journalctl -u tux -f          # systemd

# Restart services
docker compose restart tux          # Docker
sudo systemctl restart tux          # systemd

# Database backup
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup.sql

# Fix sequences
uv run db fix-sequences
```

## Related Documentation

- [Installation Guides](../install/index.md) - Installation instructions
- [Configuration Guide](../config/index.md) - Configuration reference
- [Troubleshooting](../../support/troubleshooting/selfhost.md) - Common issues and solutions
