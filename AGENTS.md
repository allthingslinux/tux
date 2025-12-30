# AGENTS.md

**Tux** is an all-in-one open source Discord bot for the [All Things Linux](https://allthingslinux.org) community.

## Tech Stack

**Core:** Python 3.13+ • discord.py • PostgreSQL • SQLModel • Docker
**Tools:** uv • ruff • basedpyright • pytest • loguru • sentry-sdk • httpx • Zensical

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
uv sync
uv run config generate
cp .env.example .env && cp config/config.toml.example config/config.toml
uv run tux start
```

## Project Structure

```text
tux/
├── src/tux/                    # Main source
│   ├── core/                   # Bot core
│   ├── database/               # Models & migrations
│   ├── services/               # Business logic
│   ├── modules/                # Commands (cogs)
│   ├── plugins/                # Plugin system
│   ├── ui/                     # Embeds & views
│   ├── shared/                 # Utils & config
│   └── main.py                 # Entry point
├── scripts/                    # CLI scripts
├── tests/                      # Tests (core/database/services/shared/modules)
├── docs/                       # Zensical documentation
├── docker/                     # Docker related files
├── config/                     # Config examples
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
uv run dev all            # Run all quality checks (lint, type, format)
uv run dev pre-commit     # Run pre-commit checks
```

## Testing

```bash
uv run test all             # Full test suite with coverage
uv run test quick           # Fast run (no coverage)
uv run test html            # Generate HTML report
```

**Markers:** `unit`, `integration`, `slow`, `database`, `async`

## Database

**Stack:** SQLModel (ORM) • Alembic (migrations) • PostgreSQL (psycopg async)

```bash
uv run db init              # Initialize with migrations
uv run db dev               # Generate & apply migration
uv run db push              # Apply pending migrations
uv run db status            # Show migration status
uv run db health            # Check connection
uv run db reset             # Safe reset
uv run db nuke              # Complete wipe (dangerous)
```

## CLI Commands

**Bot:**

```bash
uv run tux start            # Start bot
uv run tux start --debug    # Debug mode
```

**Docs:**

```bash
uv run docs serve           # Local preview
uv run docs build           # Build site
uv run docs deploy          # Deploy to GitHub Pages
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

1. **Setup:** `uv sync` → configure `.env` & `config.toml`
2. **Develop:** Make changes → `uv run dev all` → `uv run test quick`
3. **Database:** Modify models → `uv run db new "description"` → `uv run db dev`
4. **Rules:** Validate rules/commands → `uv run ai validate-rules`
5. **Commit:** `uv run dev pre-commit` → `uv run test all`

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

- No secrets in code
- Environment variables for config
- Validate all inputs
- Proper permission checks

**Performance:**

- Async for I/O
- Cache frequently accessed data
- Optimize queries
- Monitor memory

## File Organization

- Max 1600 lines per file
- One class/function per file when possible
- Descriptive filenames

## Troubleshooting

```bash
# Database issues
uv run db health

# Import errors
uv sync --reinstall

# Type errors
uv run basedpyright --verbose

# Test failures
uv run pytest -v -s

# Cursor validation
uv run ai validate-rules
```

## Resources

- **Docs:** <https://tux.atl.dev>
- **Issues:** <https://github.com/allthingslinux/tux/issues>
- **Discord:** <https://discord.gg/gpmSjcjQxg>
- **Repo:** <https://github.com/allthingslinux/tux>
