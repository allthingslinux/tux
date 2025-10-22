# Getting Started - For Developers

Welcome to Tux development! This guide will help you set up your development environment and make your first contribution.

## What You'll Need

### Required

- **Python 3.13+** - The minimum supported version
- **[UV](https://docs.astral.sh/uv/)** - Fast Python package manager
- **PostgreSQL** - Database (can use Docker)
- **Git** - Version control
- **Discord Bot Application** - For testing

### Recommended

- **[VS Code](https://code.visualstudio.com/)** or **[PyCharm](https://www.jetbrains.com/pycharm/)** - IDEs with great Python support
- **Docker & Docker Compose** - For database and testing
- **[Pre-commit](https://pre-commit.com/)** - Git hooks for code quality

## Quick Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Install UV if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (including dev, test, docs)
uv sync

# Set up pre-commit hooks
uv run pre-commit install
```

### 2. Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit with your bot token and database settings
nano .env
```

Minimum required settings:

```bash
# Your Discord bot token
BOT_TOKEN=your_test_bot_token

# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tuxdb
POSTGRES_USER=tuxuser
POSTGRES_PASSWORD=devpassword123

# Enable debug mode for development
DEBUG=true
```

### 3. Set Up Database

**Option A: Using Docker (Recommended)**

```bash
# Start PostgreSQL with Docker Compose
uv run docker up

# This starts postgres + adminer web UI
# Access adminer at http://localhost:8080
```

**Option B: Local PostgreSQL**

```bash
# Create database and user
createdb tuxdb
createuser tuxuser

# Set password and grant permissions
psql -c "ALTER USER tuxuser PASSWORD 'devpassword123';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE tuxdb TO tuxuser;"
```

### 4. Run Migrations

```bash
# Initialize database with migrations
uv run db push
```

### 5. Start Development Bot

```bash
# Start with hot-reload enabled
uv run tux start --debug

# Bot will automatically reload when you change code!
```

## Development Workflow

### Running Code Quality Checks

```bash
# Run all checks at once
uv run dev all

# Or run individually:
uv run dev lint           # Ruff linter
uv run dev format         # Ruff formatter
uv run dev type-check     # Basedpyright
uv run dev lint-docstring # Pydoclint
```

### Running Tests

```bash
# Run all tests with coverage
uv run tests run

# Quick run without coverage
uv run tests quick

# Run specific test file
uv run pytest tests/unit/test_config_loaders.py

# Run with specific marker
uv run pytest -m unit
```

**[Full Testing Guide →](../developer-guide/testing/overview.md)**

### Database Operations

```bash
# Create new migration
uv run db new "add user preferences"

# Apply migrations
uv run db push

# Check migration status
uv run db status

# View database tables
uv run db tables

# Reset database (safe, uses migrations)
uv run db reset
```

**[Database Guide →](../developer-guide/database/migrations.md)**

### Building Documentation

```bash
# Serve docs locally with hot-reload
uv run docs serve

# Build static docs
uv run docs build

# Access at http://localhost:8000
```

## Project Structure

Understanding the codebase layout:

```
tux/
├── src/tux/              # Main source code
│   ├── core/             # Core bot functionality
│   ├── database/         # Database models & controllers
│   ├── modules/          # Command modules (cogs)
│   ├── services/         # Service layer (wrappers, handlers)
│   ├── ui/               # UI components (embeds, views, modals)
│   └── shared/           # Shared utilities & config
├── scripts/              # CLI tools (db, dev, tests, etc.)
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── docs/                 # Documentation
└── pyproject.toml        # Project configuration
```

**[Detailed Project Structure →](../developer-guide/getting-started/project-structure.md)**

## Making Your First Contribution

### 1. Choose What to Work On

- **[Good First Issues](https://github.com/allthingslinux/tux/labels/good%20first%20issue)** - Beginner-friendly
- **[Help Wanted](https://github.com/allthingslinux/tux/labels/help%20wanted)** - Community priority
- **[Bug Reports](https://github.com/allthingslinux/tux/labels/bug)** - Fix bugs

### 2. Create a Branch

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Or bugfix branch
git checkout -b fix/bug-description
```

### 3. Make Your Changes

Follow our coding standards:

- **Type hints** on all functions
- **Numpy-style docstrings** for documentation
- **Async/await** patterns for I/O operations
- **Controller pattern** for database access
- **No print statements** (use loguru logger)

**[Code Standards Guide →](../developer-guide/getting-started/code-standards.md)**

### 4. Test Your Changes

```bash
# Run relevant tests
uv run tests run

# Run code quality checks
uv run dev all

# Test the bot manually in Discord
uv run tux start --debug
```

### 5. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: add user preferences command"
# OR
git commit -m "fix: resolve database connection timeout"
```

Commit types:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Fill out the PR template with details
```

**[Full Contribution Guide →](../developer-guide/contributing/git-workflow.md)**

## Essential Developer Resources

### Architecture Documentation

- **[Architecture Overview](../developer-guide/architecture/overview.md)** - System design
- **[Bot Lifecycle](../developer-guide/architecture/bot-lifecycle.md)** - Startup/shutdown
- **[Cog System](../developer-guide/architecture/cog-system.md)** - Module system
- **[Permission System](../developer-guide/architecture/permission-system.md)** - Dynamic permissions

### Development Guides

- **[Creating a Cog](../developer-guide/guides/creating-a-cog.md)** - Add new modules
- **[Creating Commands](../developer-guide/guides/creating-commands.md)** - Hybrid commands
- **[Database Operations](../developer-guide/guides/database-operations.md)** - Using controllers
- **[UI Components](../developer-guide/guides/ui-components.md)** - Views, modals, buttons

### Patterns & Best Practices

- **[Database Patterns](../developer-guide/patterns/database-patterns.md)** - Controller pattern, DI
- **[Error Handling](../developer-guide/patterns/error-patterns.md)** - Error patterns
- **[Async Patterns](../developer-guide/patterns/async-patterns.md)** - Async best practices

## Development Tools

### CLI Commands

All development tasks use our custom CLI:

```bash
# Bot management
uv run tux start         # Start bot
uv run tux start --debug # Start with debug mode
uv run tux version       # Show version

# Database management
uv run db push           # Apply migrations
uv run db new "msg"      # Create migration
uv run db status         # Check status
uv run db health         # Health check

# Development tools
uv run dev lint          # Lint code
uv run dev format        # Format code
uv run dev type-check    # Type checking
uv run dev all           # All checks

# Testing
uv run tests run         # Run tests
uv run tests quick       # Quick run
uv run tests coverage    # Coverage report

# Docker
uv run docker up         # Start services
uv run docker down       # Stop services
uv run docker logs       # View logs

# Documentation
uv run docs serve        # Serve docs
uv run docs build        # Build docs
```

**[CLI Tools Guide →](../developer-guide/cli-tools/overview.md)**

### Hot Reload

Tux includes automatic hot-reload for development:

- Edit any Python file
- Save the file
- Tux automatically reloads the changed module
- No need to restart the bot!

**[Hot Reload System →](../developer-guide/core-systems/hot-reload.md)**

### Debugging

```python
# Use loguru for logging
from loguru import logger

logger.debug("Debug information")
logger.info("Information")
logger.warning("Warning")
logger.error("Error occurred")
```

**[Logging Guide →](../developer-guide/core-systems/logging.md)**

## Common Development Tasks

### Adding a New Command

1. Create file in `src/tux/modules/category/`
2. Inherit from `BaseCog`
3. Add `@commands.hybrid_command` decorator
4. Implement command logic
5. Add docstring and type hints
6. Write tests
7. Update documentation

**[Full Guide →](../developer-guide/guides/creating-commands.md)**

### Working with Database

1. Create/modify SQLModel model
2. Generate migration: `uv run db new "description"`
3. Review generated migration
4. Apply: `uv run db push`
5. Use controller for database operations

**[Database Guide →](../developer-guide/database/models.md)**

### Adding Configuration Options

1. Add field to config model in `src/tux/shared/config/models.py`
2. Add to `.env.example`
3. Run: `uv run config generate`
4. Update documentation

**[Config Guide →](../developer-guide/guides/config-options.md)**

## Getting Help

### Documentation

- **[Developer Guide](../developer-guide/)** - Complete dev docs
- **[API Reference](../reference/api/)** - Auto-generated code docs
- **[CLI Reference](../reference/cli/)** - CLI command docs

### Community

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask in #development
- **[GitHub Discussions](https://github.com/allthingslinux/tux/discussions)** - Technical discussions
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Bug reports & features

## Code Style Checklist

Before submitting:

- [ ] All functions have type hints
- [ ] Docstrings use numpy format
- [ ] Code passes `uv run dev all`
- [ ] Tests pass with `uv run tests run`
- [ ] No print statements (use logger)
- [ ] Follows async patterns
- [ ] Uses controller pattern for database
- [ ] Conventional commit message
- [ ] PR description filled out

**[Code Standards →](../developer-guide/getting-started/code-standards.md)**

## What's Next?

### Essential Reading

- **[Architecture Overview](../developer-guide/architecture/overview.md)** - Understand the system
- **[Code Standards](../developer-guide/getting-started/code-standards.md)** - Style guide
- **[First Contribution](../developer-guide/getting-started/first-contribution.md)** - Step-by-step guide

### Deep Dives

- **[Core Systems](../developer-guide/core-systems/)** - Hot-reload, error handling, Sentry
- **[Database Architecture](../developer-guide/database/)** - Models, controllers, migrations
- **[Testing](../developer-guide/testing/)** - Unit, integration, E2E tests

Ready to contribute? Check out the **[Developer Guide](../developer-guide/)** for comprehensive documentation!
