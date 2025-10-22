# Configuration Overview

Comprehensive guide to configuring your Tux instance.

## Configuration System

Tux uses a multi-source configuration system with priority:

1. **Environment variables** (`.env`) - Highest priority
2. **Config file** (`config.toml`/`yaml`/`json`)
3. **Default values** - Lowest priority

## Configuration Topics

### Bot Settings

**[Bot Settings →](bot-settings.md)**

Configure:

- Command prefix
- Bot name and activities
- Owner information

### Guild Setup

**[Guild Setup →](guild-setup.md)**

Per-server configuration via:

- Config wizard
- Manual commands
- Database settings

### Permissions

**[Permissions →](permissions.md)**

Set up:

- Permission ranks (0-7)
- Role assignments
- Command permissions

### Features

**[Features →](features.md)**

Enable/configure:

- XP/Leveling system
- Starboard
- Temp VC
- Status roles
- GIF limiter

### Advanced

**[Advanced →](advanced.md)**

Optional integrations:

- Sentry error tracking
- InfluxDB metrics
- GitHub integration
- Plugins

## Quick Reference

### Essential Settings

```toml
[bot_info]
prefix = "$"
bot_name = "Tux"

[xp]
xp_cooldown = 60
levels_exponent = 2.0
```

### Where to Configure

| Setting Type | Best Place |
|-------------|------------|
| Secrets (tokens, passwords) | `.env` file |
| Simple values | `.env` or config file |
| Complex structures (arrays) | Config file (TOML/YAML/JSON) |
| Per-server settings | Database (via commands) |

## Configuration Layers

### 1. Application Level (.env + config file)

- Bot token
- Database connection
- Global features
- External services

### 2. Guild Level (Database)

- Per-server prefix
- Mod log channels
- Jail configuration
- Starboard settings

Configured via `/config` commands in Discord.

## Getting Help

- **[Environment Variables](../setup/environment-variables.md)** - .env reference
- **[Config Files](../setup/config-files.md)** - TOML/YAML/JSON format
- **[Configuration Reference](../../reference/configuration.md)** - Complete schema

---

**Choose a topic above to continue.**
