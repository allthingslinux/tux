# Developer Guide

Welcome to the Tux Developer Guide! This comprehensive resource covers everything you need to contribute to Tux development.

## Who Is This For?

This guide is for:

- **Contributors** who want to add features or fix bugs
- **Developers** learning the Tux codebase
- **Maintainers** working on core systems
- **Anyone** interested in how Tux works internally

If you're using or deploying Tux, see the **[User Guide](../user-guide/index.md)** or **[Admin Guide](../admin-guide/index.md)** instead.

## Quick Navigation

### 🚀 Getting Started

New to Tux development? Start here:

- **[Development Setup](getting-started/development-setup.md)** - Set up your environment
- **[Project Structure](getting-started/project-structure.md)** - Understand the codebase
- **[First Contribution](getting-started/first-contribution.md)** - Make your first PR
- **[Code Standards](getting-started/code-standards.md)** - Style guide and best practices

### 🏗️ Architecture

Understanding the system:

- **[Architecture Overview](architecture/overview.md)** - High-level system design
- **[Bot Lifecycle](architecture/bot-lifecycle.md)** - Startup/shutdown process
- **[Cog System](architecture/cog-system.md)** - Module/plugin architecture
- **[Command System](architecture/command-system.md)** - Hybrid command implementation
- **[Permission System](architecture/permission-system.md)** - Dynamic rank-based permissions
- **[Configuration System](architecture/configuration-system.md)** - Multi-source config loading
- **[Database Architecture](architecture/database-architecture.md)** - Controller + Service pattern
- **[Service Layer](architecture/service-layer.md)** - Service architecture

### 🔧 Core Systems

Deep dives into key systems:

- **[Hot Reload](core-systems/hot-reload.md)** - Development hot-reload system
- **[Error Handling](core-systems/error-handling.md)** - Error handling architecture
- **[Sentry Integration](core-systems/sentry-integration.md)** - Error tracking and tracing
- **[Task Monitor](core-systems/task-monitor.md)** - Background task monitoring
- **[Logging](core-systems/logging.md)** - Loguru integration
- **[Prefix Manager](core-systems/prefix-manager.md)** - Guild prefix management
- **[Emoji Manager](core-systems/emoji-manager.md)** - Custom emoji system
- **[Plugin System](core-systems/plugin-system.md)** - Plugin architecture

### 📐 Patterns & Best Practices

Learn our coding patterns:

- **[Database Patterns](patterns/database-patterns.md)** - Controller pattern, DI
- **[Error Patterns](patterns/error-patterns.md)** - Error handling best practices
- **[Async Patterns](patterns/async-patterns.md)** - Async/await guidelines
- **[Caching](patterns/caching.md)** - Cache strategies
- **[Service Wrappers](patterns/service-wrappers.md)** - External API patterns

### 📚 How-To Guides

Step-by-step tutorials:

- **[Creating a Cog](guides/creating-a-cog.md)** - Add new command modules
- **[Creating Commands](guides/creating-commands.md)** - Implement hybrid commands
- **[Database Operations](guides/database-operations.md)** - Use controllers
- **[UI Components](guides/ui-components.md)** - Views, modals, buttons
- **[External APIs](guides/external-apis.md)** - HTTP client and wrappers
- **[Adding Features](guides/adding-features.md)** - Feature implementation
- **[Config Options](guides/config-options.md)** - Add configuration options

### 🧩 Module Deep Dives

Understanding key modules:

- **[Moderation System](modules/moderation-system.md)** - Coordinator pattern
- **[Levels System](modules/levels-system.md)** - XP and ranking
- **[Snippets System](modules/snippets-system.md)** - Text snippet management
- **[Code Execution](modules/code-execution.md)** - Godbolt/Wandbox integration
- **[Config Wizard](modules/config-wizard.md)** - Interactive onboarding

### 🗄️ Database

Working with data:

