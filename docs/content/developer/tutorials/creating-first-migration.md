---
title: Creating Your First Migration
tags:
  - developer-guide
  - tutorials
  - database
  - migrations
---

# Creating Your First Migration

This tutorial walks you through creating your first database migration in Tux. You'll learn how to modify models and generate migrations that safely update your database schema.

## Prerequisites

Before starting, ensure you have:

- Tux repository cloned locally
- Development environment set up ([Development Setup](development-setup.md))
- Database running (Docker Compose or local PostgreSQL)
- Basic understanding of SQLModel models

## Step 1: Understand the Migration Workflow

Tux uses **Alembic** for database migrations. The workflow is:

1. **Modify models** - Change your SQLModel classes
2. **Generate migration** - Create migration file from model changes
3. **Review migration** - Check the generated SQL
4. **Apply migration** - Run migration against database
5. **Commit migration** - Add migration file to git

## Step 2: Set Up Your Development Environment

### Start Database

**Using Docker Compose:**

```bash
# Start PostgreSQL
docker compose up -d tux-postgres

# Wait for database to be ready
docker compose exec tux-postgres pg_isready -U tuxuser
```

**Using Local PostgreSQL:**

```bash
# Ensure PostgreSQL is running
sudo systemctl status postgresql
```

### Enable Migration Mount (Docker Only)

If using Docker Compose for development:

```bash
# Copy override example to enable migration mount
cp compose.override.yaml.example compose.override.yaml
```

This allows you to test migrations without rebuilding the Docker image.

## Step 3: Modify a Model

Let's add a new field to an existing model. For this example, we'll add an `email` field to a hypothetical `User` model:

```python
# src/tux/database/models/user.py
from sqlmodel import Field
from tux.database.models.base import BaseModel

class User(BaseModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: str  # ← New field we're adding
    active: bool = Field(default=True)
```

**Important:** Only modify models in `src/tux/database/models/`. Don't edit migration files directly.

## Step 4: Generate Migration

Use the database CLI to generate a migration:

```bash
# Generate and apply migration with auto-generated name
uv run db dev

# Or specify a descriptive name
uv run db dev --name "add email to user"
```

**What happens:**

1. Alembic compares current models to database schema
2. Detects the new `email` field
3. Generates migration file in `src/tux/database/migrations/versions/`
4. Applies migration to your database automatically

**Migration file created:**

```text
src/tux/database/migrations/versions/2025_01_15_1430-abc123def456_add_email_to_user.py
```

## Step 5: Review Generated Migration

Always review the generated migration before committing:

```bash
# View migration SQL
uv run db show head

# Or read the file directly
cat src/tux/database/migrations/versions/2025_01_15_1430-abc123def456_add_email_to_user.py
```

**Example migration content:**

```python
"""add email to user

Revision ID: abc123def456
Revises: xyz789ghi012
Create Date: 2025-01-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = 'xyz789ghi012'
branch_labels = None
depends_on = None

def upgrade():
    # Add email column
    op.add_column('user', sa.Column('email', sa.String(), nullable=False))

def downgrade():
    # Remove email column
    op.drop_column('user', 'email')
```

**Check for:**

- ✅ Correct column type (`sa.String()`)
- ✅ Correct nullable setting (`nullable=False` or `nullable=True`)
- ✅ Correct table name (`'user'`)
- ✅ Proper downgrade function (for rollback)

## Step 6: Test Migration

### Verify Migration Applied

```bash
# Check migration status
uv run db status

# Should show:
# Current revision: abc123def456 (head)
# No pending migrations
```

### Test Application

Start the bot and verify it works with the new schema:

```bash
# Start bot (if using Docker)
docker compose up -d tux

# Or run locally
uv run tux start --debug
```

### Test Rollback (Optional)

Test that rollback works:

```bash
# Rollback one migration
uv run db downgrade -1

# Verify column removed
uv run db status

# Re-apply migration
uv run db push
```

## Step 7: Handle Edge Cases

### Making Field Optional

If you want to make a field optional (nullable):

```python
class User(BaseModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: str | None = None  # Optional field
```

**Migration will include:**

```python
def upgrade():
    op.add_column('user', sa.Column('email', sa.String(), nullable=True))
```

### Adding Default Value

If adding a field with a default:

```python
class User(BaseModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: str = Field(default="")
```

**Migration will include:**

```python
def upgrade():
    op.add_column('user', sa.Column('email', sa.String(), nullable=False, server_default=''))
```

### Adding Index

If adding an indexed field:

```python
class User(BaseModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
```

**Migration will include:**

```python
def upgrade():
    op.add_column('user', sa.Column('email', sa.String(), nullable=False))
    op.create_index('ix_user_email', 'user', ['email'], unique=True)
```

## Step 8: Commit Migration

Once you've reviewed and tested:

```bash
# Stage migration file
git add src/tux/database/migrations/versions/

# Commit with descriptive message
git commit -m "feat(database): add email field to user model"
```

**Best practices:**

- ✅ Commit migration file with model changes in same PR
- ✅ Use conventional commit format
- ✅ Include migration file in PR review
- ✅ Test migration on clean database before merging

## Common Issues and Solutions

### "No changes detected"

**Problem:** Migration not generated even after model changes.

**Solutions:**

```bash
# Check if models are imported
# Ensure models are registered in src/tux/database/models/__init__.py

# Try with explicit name
uv run db dev --name "add email field"

# Check for syntax errors in models
uv run basedpyright src/tux/database/models/
```

### "Migration file already exists"

**Problem:** Migration file conflicts with existing one.

**Solutions:**

```bash
# Check migration status
uv run db status

# If migration not applied, delete file and regenerate
rm src/tux/database/migrations/versions/conflicting_file.py
uv run db dev --name "add email field"
```

### "Database out of sync"

**Problem:** Database schema doesn't match models.

**Solutions:**

```bash
# Check what's different
uv run db status

# Apply pending migrations
uv run db push

# If still out of sync, reset (⚠️ destroys data!)
uv run db reset
```

## Next Steps

Now that you've created your first migration:

- **Learn more:** Read [Database Migrations](../concepts/database/migrations.md)

## Related Documentation

- **[Database Migrations](../concepts/database/migrations.md)** - Complete migration reference
- **[Database Models](../concepts/database/models.md)** - Model definition guide
- **[Development Setup](development-setup.md)** - Setting up development environment
