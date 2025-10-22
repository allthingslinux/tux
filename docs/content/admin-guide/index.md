# Admin Guide

Welcome to the Tux Administration Guide! This section covers everything you need to deploy, configure, and operate your own Tux instance.

## Who Is This For?

This guide is for:

- **Self-hosters** running their own Tux instance
- **System administrators** deploying Tux for their community
- **DevOps engineers** managing Tux in production
- **Server administrators** configuring advanced settings

If you're just using Tux in a server, see the **[User Guide](../user-guide/index.md)** instead.

## Quick Navigation

### 🚀 Deployment

Choose your deployment method:

- **[Docker Compose](deployment/docker-compose.md)** - **Recommended** for most users
- **[VPS with Systemd](deployment/systemd-vps.md)** - Bare metal deployment
- **[Cloud Platforms](deployment/cloud-platforms.md)** - Railway, DigitalOcean, etc.

### ⚙️ Setup

Initial setup guides:

- **[Discord Bot Token](setup/discord-bot-token.md)** - Create your Discord application
- **[Database Setup](setup/database.md)** - Configure PostgreSQL
- **[Environment Variables](setup/environment-variables.md)** - Configure `.env`
- **[Config Files](setup/config-files.md)** - TOML/YAML/JSON configuration
- **[First Run](setup/first-run.md)** - Starting Tux for the first time

### 🔧 Configuration

Configure your instance:

- **[Configuration Overview](configuration/index.md)** - Understanding the config system
- **[Bot Settings](configuration/bot-settings.md)** - Prefix, activity, presence
- **[Guild Setup](configuration/guild-setup.md)** - Per-server configuration
- **[Permissions](configuration/permissions.md)** - Set up permission ranks
- **[Features](configuration/features.md)** - Enable/disable features
- **[Advanced](configuration/advanced.md)** - Sentry, InfluxDB, plugins

### 🗄️ Database

Manage your database:

- **[PostgreSQL Setup](database/postgres-setup.md)** - Database configuration
- **[Migrations](database/migrations.md)** - Running and managing migrations
- **[Backups](database/backups.md)** - Backup strategies
- **[Adminer](database/adminer.md)** - Web UI for database management

### 🔍 Operations

Day-to-day operations:

- **[Logging](operations/logging.md)** - Log management and rotation
- **[Monitoring](operations/monitoring.md)** - Health checks and metrics
- **[Updating](operations/updating.md)** - Keep Tux up to date
- **[Troubleshooting](operations/troubleshooting.md)** - Common issues and solutions
- **[Performance](operations/performance.md)** - Optimization and scaling

### 🔒 Security

Secure your deployment:

- **[Best Practices](security/best-practices.md)** - Security hardening
- **[Token Security](security/token-security.md)** - Protecting sensitive data
- **[Firewall](security/firewall.md)** - Network security

## Quick Start

New to self-hosting? Start here:

### 1. Choose Deployment Method

**[Docker Compose](deployment/docker-compose.md)** (Recommended)

- Easiest to set up
- Includes PostgreSQL and Adminer
- Automatic updates
- Works on Linux, macOS, Windows

**[VPS Deployment](deployment/systemd-vps.md)**

- Full control
- Better for production
- Requires Linux knowledge

### 2. Get Prerequisites

- Discord bot application
- PostgreSQL database
- Server or cloud instance

### 3. Deploy

Follow the deployment guide for your chosen method.

### 4. Configure

Set up your instance with environment variables and config files.

### 5. Start Using

Invite Tux to your server and run `/config wizard`.

## Common Admin Tasks

### Updating Tux

```bash
# Docker Compose
git pull
docker compose up -d --build
docker compose exec tux uv run db push

# Systemd
git pull
uv sync
uv run db push
sudo systemctl restart tux
```

**[Full Update Guide →](operations/updating.md)**

### Viewing Logs

```bash
# Docker Compose
docker compose logs -f tux

# Systemd
journalctl -u tux -f
```

**[Logging Guide →](operations/logging.md)**

### Database Backups

```bash
# Create backup
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup.sql

# Restore backup
docker compose exec -T tux-postgres psql -U tuxuser tuxdb < backup.sql
```

**[Backup Guide →](database/backups.md)**

### Checking Health

```bash
# Check bot status
docker compose ps

# Check database
docker compose exec tux uv run db health

# View metrics (if configured)
curl http://localhost:9090/metrics
```

**[Monitoring Guide →](operations/monitoring.md)**

## Configuration Overview

Tux supports multiple configuration sources with priority:

1. **Environment Variables** (highest priority)
2. **Config File** (TOML/YAML/JSON)
3. **Default Values** (lowest priority)

### Environment Variables (`.env`)

Required settings:

```bash
# Discord
BOT_TOKEN=your_token_here

# Database
POSTGRES_HOST=tux-postgres
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=secure_password

# Environment
ENVIRONMENT=production
DEBUG=false
```

**[Full Reference →](setup/environment-variables.md)**

### Config File (`config/config.toml`)

Optional but recommended:

