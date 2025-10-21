# Deployment Options

Choose the best deployment method for your needs.

## Comparison

| Method | Difficulty | Control | Cost | Best For |
|--------|-----------|---------|------|----------|
| **[Docker Compose](docker-compose.md)** | ⭐⭐ Easy | ⭐⭐⭐⭐ High | Free* | Most users |
| **[VPS/Systemd](systemd-vps.md)** | ⭐⭐⭐⭐ Advanced | ⭐⭐⭐⭐⭐ Full | $5-20/mo | Power users |
| **[Cloud Platforms](cloud-platforms.md)** | ⭐ Very Easy | ⭐⭐⭐ Medium | $5-15/mo | Quick start |

*Free if you already have a server

## Recommended: Docker Compose

**Best for:** Most self-hosters

✅ **Pros:**

- Easy to set up and maintain
- Includes PostgreSQL and Adminer
- Automatic restarts
- Simple updates (`git pull && docker compose up -d --build`)
- Works on Linux, macOS, Windows

❌ **Cons:**

- Requires Docker knowledge
- Slightly more resources than bare metal
- Container management overhead

**[Docker Compose Guide →](docker-compose.md)**

## VPS with Systemd

**Best for:** Advanced users who want full control

✅ **Pros:**

- Complete control over environment
- Better performance (no container overhead)
- Flexible configuration
- Direct access to everything

❌ **Cons:**

- Requires Linux system administration skills
- Manual dependency management
- More complex updates
- You manage PostgreSQL separately

**[VPS Deployment Guide →](systemd-vps.md)**

## Cloud Platforms

**Best for:** Quick deployment without managing servers

✅ **Pros:**

- Extremely fast setup
- Managed infrastructure
- Automatic scaling
- Built-in monitoring
- Free tier available (some platforms)

❌ **Cons:**

- Monthly costs (typically)
- Less control
- Platform lock-in
- May have limitations

**[Cloud Platform Guide →](cloud-platforms.md)**

## Requirements

### All Deployment Methods Need

- **Discord Bot Application** - [Get bot token](../setup/discord-bot-token.md)
- **PostgreSQL Database** - Included in Docker or self-managed
- **Python 3.13+** - Included in Docker or install manually

### System Requirements

**Minimum:**

- 1 CPU core
- 512 MB RAM
- 2 GB storage
- Linux/macOS/Windows

**Recommended for Production:**

- 2 CPU cores
- 2 GB RAM
- 10 GB storage (for logs and backups)
- Linux (Ubuntu 22.04+ or Debian 12+)

**For Large Servers (1000+ members):**

- 4 CPU cores
- 4 GB RAM
- 20 GB storage
- Dedicated database server

## Quick Decision Guide

### Choose Docker Compose if

:

- ✅ You want the easiest setup
- ✅ You have Docker installed or can install it
- ✅ You want included PostgreSQL
- ✅ You prefer container-based deployment
- ✅ You want easy updates

### Choose VPS/Systemd if

- ✅ You have Linux sysadmin experience
- ✅ You want maximum performance
- ✅ You want complete control
- ✅ You have existing infrastructure
- ✅ You prefer bare metal

### Choose Cloud Platform if

- ✅ You want fastest deployment
- ✅ You don't want to manage servers
- ✅ You're okay with monthly costs
- ✅ You want managed database
- ✅ You prefer hands-off approach

## Next Steps

1. **Choose your deployment method** using the comparison above
2. **Follow the specific guide** for your chosen method
3. **Complete initial setup** (bot token, configuration)
4. **Deploy Tux** and verify it's running
5. **Configure your instance** per server needs

## Getting Help

- **[Discord Support](https://discord.gg/gpmSjcjQxg)** - Ask in #self-hosting
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report deployment issues
- **[Troubleshooting](../operations/troubleshooting.md)** - Common problems

---

**Ready to deploy?** Choose your method above and get started!
