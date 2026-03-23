# CLI command reference

## Code quality

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

## Bot CLI

```bash
uv run tux start            # Start bot
uv run tux start --debug    # Debug mode
uv run tux version          # Show version information
```

## Documentation

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

## Configuration

```bash
uv run config generate      # Generate configuration example files
uv run config validate      # Validate the current configuration
```

## Cursor

```bash
uv run ai validate-rules   # Validate Cursor rules and commands
```

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
