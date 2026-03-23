# Code standards, architecture notes, and cache

For authoritative Python style and domain rules, prefer [.cursor/rules/rules.mdc](../.cursor/rules/rules.mdc) and the focused `.mdc` files (for example `core/style-guide.mdc`).

## Code standards (summary)

**Python:**

- Strict type hints (`Type | None` not `Optional[Type]`)
- NumPy docstrings
- Absolute imports preferred, relative imports allowed within the same module
- Import grouping: stdlib → third-party → local
- 88 char line length (ruff)
- snake_case (functions/vars), PascalCase (classes), UPPER_CASE (constants)
- Always add imports to the top of the file unless absolutely necessary

## Common patterns

**Services:**

- Dependency injection
- Stateless where possible
- Async/await for I/O
- Appropriate logging

**Error handling:**

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

## Security and performance

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

## File organization

- **Max 1600 lines per file** - Split larger files into logical modules
- **One class/function per file when possible** - Improves maintainability
- **Descriptive filenames** - Use clear, purpose-driven names
- **Absolute imports preferred** - Relative imports allowed within same module
- **Import grouping** - stdlib → third-party → local (with blank lines)

## Cache

**Stack:** `tux.cache` — CacheService (Valkey lifecycle), backends (InMemoryBackend, ValkeyBackend), TTLCache, cache managers (GuildConfigCacheManager, JailStatusCache). Optional Valkey for shared cache across processes/restarts.

- **CacheService** — Async Valkey client; connect/ping/close. Created at startup; `bot.cache_service` is set when `VALKEY_URL` is configured and connection succeeds.
- **Backends** — `get_cache_backend(bot)` returns ValkeyBackend when connected, else a shared InMemoryBackend. Keys use `tux:` prefix; values are JSON.
- **Managers** — GuildConfigCacheManager and JailStatusCache (and prefix/permission consumers) use the injected backend; no code changes needed when switching in-memory vs Valkey.
- **Config** — Set `VALKEY_URL=valkey://host:port/db` in `.env` to enable Valkey; leave unset for in-memory only.
- **Health** — `uv run db health` includes an optional Valkey check when `VALKEY_URL` is set.

See [Caching Best Practices](../docs/content/developer/best-practices/caching.md) for usage and multi-guild safety.
