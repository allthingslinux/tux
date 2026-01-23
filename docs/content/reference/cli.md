---
title: CLI Reference
description: Complete reference for Tux command-line interface commands
tags:
  - cli
  - typer
  - commands
  - terminal
---

# CLI Reference

Tux provides a comprehensive command-line interface built with Typer. All commands are accessed via `uv run <command>`.

## Bot Commands

### `tux start`

Start the Discord bot.

```bash
uv run tux start
uv run tux start --debug  # Debug mode with verbose logging
```

### `tux version`

Show version information.

```bash
uv run tux version
```

## Database Commands

### Migration Management

```bash
# Initialize empty database with migrations
uv run db init

# Generate & apply migration (auto-name)
uv run db dev

# Generate & apply with custom name
uv run db dev --name "description"

# Create new migration file only
uv run db new "description"

# Apply all pending migrations
uv run db push

# Rollback one migration
uv run db downgrade -1

# Rollback to specific revision
uv run db downgrade <rev>
```

### Status & Inspection

```bash
# Show current revision and pending migrations
uv run db status

# Show current revision
uv run db current

# Show full migration history
uv run db history

# Show SQL for head revision
uv run db show head

# Validate migration files
uv run db check

# Show Alembic version
uv run db version
```

### Database Operations

```bash
# Check database connection
uv run db health

# List all database tables
uv run db tables

# Show database schema
uv run db schema

# Run custom database queries
uv run db queries

# Safe reset (downgrade to base, reapply all)
uv run db reset

# Complete wipe (destructive, requires confirmation)
uv run db nuke

# Nuclear reset + delete migration files
uv run db nuke --fresh

# Fix PostgreSQL sequence synchronization issues
uv run db fix-sequences

# Dry run mode (show what would be fixed without making changes)
uv run db fix-sequences --dry-run
```

#### `db fix-sequences`

Fixes PostgreSQL sequence synchronization issues that can occur after data restoration or manual database operations. This command resets all sequences to match the maximum ID value in their respective tables, preventing duplicate key violations.

**Options:**

- `--dry-run`, `-d` - Show what would be fixed without making changes

**When to use:**

- After restoring data from a backup
- After manual database operations that bypass sequences
- When encountering duplicate key violations on insert

## Testing Commands

```bash
# Quick tests (default, no coverage)
uv run test

# Full test suite with coverage
uv run test all

# Fast run (no coverage, explicit)
uv run test quick

# Fast tests only
uv run test fast

# Plain output (no colors/formatting)
uv run test plain

# Parallel test execution
uv run test parallel

# Run tests in specific file
uv run test file <path>

# Re-run last failed tests
uv run test last-failed

# Generate coverage report
uv run test coverage

# Generate HTML coverage report
uv run test html

# Run benchmark tests
uv run test benchmark
```

## Development Commands

```bash
# Run all quality checks (format, lint, type-check)
uv run dev all

# Run full pre-commit suite
uv run dev pre-commit

# Format code with ruff
uv run dev format

# Lint code (check only)
uv run dev lint

# Lint and auto-fix issues
uv run dev lint-fix

# Type checking with basedpyright
uv run dev type-check

# Lint docstrings with pydoclint
uv run dev lint-docstring

# Check docstring coverage
uv run dev docstring-coverage

# Clean build artifacts and caches
uv run dev clean
```

## Documentation Commands

```bash
# Local preview server
uv run docs serve

# Build documentation site
uv run docs build

# Lint documentation files
uv run docs lint

# Deploy to GitHub Pages (via Wrangler)
uv run docs deploy
```

### Wrangler Commands (Cloudflare Pages)

```bash
# Start Wrangler dev server
uv run docs wrangler-dev

# Deploy to Cloudflare Pages
uv run docs wrangler-deploy

# Rollback deployment
uv run docs wrangler-rollback

# List deployment versions
uv run docs wrangler-versions

# Tail deployment logs
uv run docs wrangler-tail

# List all deployments
uv run docs wrangler-deployments
```

## Configuration Commands

```bash
# Generate configuration example files
uv run config generate

# Validate the current configuration
uv run config validate
```

## AI/Cursor Commands

```bash
# Validate Cursor rules and commands
uv run ai validate-rules
```

## Common Workflows

### Initial Setup

```bash
# Install dependencies
uv sync

# Generate configuration files
uv run config generate
cp .env.example .env
cp config/config.json.example config/config.json

# Start database
docker compose up -d tux-postgres

# Initialize database
uv run db init

# Start bot
uv run tux start
```

### Development Workflow

```bash
# Make changes, then run quality checks
uv run dev all

# Run quick tests
uv run test quick

# Create and apply migration
uv run db dev --name "description"

# Validate Cursor rules
uv run ai validate-rules

# Run full pre-commit suite
uv run dev pre-commit

# Run full test suite
uv run test all
```

### Database Maintenance

```bash
# Check database health
uv run db health

# Check migration status
uv run db status

# Fix sequence synchronization issues
uv run db fix-sequences --dry-run  # Preview changes
uv run db fix-sequences            # Apply fixes
```

## See Also

- [AGENTS.md](../../../AGENTS.md) - Project overview and standards
- [Database Management](../../selfhost/manage/database.md) - Database management guide
- [Development Setup](../../developer/tutorials/development-setup.md) - Development environment setup
