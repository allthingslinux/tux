# Setup and repository layout

## Tech stack

**Core:** Python 3.13.2+ • discord.py • PostgreSQL 17+ • SQLModel • Docker

**Tools:** uv • ruff • basedpyright • pytest • loguru • sentry-sdk • httpx • Zensical

**Additional:** typer (CLI) • Alembic (migrations) • psycopg (async PostgreSQL) • pydantic-settings • Valkey (optional cache backend; CacheService, InMemoryBackend/ValkeyBackend)

## Quick setup

```bash
# Install dependencies
uv sync

# Generate configuration files
uv run config generate
cp .env.example .env
cp config/config.json.example config/config.json

# Edit configuration (minimum required: BOT_TOKEN)
nano .env
nano config/config.json

# Start database (Docker Compose)
docker compose up -d tux-postgres
# Or with Adminer UI:
docker compose --profile adminer up -d

# Initialize database
uv run db init

# Start bot
uv run tux start
# Or with debug mode:
uv run tux start --debug
```

## Project structure

```text
tux/
├── src/tux/                    # Main source code
│   ├── cache/                  # Cache layer: CacheService, backends (InMemoryBackend, ValkeyBackend), TTLCache, managers (GuildConfigCacheManager, JailStatusCache)
│   ├── core/                   # Bot core (bot.py, app.py, base_cog.py)
│   ├── database/               # Database layer
│   │   ├── models/             # SQLModel models
│   │   ├── migrations/         # Alembic migrations
│   │   ├── controllers/        # Database controllers (CRUD)
│   │   ├── service.py          # DatabaseService
│   │   └── utils.py            # Database utilities
│   ├── services/               # Business logic services
│   │   ├── handlers/           # Event & error handlers
│   │   ├── hot_reload/         # Hot reload system
│   │   ├── moderation/         # Moderation services
│   │   ├── sentry/             # Sentry integration
│   │   └── wrappers/           # External API wrappers
│   ├── modules/                # Discord commands (cogs)
│   │   ├── admin/              # Admin commands
│   │   ├── config/             # Configuration commands
│   │   ├── features/           # Feature modules
│   │   ├── fun/                # Fun commands
│   │   ├── info/               # Information commands
│   │   ├── levels/             # Leveling system
│   │   ├── moderation/         # Moderation commands
│   │   ├── snippets/           # Snippet commands
│   │   ├── tools/              # Utility tools
│   │   └── utility/            # Utility commands
│   ├── plugins/                # Plugin system
│   │   ├── atl/                # All Things Linux plugins
│   ├── ui/                     # UI components
│   │   ├── embeds.py           # Rich embeds
│   │   ├── buttons.py          # Button components
│   │   ├── modals/             # Modal dialogs
│   │   └── views/              # View components
│   ├── shared/                 # Shared utilities
│   │   ├── config/             # Configuration models
│   │   ├── constants.py        # Constants
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── functions.py        # Utility functions
│   ├── help/                   # Help system
│   └── main.py                 # Application entry point
├── scripts/                    # CLI command scripts
│   ├── ai/                     # AI/Cursor validation
│   ├── config/                 # Configuration commands
│   ├── db/                     # Database commands
│   ├── dev/                    # Development tools
│   ├── docs/                   # Documentation commands
│   ├── test/                   # Testing commands
│   └── tux/                    # Bot commands
├── tests/                      # Test suite
│   ├── core/                   # Core tests
│   ├── database/               # Database tests
│   ├── services/               # Service tests
│   ├── modules/                # Module tests
│   ├── plugins/                # Plugin tests
│   └── shared/                 # Shared test utilities
├── docs/                       # Zensical documentation
│   └── content/                # Documentation content
├── docker/                     # Docker configuration
│   ├── entrypoint.sh           # Container entrypoint
│   ├── postgres/               # PostgreSQL config
│   └── adminer/                # Adminer config
├── config/                     # Configuration examples
├── compose.yaml                # Docker Compose (dev + production)
├── Containerfile               # Docker image definition
└── .cursor/                    # Cursor rules & commands
    ├── rules/                  # AI coding patterns (.mdc)
    ├── commands/               # Workflow commands (.md)
    └── templates/              # Rule/command templates
```
