---
title: Database Migrations
tags:
  - developer-guide
  - concepts
  - database
  - migrations
---

# Database Migrations

Tux uses **Alembic** for database schema migrations, providing version control for PostgreSQL schema changes. Migrations enable safe, incremental database evolution while maintaining data integrity across environments.

## Overview

The migration system provides:

- **Version control** for schema changes
- **Safe rollbacks** to previous schema versions
- **Team collaboration** through committed migration files
- **Production safety** with automatic migration checks
- **Environment consistency** across development, staging, and production

Migrations are automatically applied on bot startup, ensuring your database is always up-to-date. If migrations fail, the bot will not start, preventing inconsistent database states.

## Architecture

### Migration Environment Configuration

Alembic migrations are configured with production-ready features:

- **Async-to-sync URL conversion**: Automatically converts async database URLs for Alembic compatibility
- **Comprehensive schema comparison**: Detects table operations, column changes, constraints, and indexes
- **Batch rendering**: Better ALTER TABLE support for complex migrations
- **Transaction safety**: Each migration runs in its own transaction
- **Retry logic**: Automatic retry with exponential backoff for Docker/CI environments
- **Empty migration prevention**: Prevents generation of empty migration files

### Model Registration Process

All models are registered with SQLAlchemy metadata to ensure complete coverage in migration detection and prevent garbage collection during migration generation.

### Migration Modes

Alembic supports two execution modes:

- **Online mode** (database connection): Used for development, staging, and production
- **Offline mode** (SQL generation): Used for code review, manual DBA execution, and CI/CD pipelines

### Database CLI Integration

Tux provides a comprehensive database CLI (`uv run db`) that wraps Alembic commands with:

- Workflow optimization
- Safety features
- Rich output formatting
- Integration with service initialization

## Key Concepts

### Async-to-Sync URL Conversion

Alembic requires synchronous database drivers, so async URLs (`postgresql+psycopg_async://`) are automatically converted to sync format (`postgresql+psycopg://`) for compatibility.

### Retry Logic for Docker/CI

Migrations include automatic retry logic with configurable attempts and delays to handle container startup timing and infrastructure resilience:

- **5 retry attempts** with 2-second delays
- Handles Docker container startup delays
- Provides resilience for transient network issues

### Empty Migration Prevention

Alembic prevents generation of empty migration files to maintain clean history and avoid meaningless commits. If no schema changes are detected, no migration file is created.

### Transaction per Migration

Each migration runs in its own transaction ensuring:

- **Atomicity**: Each migration succeeds or fails completely
- **Individual rollback**: Can rollback specific migrations
- **Isolation**: Migrations don't interfere with each other
- **Easier debugging**: Clear transaction boundaries

### Schema Change Detection

Alembic automatically detects:

- Table operations (create, drop, alter)
- Column changes (add, remove, modify)
- Constraints (foreign keys, unique, check)
- Indexes (create, drop)
- Server defaults

## Workflow by Role

### 👨‍💻 Developers (Contributing to Tux)

#### Understanding Migration Workflow

**Key Concept:** The initial migration is **already in the repository**. You don't create it - you apply it.

**Migration Lifecycle:**

1. **Project Start** (one-time): Maintainer runs `db init` → Creates initial migration → Commits to repo
2. **Schema Changes**: Developer modifies models → Runs `db dev` → Creates new migration → Commits to repo
3. **New Developers**: Clone repo → Run `db push` → Applies all existing migrations

**Important:** `db init` checks for existing migration files and will **fail** if any exist. This prevents accidentally recreating migrations that are already committed.

#### Initial Setup

**For New Developers (Existing Project):**

```bash
# 1. Clone and setup
git clone <repo>
cd tux
uv sync

# 2. Apply existing migrations (migrations are already in repo)
uv run db push
# Applies all migrations from the repo to your local database
```

**For Project Maintainers (Creating Initial Migration):**

```bash
# ONLY run this when creating the FIRST migration for a brand new project
# This should only happen ONCE in the project's lifetime
uv run db init
# Creates initial migration from models and applies it
# THEN commit this migration file to the repo!
```

**Important Notes:**

