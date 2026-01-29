---
title: Environment Configuration
tags:
  - selfhost
  - configuration
  - environment
icon: lucide/variable
---

# Environment Configuration

Configure Tux using environment variables. The **[ENV Reference](../../reference/env.md)** is auto-generated from code and lists every variable, type, default, and example—use it as the single source of truth.

!!! tip "Configuration priority"
    Load order (highest to lowest): environment variables → `.env` → `config/config.json` or `config.json` → file secrets (`/run/secrets`) → defaults. See the [ENV Reference](../../reference/env.md) for details.

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

### Optional: Valkey (cache)

Valkey (Redis-compatible) is an **optional** cache backend. When configured, Tux uses it for
guild config, jail status, prefix, and permission caches so state can be shared across
restarts or multiple processes. When Valkey is not set or unavailable, Tux uses an
in-memory cache (no extra service required).

Use either **VALKEY_URL** or **individual variables**:

```env
# Option A: URL (overrides VALKEY_HOST/PORT/DB/PASSWORD)
VALKEY_URL=valkey://localhost:6379/0

# Option B: Individual (e.g. for Docker with tux-valkey)
VALKEY_HOST=tux-valkey
VALKEY_PORT=6379
VALKEY_DB=0
VALKEY_PASSWORD=
```

Leave `VALKEY_URL` and `VALKEY_HOST` empty to disable Valkey. See the
[ENV Reference](../../reference/env.md) for all Valkey variables.

!!! note "When to use Valkey"
    Use Valkey if you want cache to persist across bot restarts or run multiple Tux
    processes. For a single instance that restarts rarely, in-memory cache is sufficient.

!!! tip "VALKEY_HOST: localhost vs tux-valkey"
    Use **`VALKEY_HOST=localhost`** (or `VALKEY_URL=valkey://localhost:6379/0`) when
    running the bot on your host (e.g. `uv run tux start`). Use **`VALKEY_HOST=tux-valkey`**
    when the bot runs inside Docker Compose so it can reach the Valkey container by
    service name. If you see "Name or service not known" for `tux-valkey`, you are
    running the bot locally—switch to `localhost` or start Valkey and point to it.

### Bot owner and sysadmins (recommended)

Configure in **`config/config.json`**, not in `.env`:

```json
{
  "USER_IDS": {
    "BOT_OWNER_ID": 123456789012345678,
    "SYSADMINS": [123456789012345678, 987654321098765432]
  }
}
```

Enables owner-only commands and maintenance control. See [Self-Host Configuration](index.md) for the full JSON layout and `uv run config generate` for an example file.

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