- **[Models](database/models.md)** - SQLModel model creation
- **[Controllers](database/controllers.md)** - Controller pattern
- **[Base Controllers](database/base-controllers.md)** - Reusable base classes
- **[Migrations](database/migrations.md)** - Alembic workflow
- **[Testing](database/testing.md)** - py-pglite test setup

### 🧪 Testing

Ensure quality:

- **[Testing Overview](testing/overview.md)** - Philosophy and strategy
- **[Unit Tests](testing/unit-tests.md)** - Testing individual components
- **[Integration Tests](testing/integration-tests.md)** - Testing interactions
- **[E2E Tests](testing/e2e-tests.md)** - End-to-end testing
- **[Fixtures](testing/fixtures.md)** - Test data management
- **[CI Pipeline](testing/ci-pipeline.md)** - GitHub Actions

### 🛠️ CLI Tools

Development tools:

- **[CLI Overview](cli-tools/overview.md)** - Typer-based CLI system
- **[Extending CLI](cli-tools/extending-cli.md)** - Add new commands

### 🎨 UI System

Building interfaces:

- **[Embeds](ui/embeds.md)** - Create rich embeds
- **[Views](ui/views.md)** - Interactive views
- **[Modals](ui/modals.md)** - User input forms
- **[Buttons](ui/buttons.md)** - Interactive buttons
- **[Onboarding Wizard](ui/onboarding-wizard.md)** - Multi-step wizards

### 🤝 Contributing

Join the team:

- **[Git Workflow](contributing/git-workflow.md)** - Branching and PRs
- **[Code Review](contributing/code-review.md)** - Review guidelines
- **[Documentation](contributing/documentation.md)** - Writing docs
- **[Versioning](contributing/versioning.md)** - Semver and releases
- **[Design Decisions](contributing/design-decisions.md)** - ADRs

## Quick Start

### 1. Set Up Environment

```bash
# Clone repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Install UV and dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Set up pre-commit hooks
uv run pre-commit install
```

**[Full Setup Guide →](getting-started/development-setup.md)**

### 2. Start Development

```bash
# Start database
uv run docker up

# Run migrations
uv run db push

# Start bot with hot-reload
uv run tux start --debug
```

### 3. Make Changes

- Edit code in `src/tux/`
- Bot automatically reloads on save
- Test in Discord

### 4. Run Quality Checks

```bash
# Run all checks
uv run dev all

# Or individually
uv run dev lint
uv run dev format
uv run dev type-check
uv run tests run
```

### 5. Submit PR

```bash
# Create branch
git checkout -b feature/my-feature

# Commit with conventional commits
git commit -m "feat: add awesome feature"

# Push and create PR
git push origin feature/my-feature
```

**[First Contribution Guide →](getting-started/first-contribution.md)**

## Project Overview

### Tech Stack

- **Language**: Python 3.13+
- **Framework**: discord.py 2.6+
- **Package Manager**: UV
- **Database**: PostgreSQL with SQLModel + SQLAlchemy
- **Migrations**: Alembic
- **Logging**: Loguru
- **Error Tracking**: Sentry SDK
- **HTTP Client**: httpx
- **CLI**: Typer
- **Type Checking**: Basedpyright (strict mode)
- **Linting/Formatting**: Ruff
- **Testing**: pytest with py-pglite
- **Documentation**: MkDocs Material + mkdocstrings

### Architecture Principles

- **Async-first**: All I/O operations use async/await
- **Type safety**: Strict type hints throughout
- **Dependency Injection**: Controllers injected via BaseCog
- **Controller Pattern**: Database access through controllers
- **Service Layer**: External APIs wrapped in services
- **Plugin System**: Extensible via plugins
- **Hot Reload**: Fast development iteration
- **Comprehensive Testing**: Unit, integration, and E2E tests

### Codebase Structure

