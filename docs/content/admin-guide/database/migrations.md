# Database Migrations

Manage database schema changes with Alembic migrations.

## What Are Migrations?

Migrations are version-controlled database schema changes:

- Track schema history
- Apply changes incrementally  
- Rollback if needed
- Share schema changes with team

Tux uses **Alembic** for migrations.

## CLI Commands

### Apply Migrations

```bash
# Apply all pending migrations
uv run db push

# Check status
uv run db status

# View history
uv run db history
```

### After Updates

When updating Tux:

```bash
git pull
uv sync
uv run db push                      # Apply new migrations
docker compose restart tux          # Restart bot
```

## Migration Files

Located in: `src/tux/database/migrations/versions/`

**Don't manually edit** migration files unless you know what you're doing.

## Docker Migrations

Migrations can run automatically on container startup:

```bash
# In .env
FORCE_MIGRATE=true                  # Auto-run migrations on start
USE_LOCAL_MIGRATIONS=true           # Use mounted migration files
```

## Troubleshooting

### Migration Fails

```bash
# Check what's wrong
uv run db status

# View specific migration
uv run db show head

# Check for conflicts
uv run db check
```

### Database Out of Sync

```bash
# Reset safely (via migrations)
uv run db reset

# Nuclear option (destroys data!)
uv run db nuke --force
uv run db push
```

## Related

- **[Database CLI Reference](../../reference/cli.md#database-management)**
- **[Developer Migration Guide](../../developer-guide/database/migrations.md)**

---

*See CLI reference for complete migration commands.*