```toml
[bot_info]
prefix = "$"
activity = "with Linux"

[features]
xp_enabled = true
starboard_enabled = true
```

**[Config File Guide →](setup/config-files.md)**

## System Requirements

### Minimum Requirements

- **CPU**: 1 core
- **RAM**: 512 MB
- **Storage**: 2 GB
- **OS**: Linux, macOS, or Windows (with Docker)
- **Database**: PostgreSQL 12+
- **Python**: 3.13+ (if not using Docker)

### Recommended for Production

- **CPU**: 2+ cores
- **RAM**: 2 GB
- **Storage**: 10 GB (with backups)
- **OS**: Linux (Ubuntu 22.04+ or Debian 12+)
- **Database**: PostgreSQL 15+ (managed service recommended)
- **Network**: Static IP or domain name

### For Large Servers (1000+ members)

- **CPU**: 4+ cores
- **RAM**: 4+ GB
- **Storage**: 20+ GB
- **Database**: Dedicated PostgreSQL instance
- **Network**: CDN for media (if applicable)
- **Monitoring**: Sentry, Grafana, Prometheus

## Architecture Overview

Tux consists of:

- **Bot Process**: Main Discord bot (Python)
- **Database**: PostgreSQL for persistent data
- **Cache**: In-memory caching (optional Redis)
- **Logs**: Structured logging with Loguru
- **Monitoring**: Optional Sentry for errors
- **Metrics**: Optional InfluxDB for performance

```text
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Discord   │◄────►│  Tux Bot     │◄────►│ PostgreSQL  │
│     API     │      │  (Python)    │      │  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Sentry     │
                     │  (Optional)  │
                     └──────────────┘
```

## Deployment Comparison

| Feature               | Docker Compose | VPS/Systemd | Cloud Platform |
|-----------------------|----------------|-------------|----------------|
| **Ease of Setup**     | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Control**           | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cost**              | Free (if you have server) | Free to low | Low to medium |
| **Maintenance**       | Low | Medium | Very low |
| **Scalability**       | Good | Excellent | Excellent |
| **Recommended For**   | Most users | Advanced users | Quick start |

**[Detailed Comparison →](deployment/index.md)**

## Security Checklist

Before going to production:

- [ ] Use strong database password
- [ ] Enable firewall (UFW or similar)
- [ ] Set up SSL/TLS for web interfaces
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Use `.env` file with 600 permissions
- [ ] Never commit secrets to version control
- [ ] Enable Sentry for error monitoring
- [ ] Configure rate limiting (if public)
- [ ] Set up monitoring and alerts
- [ ] Document your setup
- [ ] Test disaster recovery process

**[Security Guide →](security/best-practices.md)**

## Monitoring & Alerts

### What to Monitor

- **Bot uptime** - Is the bot running?
- **Discord connection** - Connected to Discord API?
- **Database health** - Can connect to database?
- **Error rates** - Are there unusual errors?
- **Resource usage** - CPU, RAM, disk
- **Response times** - Command latency

### Recommended Tools

- **[Sentry](https://sentry.io)** - Error tracking and performance
- **[UptimeRobot](https://uptimerobot.com)** - Uptime monitoring (free tier)
- **Grafana + Prometheus** - Advanced metrics (optional)
- **InfluxDB** - Time-series metrics (optional)

**[Monitoring Guide →](operations/monitoring.md)**

## Getting Help

### Documentation

- **Deployment**: Choose your method above
- **Configuration**: See configuration section
- **Operations**: Day-to-day management guides
- **Troubleshooting**: Common issues and solutions

### Community Support

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask in #self-hosting
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/allthingslinux/tux/discussions)** - General questions

### Emergency Support

For critical issues:

1. Check **[Troubleshooting Guide](operations/troubleshooting.md)**
2. Search **[GitHub Issues](https://github.com/allthingslinux/tux/issues)**
3. Ask in **[Discord #support](https://discord.gg/gpmSjcjQxg)**
4. Check **[System Status](https://github.com/allthingslinux/tux)**

## What's Next?

### New Self-Hosters

1. **[Choose Deployment Method](deployment/index.md)** - Docker, VPS, or cloud
2. **[Follow Setup Guide](setup/discord-bot-token.md)** - Get Discord token and database
3. **[Deploy Tux](deployment/docker-compose.md)** - Start your instance
4. **[Configure](configuration/index.md)** - Set up your preferences

### Existing Deployments

- **[Update Tux](operations/updating.md)** - Keep up to date
- **[Optimize Performance](operations/performance.md)** - Tune for your server
- **[Advanced Configuration](configuration/advanced.md)** - Sentry, plugins, etc.

### Advanced Topics

- **[Database Optimization](database/postgres-setup.md)** - Tuning PostgreSQL
- **[Scaling](operations/performance.md#scaling)** - Handle more load
- **[Custom Plugins](configuration/advanced.md#plugin-system)** - Extend functionality

Ready to deploy? Start with **[Docker Compose Deployment](deployment/docker-compose.md)**!