- ✅ **Initial migration IS committed to repo** - it's part of the codebase
- ✅ **New developers use `db push`** - not `db init`
- ❌ **`db init` will fail** if migration files already exist (by design - prevents duplicate migrations)
- ✅ **Only use `db init`** when starting a completely new project with zero migrations

#### Making Schema Changes

##### Step 1: Modify Models

```python
# src/tux/database/models/models.py
class User(BaseModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: str  # ← Added new field
```

##### Step 2: Generate Migration

```bash
# Option A: Create + apply immediately (like Prisma migrate dev)
uv run db dev --name "add email to user"

# Option B: Create only, review later
uv run db dev --create-only --name "add email to user"
```

##### Step 3: Review Migration File

```bash
# Check what was generated
uv run db show head

# Or manually review:
cat src/tux/database/migrations/versions/YYYY_MM_DD_HHMM-<revision>_add_email_to_user.py
```

##### Step 4: Apply Migration (if created only)

```bash
uv run db push
```

##### Step 5: Commit Migration File

```bash
git add src/tux/database/migrations/versions/
git commit -m "feat(database): add email field to user model"
```

#### Common Developer Commands

```bash
# Development workflow (like Prisma migrate dev)
uv run db dev                    # Create + apply with auto name
uv run db dev --name "message"  # Create + apply with custom name
uv run db dev --create-only     # Create only, don't apply

# Apply existing migrations
uv run db push                   # Apply all pending migrations

# Check status
uv run db status                 # Show current revision and pending
uv run db history               # Show full migration history
uv run db check                 # Validate migration files

# Troubleshooting
uv run db reset                 # Reset DB and reapply all migrations
uv run db nuke                  # Nuclear reset (destroys all data!)
uv run db nuke --fresh          # Nuclear reset and reset to initial migration
uv run db downgrade -1          # Rollback one migration
```

#### Best Practices for Developers

✅ **DO:**

- Always review generated migrations before committing
- Use descriptive migration names (`--name "add user email field"`)
- Test migrations locally before pushing
- Commit migration files with model changes in same PR
- Run `uv run db check` before committing

❌ **DON'T:**

- Edit migration files after they're applied (create new migration instead)
- Delete migration files that have been applied
- Skip reviewing auto-generated migrations
- Commit empty migrations (auto-prevented by system)

### 🏠 Self-Hosters (Running Tux)

#### First-Time Setup

##### Option A: Let Bot Auto-Migrate (Recommended)

```bash
# 1. Start services
docker compose up -d

# 2. Bot automatically runs migrations on first startup
# Bot will NOT start if migrations fail - check logs:
docker compose logs tux | grep -i -E "(migration|error|failed)"

# If migrations fail, bot exits with error. Fix issues and restart.
```

##### Option B: Manual Migration (More Control)

```bash
# 1. Start database only
docker compose up -d tux-postgres

# 2. Wait for DB to be ready
docker compose exec tux-postgres pg_isready -U tuxuser

# 3. Run migrations manually
docker compose exec tux uv run db push

# 4. Start bot
docker compose up -d tux
```

#### Updating Tux (Applying New Migrations)

**Standard Update Workflow:**

```bash
# 1. Backup database (IMPORTANT!)
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup_$(date +%Y%m%d).sql

# 2. Pull latest code
git pull origin main  # or your branch

# 3. Update dependencies
uv sync

# 4. Apply new migrations
uv run db push

# 5. Restart bot
docker compose restart tux
```

**Or Let Bot Auto-Migrate:**

```bash
# 1. Backup database
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup.sql

# 2. Pull and restart
git pull origin main
uv sync
docker compose restart tux

# Bot will auto-apply migrations on startup
# Bot will NOT start if migrations fail - check logs:
docker compose logs -f tux | grep -i -E "(migration|error|failed)"

# If migrations fail, bot exits. Fix issues and restart.
```

#### Self-Hoster Best Practices

✅ **DO:**

- **Always backup before updates** (migrations can fail)
- Monitor migration logs on startup
- Use `uv run db status` to check migration state
- Keep migration files in sync with code version
- Test updates in staging first if possible

❌ **DON'T:**

- Skip backups before updates
- Manually edit migration files
- Run migrations while bot is running (bot handles this)
- Delete migration files from your installation

