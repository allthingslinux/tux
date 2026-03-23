# Workflow, Docker, and contributing

## Development workflow

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

## Conventional commits

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

## Pull requests

**Title:** `[module/area] Brief description`

**Requirements:**

- All tests pass (`uv run test all`)
- Quality checks pass (`uv run dev all`)
- Migrations tested (`uv run db dev`)
- Cursor rules/commands validated (`uv run ai validate-rules`)
- Documentation updated
- Type hints complete
- Docstrings for public APIs