```text
tux/
├── src/tux/              # Main source code
│   ├── core/             # Core bot functionality
│   │   ├── app.py        # Application lifecycle
│   │   ├── bot.py        # Bot class
│   │   ├── base_cog.py   # Base class for cogs
│   │   ├── permission_system.py
│   │   └── setup/        # Startup orchestration
│   ├── database/
│   │   ├── models/       # SQLModel models
│   │   ├── controllers/  # Database controllers
│   │   ├── migrations/   # Alembic migrations
│   │   └── service.py    # Database service
│   ├── modules/          # Command modules (cogs)
│   │   ├── moderation/   # Mod commands
│   │   ├── utility/      # Utility commands
│   │   ├── features/     # Feature modules
│   │   └── ...
│   ├── services/         # Service layer
│   │   ├── handlers/     # Event/error handlers
│   │   ├── hot_reload/   # Hot reload system
│   │   ├── moderation/   # Moderation coordinator
│   │   ├── sentry/       # Sentry integration
│   │   └── wrappers/     # API wrappers
│   ├── ui/               # UI components
│   │   ├── embeds.py     # Embed creator
│   │   ├── views/        # Discord views
│   │   ├── modals/       # Discord modals
│   │   └── buttons.py    # Buttons
│   ├── shared/           # Shared utilities
│   │   ├── config/       # Configuration system
│   │   ├── constants.py  # Constants
│   │   └── exceptions.py # Custom exceptions
│   ├── help/             # Custom help system
│   └── plugins/          # Plugin system
├── scripts/              # CLI tools
│   ├── cli.py            # Unified CLI
│   ├── db.py             # Database CLI
│   ├── dev.py            # Dev tools CLI
│   ├── tests.py          # Test runner CLI
│   └── ...
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   └── fixtures/         # Test fixtures
├── docs/                 # Documentation
└── pyproject.toml        # Project configuration
```

**[Detailed Structure →](getting-started/project-structure.md)**

## Development Workflow

### Daily Development

```bash
# Start services
uv run docker up

# Start bot (with hot-reload)
uv run tux start --debug

# Make changes → bot reloads automatically

# Run checks before committing
uv run dev all
uv run tests run
```

### Database Changes

```bash
# Modify models in src/tux/database/models/

# Generate migration
uv run db new "add user preferences"

# Review migration file in src/tux/database/migrations/versions/

# Apply migration
uv run db push

# Test changes
```

### Adding a Command

1. Create file in appropriate module directory
2. Inherit from `BaseCog`
3. Add `@commands.hybrid_command` decorator
4. Implement command logic
5. Add docstring (numpy format)
6. Write tests
7. Update documentation

**[Full Guide →](guides/creating-commands.md)**

### Testing

```bash
# Run all tests
uv run tests run

# Run specific category
uv run pytest -m unit
uv run pytest -m integration

# Run specific file
uv run pytest tests/unit/test_config_loaders.py

# Run with coverage report
uv run tests coverage
```

**[Testing Guide →](testing/overview.md)**

## Code Style

### Type Hints

All functions must have type hints:

```python
def get_user_rank(user_id: int, guild_id: int) -> int | None:
    """Get user's permission rank."""
    ...
```

### Docstrings

Use numpy-style docstrings:

```python
def timeout_user(user: discord.Member, duration: int, reason: str) -> Case:
    """
    Timeout a user for a specified duration.

    Parameters
    ----------
    user : discord.Member
        The user to timeout.
    duration : int
        Timeout duration in seconds.
    reason : str
        Reason for the timeout.

    Returns
    -------
    Case
        The created moderation case.

    Raises
    ------
    discord.Forbidden
        Bot lacks permissions.
    ValueError
        Invalid duration.
    """
    ...
```

### Async Patterns

Use async for I/O operations:

```python
# ✅ Good
async def get_user_data(user_id: int) -> UserData:
    async with self.db.session() as session:
        result = await session.execute(...)
        return result.scalar_one()

# ❌ Bad - blocking call
def get_user_data(user_id: int) -> UserData:
    session = self.db.session()
    result = session.execute(...)
    return result.scalar_one()
```

### Controller Pattern

Use controllers for database access:

