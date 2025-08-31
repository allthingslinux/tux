# Database Lifecycle Guide

This guide explains the complete database lifecycle in Tux, from development to production, covering how database changes flow through the system and how different user types manage their databases.

## 🔄 **Database Lifecycle Overview**

```
Development → Testing → Migration Creation → Production Deployment → Self-Hoster Updates
     ↓              ↓            ↓                ↓                    ↓
  Model Changes → Test DB → Alembic Revision → Release → Migration Application
```

## 👨‍💻 **For Contributors (Development Workflow)**

### 1. **Making Database Changes**

When you modify database models in `src/tux/database/models/`:

```python
# Example: Adding a new field to Guild model
class Guild(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, sa_type=BigInteger)
    # ... existing fields ...
    
    # NEW FIELD - This will require a migration
    new_feature_enabled: bool = Field(default=False)
```

### 2. **Testing Your Changes**

```bash
# Start with a clean test database
make db-reset

# Run tests to ensure your changes work
make test

# Test migrations specifically
make test-migrations
```

### 3. **Creating Migration Files**

**IMPORTANT**: Never manually edit migration files. Always use Alembic to generate them.

```bash
# Generate a new migration
make db-revision

# This creates a file like: src/tux/database/migrations/versions/001_add_new_feature.py
```

### 4. **Reviewing Generated Migrations**

Check the generated migration file:

```python
# src/tux/database/migrations/versions/001_add_new_feature.py
"""add new feature

Revision ID: 001
Revises: 000
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # ✅ GOOD: Alembic generated this automatically
    op.add_column('guild', sa.Column('new_feature_enabled', sa.Boolean(), nullable=False, server_default='false'))

def downgrade() -> None:
    # ✅ GOOD: Alembic generated rollback automatically
    op.drop_column('guild', 'new_feature_enabled')
```

**⚠️ WARNING**: If the migration looks wrong or incomplete, DO NOT edit it manually. Instead:
1. Delete the migration file
2. Fix your model
3. Regenerate the migration

### 5. **Testing Migrations**

```bash
# Test the migration on a clean database
make db-reset
make db-upgrade

# Verify your changes work
make test

# Test rollback (if needed)
make db-downgrade 1  # Downgrade 1 revision
```

### 6. **Committing Changes**

```bash
# Include both model changes AND migration files
git add src/tux/database/models/your_model.py
git add src/tux/database/migrations/versions/001_add_new_feature.py

git commit -m "feat: add new_feature_enabled to Guild model

- Add boolean field for new feature toggle
- Include Alembic migration 001_add_new_feature
- Tested migration up/down successfully"
```

## 🏭 **For Production Deployments**

### 1. **Release Process**

When a new Tux version is released:

1. **Database migrations are included** in the release
2. **Bot startup automatically runs migrations** in production
3. **Self-hosters get the new schema** when they update

### 2. **Automatic Migration on Startup**

The bot automatically runs migrations in production:

```python
# From src/tux/core/bot.py
async def setup(self) -> None:
    # ... other setup ...
    await self._setup_database()
    # Ensure DB schema is up-to-date in non-dev
    await upgrade_head_if_needed()  # ← This runs migrations automatically
```

## 🏠 **For Self-Hosters (Database Management)**

### 1. **Initial Database Setup (First Time)**

**For new self-hosters setting up Tux for the first time:**

```bash
# 1. Start the database
make prod

# 2. Wait for database to be ready (5-10 seconds)
sleep 5

# 3. Apply the baseline migration (this establishes version tracking)
uv run alembic -c alembic.ini upgrade head

# 4. Verify setup
uv run alembic -c alembic.ini current
# Should show: 588f4746c621 (head)
```

**Important Notes:**
- The baseline migration establishes Alembic's version tracking
- Tables are created automatically by SQLModel when the bot connects
- No manual table creation needed

### 2. **Understanding Migration Flow**

```
Tux Update → New Migration Files → Bot Startup → Automatic Migration → New Features Available
     ↓              ↓                    ↓              ↓                    ↓
  Pull Changes → Get New Models → Connect to DB → Apply Changes → Use New Features
```

### 3. **Updating Your Tux Installation**

```bash
# 1. Pull the latest changes
git pull origin main

# 2. Update your bot (Docker or local)
make docker-prod  # or make prod for local

# 3. The bot automatically applies migrations on startup
```

### 4. **What Happens During Updates**

When you update Tux:

1. **New migration files are downloaded** with your git pull
2. **Bot detects schema version mismatch** on startup
3. **Migrations run automatically** before bot connects to Discord
4. **Database schema is updated** to match new models
5. **Bot starts normally** with new features available

### 5. **Migration Safety Features**

- **Automatic backups**: Alembic creates backup tables for complex changes
- **Transaction safety**: All migrations run in transactions
- **Rollback support**: Failed migrations automatically rollback
- **Version tracking**: Database tracks current schema version

