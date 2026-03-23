# AGENTS.md

**Tux** is an all-in-one open source Discord bot for the [All Things Linux](https://allthingslinux.org) community.

## Tech Stack

**Core:** Python 3.13.2+ • discord.py • PostgreSQL 17+ • SQLModel • Docker
**Tools:** uv • ruff • basedpyright • pytest • loguru • sentry-sdk • httpx • Zensical
**Additional:** typer (CLI) • Alembic (migrations) • psycopg (async PostgreSQL) • pydantic-settings • Valkey (optional cache backend; CacheService, InMemoryBackend/ValkeyBackend)

## Cursor Rules & Commands

The project uses Cursor's rules and commands system for AI-assisted development:

See [.cursor/rules/rules.mdc](.cursor/rules/rules.mdc) for the complete catalog of all rules and commands.

- **Rules** (`.cursor/rules/*.mdc`) - Project-specific coding patterns automatically applied
- **Commands** (`.cursor/commands/*.md`) - Reusable workflows invoked with `/` prefix

**Validation:**

```bash
uv run ai validate-rules      # Validate all rules and commands
```

**Documentation:**

- [Creating Cursor Rules](docs/content/developer/guides/creating-cursor-rules.md)
- [Creating Cursor Commands](docs/content/developer/guides/creating-cursor-commands.md)
- [Cursor Rules & Commands Overview](.cursor/README.md)

!!! tip "Detailed Rules Available"
    This file provides a high-level overview. For detailed, domain-specific patterns and standards, see the rules in `.cursor/rules/` organized by domain (database, modules, testing, security, etc.).

## Quick Setup

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

## Project Structure

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

## Code Standards

**Python:**

- Strict type hints (`Type | None` not `Optional[Type]`)
- NumPy docstrings
- Absolute imports preferred, relative imports allowed within the same module
- Import grouping: stdlib → third-party → local
- 88 char line length
- snake_case (functions/vars), PascalCase (classes), UPPER_CASE (constants)
- Always add imports to the top of the file unless absolutely necessary

**Quality checks:**

```bash
uv run dev all                # Run all quality checks (format, lint, type-check)
uv run dev pre-commit         # Run full pre-commit suite
uv run dev format             # Format code with ruff
uv run dev lint               # Lint code (check only)
uv run dev lint-fix           # Lint and auto-fix issues
uv run dev type-check         # Type checking with basedpyright
uv run dev lint-docstring     # Lint docstrings with pydoclint
uv run dev docstring-coverage # Check docstring coverage
uv run dev clean              # Clean build artifacts and caches
```

## Testing

```bash
uv run test                 # Quick tests (default, no coverage)
uv run test all             # Full test suite with coverage
uv run test quick           # Fast run (no coverage, explicit)
uv run test fast            # Fast tests only
uv run test plain           # Plain output (no colors/formatting)
uv run test parallel        # Parallel test execution
uv run test file <path>     # Run tests in specific file
uv run test last-failed     # Re-run last failed tests
uv run test coverage        # Generate coverage report
uv run test html            # Generate HTML coverage report
uv run test benchmark       # Run benchmark tests
```

**Markers:** `unit`, `integration`, `slow`, `database`, `async`

## Database

**Stack:** SQLModel (ORM) • Alembic (migrations) • PostgreSQL 17+ (psycopg async)

```bash
# Migration Management
uv run db init              # Initialize empty database with migrations
uv run db dev               # Generate & apply migration (auto-name)
uv run db dev --name "msg"  # Generate & apply with custom name
uv run db new "description" # Create new migration file only
uv run db push              # Apply all pending migrations
uv run db downgrade -1      # Rollback one migration
uv run db downgrade <rev>   # Rollback to specific revision

# Status & Inspection
uv run db status            # Show current revision and pending migrations
uv run db current           # Show current revision
uv run db history           # Show full migration history
uv run db show head         # Show SQL for head revision
uv run db check             # Validate migration files
uv run db version           # Show Alembic version

# Database Operations
uv run db health            # Check database connection
uv run db tables            # List all database tables
uv run db schema            # Show database schema
uv run db queries           # Run custom database queries
uv run db fix-sequences     # Fix PostgreSQL sequence synchronization issues
uv run db fix-sequences --dry-run  # Preview sequence fixes
uv run db reset             # Safe reset (downgrade to base, reapply all)
uv run db nuke              # Complete wipe (destructive, requires confirmation)
uv run db nuke --fresh      # Nuclear reset + delete migration files
```

**Health:** `uv run db health` checks PostgreSQL and, when `VALKEY_URL` is set, Valkey (cache) connectivity.

## Cache

**Stack:** `tux.cache` — CacheService (Valkey lifecycle), backends (InMemoryBackend, ValkeyBackend), TTLCache, cache managers (GuildConfigCacheManager, JailStatusCache). Optional Valkey for shared cache across processes/restarts.

- **CacheService** — Async Valkey client; connect/ping/close. Created at startup; `bot.cache_service` is set when `VALKEY_URL` is configured and connection succeeds.
- **Backends** — `get_cache_backend(bot)` returns ValkeyBackend when connected, else a shared InMemoryBackend. Keys use `tux:` prefix; values are JSON.
- **Managers** — GuildConfigCacheManager and JailStatusCache (and prefix/permission consumers) use the injected backend; no code changes needed when switching in-memory vs Valkey.
- **Config** — Set `VALKEY_URL=valkey://host:port/db` in `.env` to enable Valkey; leave unset for in-memory only.
- **Health** — `uv run db health` includes an optional Valkey check when `VALKEY_URL` is set.

See [Caching Best Practices](docs/content/developer/best-practices/caching.md) for usage and multi-guild safety.

## CLI Commands

**Bot:**

```bash
uv run tux start            # Start bot
uv run tux start --debug    # Debug mode
uv run tux version          # Show version information
```

**Docs:**

```bash
uv run docs serve           # Local preview server
uv run docs build           # Build documentation site
uv run docs lint            # Lint documentation files
uv run docs deploy          # Deploy to GitHub Pages (via Wrangler)
# Wrangler commands (Cloudflare Pages):
uv run docs wrangler-dev    # Start Wrangler dev server
uv run docs wrangler-deploy # Deploy to Cloudflare Pages
uv run docs wrangler-rollback # Rollback deployment
uv run docs wrangler-versions # List deployment versions
uv run docs wrangler-tail   # Tail deployment logs
uv run docs wrangler-deployments # List all deployments
```

**Configuration:**

```bash
uv run config generate      # Generate configuration example files
uv run config validate      # Validate the current configuration
```

**Cursor:**

```bash
uv run ai validate-rules   # Validate Cursor rules and commands
```

## Development Workflow

1. **Setup:** `uv sync` → configure `.env` & `config.json` → `docker compose up -d tux-postgres` → `uv run db init`
2. **Develop:** Make changes → `uv run dev all` → `uv run test quick`
3. **Database:** Modify models → `uv run db new "description"` → `uv run db dev` (or `uv run db dev --name "description"` for auto-create+apply)
4. **Rules:** Validate rules/commands → `uv run ai validate-rules`
5. **Commit:** `uv run dev pre-commit` → `uv run test all`

## Docker Compose

Tux uses a single `compose.yaml` with profiles for development and production:

```bash
# Development (build from source, hot reload)
docker compose --profile dev up -d
docker compose --profile dev up --watch  # With hot reload

# Production (pre-built image, security hardening)
docker compose --profile production up -d

# Add Adminer (database UI)
docker compose --profile dev --profile adminer up -d
docker compose --profile production --profile adminer up -d

# Using environment variable
COMPOSE_PROFILES=dev docker compose up -d
COMPOSE_PROFILES=production docker compose up -d

# PostgreSQL only (no profile needed)
docker compose up -d tux-postgres
```

**Profiles:**

- `dev` - Development mode with source bindings and hot reload
- `production` - Production mode with pre-built image and security hardening
- `adminer` - Optional database management UI (combine with dev or production)

**Note:** `tux-postgres` has no profile and always starts. Use `--profile valkey` to start Valkey (optional cache). Do not use `--profile dev` and `--profile production` together.

**Optional: Valkey (cache):** For shared cache across processes or restarts, start Valkey and set env:

```bash
docker compose --profile valkey up -d tux-valkey
# In .env: VALKEY_URL=valkey://localhost:6379/0  (or leave unset to use in-memory cache)
```

When `VALKEY_URL` is set and reachable, guild config, jail status, prefix, and permission caches use Valkey; otherwise they use in-memory TTL caches.

## Conventional Commits

Format: `<type>[scope]: <description>`

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Rules:**

- Lowercase type
- Max 120 chars subject
- No period at end
- Start with lowercase

**Examples:**

```bash
feat: add user authentication
fix: resolve memory leak in message handler
docs: update API documentation
refactor(database): optimize query performance
```

## Pull Requests

**Title:** `[module/area] Brief description`

**Requirements:**

- All tests pass (`uv run test all`)
- Quality checks pass (`uv run dev all`)
- Migrations tested (`uv run db dev`)
- Cursor rules/commands validated (`uv run ai validate-rules`)
- Documentation updated
- Type hints complete
- Docstrings for public APIs

## Common Patterns

**Services:**

- Dependency injection
- Stateless where possible
- Async/await for I/O
- Appropriate logging

**Error Handling:**

- Custom exceptions for business logic
- Log with context
- Meaningful user messages
- Handle Discord rate limits

**Database:**

- SQLModel for type safety
- Alembic for migrations
- Pydantic for data validation
- Async operations
- Transactions for multi-step ops
- Model-level validation

**Discord:**

- Hybrid commands (slash + traditional)
- Role-based permissions
- Rich embeds
- Cooldowns & rate limiting

## Security & Performance

**Security:**

- **No secrets in code** - Use `.env` files and environment variables
- **Environment variables for config** - `pydantic-settings` for validation
- **Validate all inputs** - User input validation at boundaries
- **Proper permission checks** - Role-based permission system
- **Read-only filesystem** - Production Docker containers use read-only root
- **Non-root user** - Containers run as `nonroot` (UID 1001)
- **Security options** - `no-new-privileges` in production

**Performance:**

- **Async for I/O** - All database and HTTP operations are async
- **Connection pooling** - psycopg connection pooling for PostgreSQL
- **TTL caching** - Thread-safe TTL cache system for frequently accessed data (guild config, jail status, permissions). Optional Valkey backend for shared cache across restarts (set `VALKEY_URL` and run `tux-valkey` in compose).
- **Batch operations** - Batch retrieval for permission checks and database queries
- **Cache pre-warming** - Automatic cache pre-warming on bot startup
- **Optimize queries** - Use database controllers with proper indexing
- **HTTP client optimization** - Automatic configuration for high-latency environments
- **Monitor memory** - Sentry integration for performance monitoring
- **Lazy loading** - Load modules and plugins on demand

## File Organization

- **Max 1600 lines per file** - Split larger files into logical modules
- **One class/function per file when possible** - Improves maintainability
- **Descriptive filenames** - Use clear, purpose-driven names
- **Absolute imports preferred** - Relative imports allowed within same module
- **Import grouping** - stdlib → third-party → local (with blank lines)

## Troubleshooting

```bash
# Database issues
uv run db health              # Check database connection
uv run db status              # Check migration status
uv run db fix-sequences --dry-run  # Check sequence synchronization issues
docker compose ps tux-postgres # Check PostgreSQL container

# Import errors
uv sync --reinstall          # Reinstall all dependencies

# Type errors
uv run dev type-check         # Run type checker
uv run basedpyright --verbose # Verbose type checking

# Test failures
uv run test quick            # Quick test run
uv run test last-failed      # Re-run failed tests
uv run pytest -v -s          # Verbose pytest output

# Code quality issues
uv run dev all                # Run all quality checks
uv run dev lint-fix           # Auto-fix linting issues
uv run dev format             # Format code

# Cursor validation
uv run ai validate-rules      # Validate Cursor rules and commands

# Docker issues
docker compose logs tux       # View bot logs
docker compose logs tux-postgres # View database logs
docker compose ps             # Check container status
docker compose restart tux    # Restart bot container
```

## Resources

- **Docs:** <https://tux.atl.dev>
- **Issues:** <https://github.com/allthingslinux/tux/issues>
- **Discord:** <https://discord.gg/gpmSjcjQxg>
- **Repo:** <https://github.com/allthingslinux/tux>
