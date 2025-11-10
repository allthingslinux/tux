---
title: System Requirements
---

# System Requirements

Before installing Tux, ensure your system meets these requirements.

## Minimum Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **RAM**: 512MB
- **Storage**: 1GB free space
- **CPU**: 1 core

## Recommended Requirements

- **OS**: Linux (Ubuntu 22.04+, Debian 12+)
- **RAM**: 2GB+
- **Storage**: 5GB+ free space
- **CPU**: 2+ cores

## Software Dependencies

### Required

- **Python**: 3.11 or higher
- **Git**: For cloning the repository
- **Docker**: For containerized deployment (optional)

### Database

- **PostgreSQL**: 13+ (required)

## Network Requirements

- **Outbound HTTPS**: For Discord API communication
- **Port Access**: Configure firewall for your chosen deployment method

## Discord Bot Requirements

- **Bot Token**: From Discord Developer Portal
- **Permissions**: Administrator or specific permissions as needed
- **Server Access**: Bot must be invited to target servers

## Next Steps

After verifying requirements:

- [Docker Installation](docker.md) - Recommended for production
- [System Installation](systemd.md) - For non-Docker setups
- [First Run Setup](first-run.md) - First run