## 🐳 Docker Migration Setup

### Docker Compose Override Pattern

Tux uses the **Docker Compose override pattern** - a standard approach used by Django, Rails, and other major projects. This ensures production deployments work out-of-the-box while providing flexibility for developers and customizers.

### How It Works

**Production (Default):**

- `compose.yaml` has **no migration mount** by default
- Migrations come from the Docker image (baked in during build)
- Works immediately for users without source code
- Always matches the image version

**Development/Customization (Optional):**

- Copy `compose.override.yaml.example` to `compose.override.yaml`
- Enables migration mount for faster iteration
- Docker Compose automatically merges override files
- Override file is gitignored (won't be committed)

### Quick Reference: Docker Migration Scenarios

| Scenario | Has Source? | Override File | Migration Source | Result |
|----------|-------------|---------------|-----------------|--------|
| Production, no source | ❌ No | ❌ None | Image migrations | ✅ **WORKS** |
| Production, old source | ⚠️ Old | ❌ None | Image migrations | ✅ **WORKS** |
| Development, has source | ✅ Yes | ✅ Exists | Local mount | ✅ **WORKS** |
| Customization, fork | ✅ Yes | ✅ Exists | Local mount (custom) | ✅ **WORKS** |
| Production, override exists | ❌ No | ✅ Exists | Image migrations | ✅ **WORKS** (override ignored if no source) |

### Production Setup (No Source Code)

**Default behavior - works immediately:**

```bash
# Download compose.yaml
curl -O https://raw.githubusercontent.com/allthingslinux/tux/main/compose.yaml

# Start services - migrations come from image
docker compose up -d
```

**No configuration needed** - migrations are automatically included in the Docker image.

### Development Setup (With Source Code)

**Enable migration mount for faster iteration:**

```bash
# Clone repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Copy override example
cp compose.override.yaml.example compose.override.yaml

# Start services - migrations come from local mount
docker compose up -d
```

**What this enables:**

- Test migration changes without rebuilding image
- Faster development iteration
- Local migration files override image migrations

### Customization Setup (Fork with Custom Models)

**For users who fork and add custom models:**

```bash
# Fork repository, add custom models
git clone https://github.com/yourusername/tux.git
cd tux

# Create custom migrations
uv run db dev --name "add custom features"

# Enable override for iteration
cp compose.override.yaml.example compose.override.yaml

# Build and run
docker compose build
docker compose up -d
```

**Override file contents:**

```yaml
services:
  tux:
    volumes:
      # Mount migrations for faster development/customization iteration
      # Without this, migrations come from the Docker image (production behavior)
      - ./src/tux/database/migrations:/app/src/tux/database/migrations:ro
```

### Migration File Resolution

When migration files exist in multiple locations:

1. **Mounted volume** (if override exists and source available) - **HIGHEST PRIORITY**
2. **Image migrations** (if no mount or mount is empty) - **FALLBACK**

**Behavior:**

- No override file = uses image migrations ✅
- Override file exists + source available = uses local mount ✅
- Override file exists + no source = uses image migrations ✅ (graceful fallback)

### Why This Pattern?

**Benefits:**

- ✅ **Production-first**: Works out-of-the-box for most common use case
- ✅ **Developer-friendly**: One command to enable dev features
- ✅ **Customizer-friendly**: Easy to enable for forks/patches
- ✅ **Standard pattern**: Familiar to Docker users
- ✅ **No confusion**: Clear separation between prod and dev
- ✅ **Git-safe**: Override file is gitignored, example is committed

**Standard Practice:**

This pattern is used by:

- Django (django-compose pattern)
- Rails (docker-compose override)
- Node.js projects (compose.override.yaml)
- Most Docker-based projects

### Troubleshooting Docker Migrations

#### Migrations Not Found

**Check if override file exists:**

```bash
# If override exists but source is missing, remove it
rm compose.override.yaml

# Restart services
docker compose restart tux
```

#### Using Wrong Migrations

**Verify migration source:**

```bash
# Check what migrations are being used
docker compose exec tux ls -la /app/src/tux/database/migrations/versions/

# If empty or wrong, check override file
cat compose.override.yaml

# Remove override to use image migrations
rm compose.override.yaml
docker compose restart tux
```

#### Development Changes Not Reflecting

**Ensure override file exists:**

```bash
# Copy override example if missing
cp compose.override.yaml.example compose.override.yaml

# Restart services
docker compose restart tux
```

## Troubleshooting

### Migration Fails on Startup (Bot Won't Start)

```bash
# 1. Bot exits if migrations fail - check logs for error
docker compose logs tux | grep -i -E "(migration|error|failed)"

# 2. Check migration status manually
docker compose exec tux uv run db status

# 3. View migration history
docker compose exec tux uv run db history

# 4. Try running migrations manually
docker compose exec tux uv run db push

# 5. If migrations still fail, restore backup and investigate
docker compose exec -T tux-postgres psql -U tuxuser tuxdb < backup.sql

# 6. After fixing issues, restart bot
docker compose restart tux
```

### Database Out of Sync

```bash
# Check schema validation
docker compose exec tux uv run db schema

# If validation fails, you may need to reset (DESTRUCTIVE!)
# Backup first!
docker compose exec tux-postgres pg_dump -U tuxuser tuxdb > backup.sql
docker compose exec tux uv run db reset
```

### Migration Files Missing

```bash
# If migration files are missing, pull latest code
git pull origin main

# Then apply migrations
uv run db push
```

### "Can't generate migration"

```bash
# Check if models changed
git diff src/tux/database/models/

# Try with explicit name
uv run db dev --name "descriptive name"

# Check for empty migration (should be prevented)
uv run db check
```

### "Migration file not found"

```bash
# Pull latest code
git pull origin main

# Apply migrations
uv run db push
```

## Migration File Management

### File Naming Convention

Current format: `YYYY_MM_DD_HHMM-<revision>_<slug>.py`

Example: `2025_12_01_2053-55296ad22e23_initial_schema.py`

### Migration File Lifecycle

1. **Created**: Developer runs `db dev`
2. **Reviewed**: Developer checks generated SQL
3. **Applied**: Developer runs `db push` (or bot auto-applies)
4. **Committed**: Migration file committed to git
5. **Deployed**: Self-hosters pull and apply
6. **Never Deleted**: Migration files are permanent history

### Empty Migration Prevention in Migration Files

The system **automatically prevents** empty migrations:

- If no schema changes detected, migration file is not created
- See `process_revision_directives` in `env.py`

## Comparison: Prisma vs Alembic Workflow

| Task | Prisma | Alembic (Tux) |
|------|--------|---------------|
| Create migration | `prisma migrate dev` | `uv run db dev` |
| Apply migrations | Auto on `migrate dev` | Auto on startup OR `uv run db push` |
| Review migrations | Check generated SQL | Check Python file in `versions/` |
| Migration files | Committed to git | Committed to git |
| Rollback | `prisma migrate resolve` | `uv run db downgrade -1` |
| Status | `prisma migrate status` | `uv run db status` |
| Reset DB | `prisma migrate reset` | `uv run db reset` |

## Key Takeaways

### For Developers

1. **Workflow is similar to Prisma**: `db dev` ≈ `prisma migrate dev`
2. **Always review migrations**: Auto-generated code needs review
3. **Commit migration files**: They're part of the codebase
4. **Test locally first**: Don't push untested migrations

### For Self-Hosters

1. **Bot auto-migrates**: Usually no manual steps needed
2. **Backup before updates**: Always!
3. **Monitor logs**: Check migration success on startup
4. **Production-ready by default**: No migration mount needed
5. **Use override for customization**: Copy `compose.override.yaml.example` if customizing

### Migration Philosophy

- **Migrations are code**: Review and test like any code
- **Migrations are history**: Never delete applied migrations
- **Migrations are safe**: Each runs in its own transaction
- **Migrations are required**: Bot will not start if migrations fail

## Related Topics

- [Database Models](models.md) - Model definitions that drive migrations
- [Database Service](service.md) - Database service used by migrations
- [Database Controllers](controllers.md) - Database controllers using migrated models
- [Database CLI Reference](../../../reference/cli.md) - Complete CLI command reference
