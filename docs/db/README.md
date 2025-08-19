## Database guide (SQLModel + Alembic + PostgreSQL)

This project uses SQLModel (SQLAlchemy + Pydantic v2) for models, Alembic for migrations, and PostgreSQL in production. SQLite is supported for unit tests and quick local dev.

### Environments

- DEV database URL: `DEV_DATABASE_URL`
- PROD database URL: `PROD_DATABASE_URL`

Examples:

```bash
# PostgreSQL (async)
export DEV_DATABASE_URL='postgresql+asyncpg://user:pass@host:5432/dbname'

# SQLite (async)
export DEV_DATABASE_URL='sqlite+aiosqlite:///./dev.sqlite3'
```

### Migrations

- Baseline is explicit, snake_case tables, and includes Postgres-specific types (ENUM, JSONB).
- Runtime startup automatically runs `alembic upgrade head` in non‑dev. In dev, you run Alembic manually.

Common commands:

```bash
# Upgrade to latest
uv run alembic -c alembic.ini upgrade head

# Create a new revision (write explicit ops for renames / complex changes)
uv run alembic -c alembic.ini revision -m "add feature"

# Downgrade (use with care)
uv run alembic -c alembic.ini downgrade -1
```

Notes:
- Use explicit `op.create_table` / `op.rename_table` when autogenerate is insufficient (renames, complex diffs).
- PostgreSQL JSONB indexes should be created with explicit GIN indexes in a migration.

### Local Postgres (Docker)

```bash
docker run --name tux-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16

export DEV_DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5432/postgres'
uv run alembic -c alembic.ini upgrade head
```

### Resetting a dev database (Postgres)

For a local Postgres database, you can drop and recreate the schema:

```bash
psql "$DEV_DATABASE_URL" <<'SQL'
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
SQL

uv run alembic -c alembic.ini upgrade head
```

If using a managed provider (e.g., Supabase), prefer the provider’s reset tooling where available.

### SQLite notes

- SQLite is used in unit tests. Some Postgres-only types (ENUM, JSONB) are not available. Tests target SQLite-compatible tables.
- For local dev with SQLite, use: `sqlite+aiosqlite:///./dev.sqlite3`. Create tables via Alembic (recommended) or `SQLModel.metadata.create_all` during experiments only.

### Programmatic migrations in app

- On startup, non‑dev runs a programmatic Alembic upgrade to `head` (`tux.database.migrations.runner.upgrade_head_if_needed`).
- Dev mode intentionally skips auto-upgrade to keep developer control.