### 6. **Manual Migration Control (Advanced)**

If you need manual control over migrations:

```bash
# Check current database version
make db-current

# See available migrations
make db-history

# Manually run migrations (usually not needed)
make db-upgrade

# Rollback if needed (use with caution)
make db-downgrade 1
```

## 🚨 **Common Scenarios & Solutions**

### Scenario 1: **Bot Won't Start After Update**

**Symptoms**: Bot fails to start, database connection errors

**Likely Cause**: Migration failure or database version mismatch

**Solution**:
```bash
# Check database status
make db-current

# Check bot logs for migration errors
docker compose logs tux

# If migration failed, try manual upgrade
make db-upgrade

# If still failing, check database permissions
```

### Scenario 2: **New Features Not Working**

**Symptoms**: Bot starts but new commands/features don't work

**Likely Cause**: Migration didn't complete successfully

**Solution**:
```bash
# Verify migration status
make db-current

# Check if all tables exist
make db-tables

# Force migration if needed
make db-upgrade
```

### Scenario 3: **Database Corruption or Migration Issues**

**Symptoms**: Strange errors, missing data, or migration failures

**Solution**:
```bash
# 1. Backup your database first!
pg_dump your_database > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check migration history
make db-history

# 3. Try to fix the migration
make db-upgrade

# 4. If all else fails, restore from backup and re-run migrations
```

### Scenario 4: **Bot Joins New Server**

**What Happens**: Bot automatically initializes the server in the database

**Code**: ```python
@commands.Cog.listener()
async def on_guild_join(self, guild: discord.Guild) -> None:
    await self.db.guild.insert_guild_by_id(guild.id)
```

**Result**: New server gets:
- Basic guild record
- Default configuration
- All feature tables initialized
- Ready for immediate use

### Scenario 5: **Empty Migration Generated**

**Symptoms**: `alembic revision --autogenerate -m "baseline"` creates a migration with `def upgrade(): pass`

**Likely Cause**: This is **correct behavior** when the database schema already matches the models

**Solution**: This is expected! The empty migration represents the current state:
```bash
# Apply the baseline migration
make db-upgrade

# Verify it's working
make db-current
```

### Scenario 6: **psycopg3 Compatibility Issues**

**Symptoms**: `ModuleNotFoundError: No module named 'psycopg2'` or connection errors

**Likely Cause**: Incorrect database URL format or driver mismatch

**Solution**:
```bash
# ✅ Use correct psycopg3 URLs
postgresql+psycopg_async://user:pass@host:port/db  # For async operations
postgresql+psycopg://user:pass@host:port/db        # For sync operations (Alembic)

# ❌ Don't use deprecated drivers
postgresql+psycopg2://user:pass@host:port/db      # Old driver
postgresql+asyncpg://user:pass@host:port/db        # Incompatible with psycopg3
```

## 🔧 **Database Maintenance**

### 1. **Regular Backups**

```bash
# PostgreSQL backup
pg_dump your_database > tux_backup_$(date +%Y%m%d).sql

# SQLite backup (if using SQLite)
cp tux.db tux_backup_$(date +%Y%m%d).db
```

### 2. **Monitoring Database Health**

```bash
# Check database status
make db-health

# View table sizes
make db-stats

# Check for long-running queries
make db-queries
```

### 3. **Performance Optimization**

```bash
# Analyze table statistics
make db-analyze

# Reindex tables if needed
make db-reindex

# Vacuum database (PostgreSQL)
make db-vacuum
```

## 🔧 **Technical Setup & Compatibility**

### **Database Drivers & Compatibility**

Tux uses **psycopg3** (the latest PostgreSQL driver) for optimal performance and compatibility:

```bash
# ✅ CORRECT: psycopg3 async for bot operations
postgresql+psycopg_async://user:pass@host:port/db

# ✅ CORRECT: psycopg3 sync for Alembic migrations  
postgresql+psycopg://user:pass@host:port/db

# ❌ DEPRECATED: psycopg2 (old driver)
postgresql+psycopg2://user:pass@host:port/db

# ❌ DEPRECATED: asyncpg (incompatible with psycopg3)
postgresql+asyncpg://user:pass@host:port/db
```

**Important Notes:**
- **Package name**: Install `psycopg[binary]` (not `psycopg3`)
- **Import**: Use `import psycopg` (not `import psycopg3`)
- **URL format**: The `+psycopg` and `+psycopg_async` parts are SQLAlchemy dialect specifiers
- **Connection options**: psycopg3 uses `options` parameter instead of `server_settings`

### **Environment Configuration**

Your `.env` file should contain:

```bash
# Simplified configuration
DATABASE_URL=postgresql://tuxuser:tuxpass@localhost:5432/tuxdb

# The bot automatically detects context (development/production)
```

### **Alembic Configuration**

The `alembic.ini` file includes a placeholder URL that gets overridden by `env.py`:

```ini
# Database URL - will be overridden by env.py based on environment
sqlalchemy.url = postgresql://placeholder
```

