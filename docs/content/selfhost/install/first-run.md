---
title: First Run Instructions
tags:
  - selfhost
  - installation
  - setup
icon: lucide/rocket
---

# First Run Instructions

After installing Tux, follow these steps to verify your installation and complete the initial setup.

## Prerequisites

Before running Tux for the first time, ensure you have:

- ✅ Bot token configured in `.env` (see [Bot Token Setup](../config/bot-token.md))
- ✅ Database configured and accessible (see [Database Configuration](../config/database.md))
- ✅ Configuration files generated (`uv run config generate`)
- ✅ Services started (Docker Compose or systemd)

## Verification Steps

### 1. Check Configuration

Verify your configuration is valid:

```bash
# Validate configuration
uv run config validate
```

This command checks:

- Configuration file syntax
- Required environment variables
- Configuration source priority
- Any configuration errors

### 2. Test Database Connection

Verify database connectivity:

```bash
# Check database health
uv run db health
```

Expected output:

- Database connection successful
- Current migration revision
- Database tables accessible

If this fails, check:

- Database is running
- Connection credentials are correct
- Database exists and user has permissions

### 3. Initialize Database

If this is a fresh installation, initialize the database:

```bash
# Initialize database with migrations
uv run db init
```

This creates all required tables and applies initial migrations.

!!! tip "Docker Users"
    Migrations run automatically on container startup. You only need to run `db init` manually if migrations fail or you're using a custom setup.

### 4. Start the Bot

#### Docker Compose

```bash
# Development mode
docker compose --profile dev up -d

# Production mode
docker compose --profile production up -d

# Check logs
docker compose logs -f tux
```

#### Bare Metal (systemd)

```bash
# Start service
sudo systemctl start tux

# Check status
sudo systemctl status tux

# View logs
sudo journalctl -u tux -f
```

#### Manual Start (Testing)

For testing or debugging:

```bash
# Start with debug mode
uv run tux start --debug
```

### 5. Verify Bot is Online

Check that the bot appears online in Discord:

1. Open your Discord server
2. Check the member list - Tux should appear online
3. The bot's status should show as active

### 6. Test Basic Commands

Test that commands work:

```bash
# In Discord, try:
$ping
$help
```

Expected responses:

- `/ping` - Bot latency and system stats
- `$help` - Interactive help menu

!!! note "Permission System"
    Before using moderation or configuration commands, you'll need to set up the permission system. See [Permission Configuration](../../admin/config/ranks.md) for details.

## Initial Configuration

### Set Up Permission System

1. **Initialize Permission Ranks:**

   ```text
   $config ranks
   ```

   Click "🚀 Init Default Ranks" in the dashboard

2. **Assign Roles to Ranks:**

   ```text
   $config roles
   ```

   Map your Discord roles to permission ranks

3. **Configure Command Permissions:**

   ```text
   $config commands
   ```

   Set required permission ranks for commands

### Configure Logging Channels

Set up audit and moderation logs:

```text
$config logs
```

Configure:

- **Audit Log Channel** - Records all moderation actions
- **Moderation Log Channel** - Detailed case logs

### Configure Jail System (Optional)

If you want to use the jail feature:

```text
$config jail
```

Set:

- **Jail Channel** - Channel where jailed members can talk
- **Jail Role** - Role applied to jailed members

## Troubleshooting

### Bot Won't Start

**Check logs for errors:**

```bash
# Docker
docker compose logs tux

# systemd
sudo journalctl -u tux -n 50
```

**Common issues:**

- **Missing BOT_TOKEN** - Verify `.env` has `BOT_TOKEN` set
- **Database connection failed** - Check database is running and credentials are correct
- **Migration errors** - Run `uv run db status` to check migration state
- **Permission errors** - Check file permissions and ownership

### Database Connection Issues

```bash
# Test connection
uv run db health

# Check database status (Docker)
docker compose ps tux-postgres

# Check database status (systemd)
sudo systemctl status postgresql
```

### Bot Appears Offline

**Check:**

1. Bot token is correct in `.env`
2. Bot is invited to your server
3. Bot has necessary permissions
4. No errors in logs
5. Network connectivity

### Commands Not Working

**Verify:**

1. Permission system is initialized (`$config ranks`)
2. Roles are assigned to ranks (`$config roles`)
3. Commands have permission requirements set (`$config commands`)
4. Bot has necessary Discord permissions
5. Commands are synced (slash commands may need time to sync)

## Next Steps

After successful first run:

1. **[Configure Permissions](../../admin/config/ranks.md)** - Set up the permission system
2. **[Set Up Logging](../../admin/config/logs.md)** - Configure audit and moderation logs
3. **[Database Management](../manage/database.md)** - Learn about backups and maintenance
4. **[System Operations](../manage/operations.md)** - Monitor and maintain your installation

## Related Documentation

- [Docker Installation](docker.md) - Docker setup guide
- [Bare Metal Installation](baremetal.md) - Systemd setup guide
- [Environment Configuration](../config/environment.md) - Environment variables
- [Database Configuration](../config/database.md) - Database setup
- [Troubleshooting](../../support/troubleshooting/selfhost.md) - Common issues
