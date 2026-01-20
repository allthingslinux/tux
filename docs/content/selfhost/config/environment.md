---
title: Environment Configuration
tags:
  - selfhost
  - configuration
  - environment
---

# Environment Configuration

Configure Tux using environment variables. The **[ENV Reference](../../reference/env.md)** is auto-generated from code and lists every variable, type, default, and example—use it as the single source of truth.

!!! tip "Configuration priority"
    Load order (highest to lowest): environment variables → `.env` → `config/config.toml` → `config/config.yaml` → `config/config.json` → defaults. See the [ENV Reference](../../reference/env.md) for details.

## Essential variables

You must set these to run Tux:

### Bot token

```env
BOT_TOKEN=your_bot_token_here
```

Get a token from the [Discord Developer Portal](https://discord.com/developers/applications). See [Bot Token Setup](bot-token.md) for details.

### Database

Use either **individual PostgreSQL variables** or a **connection URL**:

```env
# Option A: Individual (recommended for Docker)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=your_secure_password

# Option B: Override with a URL (overrides POSTGRES_*)
# DATABASE_URL=postgresql://user:password@localhost:5432/tuxdb
```

!!! warning "Security"
    Use a strong `POSTGRES_PASSWORD` in production. Never commit real credentials.

See [Database Configuration](database.md) for setup.

### Bot owner (recommended)

```env
USER_IDS__BOT_OWNER_ID=123456789012345678
```

Enables owner-only commands and maintenance control. [ENV Reference](../../reference/env.md) documents `USER_IDS__SYSADMINS` and other IDs.

## Docker

With Docker Compose, put variables in `.env`; Compose loads them automatically. At minimum set `BOT_TOKEN` and database settings (e.g. `POSTGRES_PASSWORD` and, if needed, `POSTGRES_HOST=tux-postgres`). For the full set of variables, see the [ENV Reference](../../reference/env.md).

The `compose.yaml` uses `${VARIABLE_NAME}`. See [Docker Installation](../install/docker.md) for setup.

## Validation and testing

```bash
uv run config validate    # Check config and which sources are loaded
uv run db health          # Test database connection
uv run tux start --debug  # Run with .env loaded (good for quick tests)
```

!!! note "Automatic .env loading"
    Tux loads `.env` on startup; you don't need to `source` it.

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| **Missing/unknown variables** | Use the **[ENV Reference](../../reference/env.md)** for correct names (e.g. `BOT_TOKEN`, not `DISCORD_TOKEN`). Nested keys use `__` (e.g. `BOT_INFO__PREFIX`). |
| **Database errors** | Verify `POSTGRES_*` or `DATABASE_URL`, that the DB is running, and that the database exists with correct permissions. |
| **Config not loading** | Run `uv run config validate` to see which files are used. Ensure paths and UTF-8 encoding are correct. |

## Next steps

- [Database Configuration](database.md) – Database setup
- [First Run Setup](../install/first-run.md) – Initial configuration
- [System Operations](../manage/operations.md) – Monitoring and maintenance  
- **[ENV Reference](../../reference/env.md)** – Full, auto-generated list of all variables