```python
# ✅ Good - via controller
class MyCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.case_controller = self.db.case

    async def create_case(self, ...):
        case = await self.case_controller.insert_case(...)

# ❌ Bad - direct database access
class MyCog(BaseCog):
    async def create_case(self, ...):
        async with db.session() as session:
            case = Case(...)
            session.add(case)
```

**[Code Standards →](getting-started/code-standards.md)**

## Key Concepts

### Cogs (Modules)

Cogs are modular command groups:

```python
class MyCog(BaseCog):
    """My command group."""

    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.controller = self.db.my_controller

    @commands.hybrid_command()
    async def mycommand(self, ctx: commands.Context[Tux]) -> None:
        """Command description."""
        ...
```

**[Cog System →](architecture/cog-system.md)**

### Hybrid Commands

Commands work as both slash and prefix commands:

```python
@commands.hybrid_command(name="ban", aliases=["b"])
@commands.guild_only()
@requires_command_permission()
async def ban(
    self,
    ctx: commands.Context[Tux],
    user: discord.Member,
    *,
    reason: str = "No reason provided",
) -> None:
    """Ban a user from the server."""
    ...
```

**[Command System →](architecture/command-system.md)**

### Permission Ranks

Dynamic rank-based permissions (0-7):

```python
@requires_command_permission()  # Uses default rank for command
async def moderate_command(self, ctx: commands.Context[Tux]) -> None:
    """Moderation command."""
    ...
```

**[Permission System →](architecture/permission-system.md)**

## Tools & Commands

### Development Commands

```bash
# Bot management
uv run tux start           # Start bot
uv run tux start --debug   # Debug mode
uv run tux version         # Version info

# Code quality
uv run dev lint            # Lint with Ruff
uv run dev format          # Format with Ruff
uv run dev type-check      # Type check with Basedpyright
uv run dev lint-docstring  # Lint docstrings
uv run dev all             # All checks

# Database
uv run db push             # Apply migrations
uv run db new "message"    # Create migration
uv run db status           # Migration status
uv run db health           # Health check
uv run db tables           # List tables

# Testing
uv run tests run           # All tests with coverage
uv run tests quick         # Quick run without coverage
uv run tests coverage      # Coverage report

# Docker
uv run docker up           # Start services
uv run docker down         # Stop services
uv run docker logs         # View logs

# Documentation
uv run docs serve          # Serve docs locally
uv run docs build          # Build static docs
```

**[CLI Reference →](../reference/cli.md)**

## Getting Help

### Documentation

- **[Architecture](architecture/overview.md)** - System design
- **[Patterns](patterns/database-patterns.md)** - Best practices
- **[Guides](guides/creating-a-cog.md)** - How-to tutorials
- **[Reference](../reference/index.md)** - API and configuration reference

### Community

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask in #development
- **[GitHub Discussions](https://github.com/allthingslinux/tux/discussions)** - Technical discussions
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Bug reports

### Resources

- **[Python 3.13 Docs](https://docs.python.org/3.13/)** - Python reference
- **[discord.py Docs](https://discordpy.readthedocs.io/)** - Discord.py guide
- **[SQLModel Docs](https://sqlmodel.tiangolo.com/)** - Database models
- **[Typer Docs](https://typer.tiangolo.com/)** - CLI framework

## What's Next?

### New Contributors

1. **[Development Setup](getting-started/development-setup.md)** - Get environment ready
2. **[Project Structure](getting-started/project-structure.md)** - Learn the layout
3. **[First Contribution](getting-started/first-contribution.md)** - Make your first PR

### Understanding the System

1. **[Architecture Overview](architecture/overview.md)** - High-level design
2. **[Bot Lifecycle](architecture/bot-lifecycle.md)** - How Tux starts
3. **[Core Systems](core-systems/hot-reload.md)** - Key subsystems

### Building Features

1. **[Creating a Cog](guides/creating-a-cog.md)** - Add command module
2. **[Database Operations](guides/database-operations.md)** - Work with data
3. **[UI Components](guides/ui-components.md)** - Build interfaces

Ready to contribute? Start with **[Development Setup](getting-started/development-setup.md)**!