This ensures Alembic can always find a URL to work with, even if it's just a placeholder.

### **psycopg3 Connection Options**

When using psycopg3, connection options are specified differently than with psycopg2:

```python
# ✅ CORRECT: psycopg3 connection options
connect_args = {
    "options": "-c timezone=UTC -c application_name=TuxBot -c statement_timeout=60s"
}

# ❌ INCORRECT: psycopg2-style options (not supported in psycopg3)
connect_args = {
    "server_settings": {
        "timezone": "UTC",
        "application_name": "TuxBot"
    }
}
```

**Key Differences from psycopg2:**
- Use `options` string instead of `server_settings` dict
- Format: `-c key=value -c key2=value2`
- Common options: `timezone`, `application_name`, `statement_timeout`, `idle_in_transaction_session_timeout`

### **psycopg3 Import and Usage Patterns**

**Correct Import Pattern:**
```python
# ✅ CORRECT: Import psycopg (not psycopg3)
import psycopg

# ✅ CORRECT: For async operations
from psycopg import AsyncConnection

# ✅ CORRECT: For sync operations  
from psycopg import Connection
```

**Installation:**
```bash
# ✅ CORRECT: Install psycopg with binary support
pip install "psycopg[binary]"

# ❌ INCORRECT: Don't install psycopg3 (package doesn't exist)
pip install psycopg3
```

**Connection String Examples:**
```python
# For async operations (bot runtime)
DATABASE_URL = "postgresql+psycopg_async://user:pass@host:port/db"

# For sync operations (Alembic migrations)
DATABASE_URL = "postgresql+psycopg://user:pass@host:port/db"

# Base format (gets converted by SQLAlchemy)
DATABASE_URL = "postgresql://user:pass@host:port/db"
```

## 📋 **Migration Best Practices**

### For Contributors

1. **Always test migrations** on clean databases
2. **Never edit migration files manually**
3. **Include both up and down migrations**
4. **Test rollback scenarios**
5. **Document breaking changes**

### For Self-Hosters

1. **Backup before major updates**
2. **Test updates on staging first** (if possible)
3. **Monitor migration logs** during updates
4. **Keep database credentials secure**
5. **Regular maintenance and backups**

## 🆘 **Getting Help**

### When Migrations Fail

1. **Check the logs** for specific error messages
2. **Verify database permissions** and connectivity
3. **Check migration history** with `make db-history`
4. **Look for similar issues** in GitHub issues
5. **Ask for help** in Discord with logs and error details

### Useful Commands Reference

```bash
# Database status
make db-current          # Show current version
make db-history         # Show migration history
make db-health          # Check database health

# Migration control
make db-upgrade         # Apply all pending migrations
make db-downgrade N     # Rollback N migrations
make db-revision        # Create new migration

# Database management
make db-reset           # Reset database (WARNING: destroys data)
make db-tables          # List all tables
make db-stats           # Show database statistics
```

## 🔄 **Migration Lifecycle Summary**

```
Development → Testing → Migration Creation → Code Review → Release → Self-Hoster Update
     ↓            ↓            ↓               ↓           ↓           ↓
  Model Change → Test DB → Alembic File → Pull Request → Tagged Release → Git Pull
     ↓            ↓            ↓               ↓           ↓           ↓
  Local Test → Migration Test → Code Review → Merge to Main → Release → Auto-Migration
```

This lifecycle ensures that:
- **Contributors** can safely develop and test database changes
- **Production deployments** automatically handle schema updates
- **Self-hosters** get seamless updates without manual intervention
- **Database integrity** is maintained throughout the process

## ✅ **Complete Setup Verification**

After following the setup process, verify everything is working:

```bash
# 1. Check database connection
uv run python -c "
from tux.database.service import DatabaseService
import asyncio
service = DatabaseService()
asyncio.run(service.connect())
print('✅ Database connection successful')
"

# 2. Verify migration status
uv run alembic -c alembic.ini current
# Should show: 588f4746c621 (head)

# 3. Check database health
uv run python -c "
from tux.database.service import DatabaseService
import asyncio
service = DatabaseService()
asyncio.run(service.connect())
health = asyncio.run(service.health_check())
print('✅ Database health:', health)
"

# 4. Test table creation (should be instant since tables exist)
uv run python -c "
from tux.database.service import DatabaseService
import asyncio
service = DatabaseService()
asyncio.run(service.connect())
asyncio.run(service.create_tables())
print('✅ Tables verified successfully')
"
```

**Expected Results:**
- All commands should complete without errors
- Migration status should show the baseline revision
- Database health should show all tables as accessible
- Table creation should be instant (tables already exist)

---

**Last Updated**: 2025-08-28
**Version**: v0.1.0
**Related Docs**: [SETUP.md](SETUP.md), [DEVELOPER.md](DEVELOPER.md), [Database Optimization Guide](database-optimization.md)
