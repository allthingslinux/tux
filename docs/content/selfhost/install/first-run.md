---
title: First Run Instructions
tags:
  - selfhost
  - installation
  - setup
---

# First Run Instructions

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Start Tux for the first time and verify everything works.

## Prerequisites Checklist

Before starting Tux, ensure you have:

- [x] Discord bot token obtained
- [x] PostgreSQL database created
- [x] `.env` file configured
- [x] Config file created (optional)
- [x] Dependencies installed (if not using Docker)

## Starting Tux

### Docker Compose

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f tux
```

### Local/VPS

```bash
# Ensure dependencies are installed
uv sync

# Run migrations
uv run db push

# Start bot
uv run tux start
```

## What to Expect

### Startup Sequence

1. **Configuration Loading**

   ```text
   Loading configuration...
   ✓ Environment variables loaded
   ✓ Config file loaded
   ```

2. **Database Connection**

   ```text
   Connecting to database...
   ✓ Database connected
   ✓ Running migrations...
   ```

3. **Bot Initialization**

   ```text
   Initializing bot...
   ✓ Loading cogs...
   ✓ Syncing commands...
   ```

4. **Discord Connection**

   ```text
   Connecting to Discord...
   ✓ Logged in as Tux#1234
   ✓ Ready!
   ```

### Success Indicators

✅ **Bot is ready** log message  
✅ Bot shows as online in Discord  
✅ No error messages in logs  
✅ Commands respond (`/ping` works)

## Initial Configuration

### 1. Verify Bot is Online

In Discord, check:

- Bot appears in member list
- Green online status
- No error badge

### 2. Test Basic Command

```text
/ping
```

Should respond with latency and uptime.

### 3. Run Setup Wizard

```text
/config wizard
```

Interactive setup for:

- Moderation channels
- Jail system
- Starboard
- XP roles
- Basic settings

### 4. Set Up Permissions

```text
/config rank init
/config role assign 3 @Moderators
/config role assign 5 @Admins
```

### 5. Test Moderation

```text
/warn @TestUser Test warning
/cases
```

Verify case system works.

## Troubleshooting First Run

### Bot Won't Start

**Check logs for specific error:**

```bash
# Docker
docker compose logs tux

# Systemd
sudo journalctl -u tux -f

# Local
# Error appears in terminal
```

**Common causes:**

#### "Invalid Token" Error

```text
discord.errors.LoginFailure: Improper token has been passed
```

**Solution:**

- Verify BOT_TOKEN in `.env` is correct
- No extra spaces or quotes
- Token is from Bot tab, not OAuth2 secret
- Reset token if unsure

#### "Database Connection Failed"

```text
asyncpg.exceptions.InvalidCatalogNameError: database "tuxdb" does not exist
```

**Solution:**

- Create database: `createdb tuxdb`
- Check POSTGRES_* variables in `.env`
- Verify PostgreSQL is running
- Test connection: `psql -h localhost -U tuxuser -d tuxdb`

#### "Permission Denied" (Database)

```text
asyncpg.exceptions.InsufficientPrivilegeError
```

**Solution:**

```bash
sudo -u postgres psql << EOF
GRANT ALL PRIVILEGES ON DATABASE tuxdb TO tuxuser;
\c tuxdb
GRANT ALL ON SCHEMA public TO tuxuser;
EOF
```

#### "Missing Intents"

```text
Privileged intent ... is not enabled
```

**Solution:**

- Go to Discord Developer Portal
- Bot tab → Enable "Server Members Intent"
- Bot tab → Enable "Message Content Intent"
- Restart bot

### Bot Starts But Shows Offline

**Causes:**

- Token is invalid
- Network connectivity issues
- Discord API issues

**Solutions:**

1. Check token is correct
2. Verify internet connection
3. Check Discord API status: [status.discord.com](https://status.discord.com)
4. Review bot logs for connection errors

### Commands Don't Work

**Test slash commands:**

```text
/ping
/help
```

**If not working:**

1. Wait 1-2 minutes (Discord sync delay)
2. Check bot has `applications.commands` scope
3. Run `/dev sync_tree` (if you have permission)
4. Re-invite bot with correct scopes

**Test prefix commands:**

```text
$ping
$help
```

**If not working:**

1. Check prefix is correct (`$` by default)
2. Verify Message Content Intent is enabled
3. Check bot has Read Messages permission

### Migration Errors

```text
alembic.util.exc.CommandError
```

**Solutions:**

```bash
# Check migration status
uv run db status

# Apply migrations
uv run db push

# If corrupted, reset and retry
uv run db reset
```

## Post-Startup Checks

### Verify Core Features

```bash
# 1. Bot responding
/ping                               # ✓ Should respond

# 2. Database working
/snippet test_snippet               # Create test snippet first

# 3. Permissions working
/config rank                        # ✓ Should show ranks

# 4. Moderation working
/warn @TestUser Test                # ✓ Creates case

# 5. Check cases
/cases                              # ✓ Shows test case
```

### Check Logs

Look for warnings or errors:

```bash
# Docker
docker compose logs tux | grep -E "ERROR|WARNING"

# Systemd
sudo journalctl -u tux | grep -E "ERROR|WARNING"
```

### Monitor Resources

```bash
# Docker
docker stats tux

# System
htop
free -h
df -h
```

## Configuration Verification

### Check Loaded Config

Bot logs show loaded configuration on startup:

```text
Configuration loaded from:
  - .env file
  - config.toml
  - Defaults
```

### Verify Settings

```text
/config                             # View current config
```

Should show your configured settings.

## Next Steps

After successful first run:

1. **[Configure Features](../config/index.md)** - Enable/disable features
2. **[Set Up Backups](../manage/database.md)** - Protect your data
3. **[Configure Monitoring](../manage/operations.md)** - Watch for issues

## Running in Background

### Background with Docker Compose

Already runs in background with `-d` flag:

```bash
docker compose up -d
```

### Background with Systemd

```bash
sudo systemctl enable tux           # Start on boot
sudo systemctl start tux            # Start now
```

### Screen/Tmux (Not Recommended)

For temporary deployments only:

```bash
# Screen
screen -S tux
uv run tux start
# Ctrl+A, D to detach

# Tmux
tmux new -s tux
uv run tux start
# Ctrl+B, D to detach
```

Use systemd instead for production!

## Logs Location

### Docker

```bash
docker compose logs tux             # View logs
```

### Systemd

```bash
journalctl -u tux -f                # Follow logs
```

### Local Development

Logs output to stdout/stderr and optionally to files in `logs/`.

## Need Help?

### Common Issues

- **[Troubleshooting Guide](../../support/troubleshooting/selfhost.md)** - Common problems
- **[Database Issues](../manage/database.md#troubleshooting)** - Database-specific

### Community Support

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask in #self-hosting
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report bugs

---

**Congratulations!** Tux is now running. Head to [Configuration](../../admin/config/index.md) to customize your instance.
