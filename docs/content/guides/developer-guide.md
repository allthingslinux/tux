# Developer Guide

This guide covers everything you need to know to contribute to Tux, from initial setup to advanced
development patterns.

## Getting Started

### Prerequisites

**Required:**

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- PostgreSQL database
- Git

**Optional:**

- Docker & Docker Compose (for containerized development)
- VS Code or PyCharm (recommended IDEs)

### Quick Setup

**1. Clone and Setup:**

```bash
git clone https://github.com/allthingslinux/tux.git
cd tux
uv sync
```text

**2. Configure Environment:**

```bash
cp .env.example .env
# Edit .env with your configuration
```text

**3. Database Setup:**

```bash
# Local PostgreSQL
createdb tux
uv run db migrate-push

# Or use Docker
uv run docker up
```text

**4. Start Development:**

```bash
uv run tux start --debug
```text

### Development Environment Options

#### Local Development

**Advantages:**

- Faster iteration
- Direct debugging
- Full system access

**Setup:**

```bash
# Install Python dependencies
uv sync

# Install pre-commit hooks
uv run dev pre-commit install

# Set up database
createdb tux
uv run db migrate-push

# Start bot
uv run tux start --debug
```text

**Environment Variables:**

```bash
# .env file
DISCORD_TOKEN=your_bot_token
DATABASE_URL=postgresql://localhost:5432/tux
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```text

#### Docker Development

**Advantages:**

- Consistent environment
- Easy database setup
- Production-like setup

**Setup:**

```bash
# Start all services
uv run docker up

# View logs
uv run docker logs

# Shell into container
uv run docker shell

# Stop services
uv run docker down
```text

**Docker Compose Services:**

- `tux` - Main bot application
- `postgres` - PostgreSQL database
- `redis` - Caching (optional)

## Development Workflow

### Daily Development

**Start Development Session:**

```bash
# Pull latest changes
git pull origin main

# Update dependencies
uv sync

# Run database migrations
uv run db migrate-push

# Start bot with debug logging
uv run tux start --debug
```text

**Code Quality Checks:**

```bash
# Run all checks
uv run dev all

# Individual checks
uv run dev lint      # Ruff linting
uv run dev format    # Code formatting
uv run dev type-check # Type checking
```text

**Testing:**

```bash
# Run tests with coverage
uv run test run

# Quick tests (no coverage)
uv run test quick

# Generate HTML coverage report
uv run test html

# Run benchmark tests
uv run test benchmark
```text

### Git Workflow

**Branch Naming:**

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

**Commit Messages:**
Follow conventional commits format:

```text
type(scope): description

feat(moderation): add timeout command
fix(database): resolve connection pool issue
docs(api): update database documentation
```text

**Pull Request Process:**

1. Create feature branch from `main`
2. Make changes with tests
3. Run quality checks locally
4. Push and create PR
5. Address review feedback
6. Merge after approval

### Code Organization

**Project Structure:**

```text
src/tux/
├── core/           # Core bot functionality
├── database/       # Database models and controllers
├── modules/        # Command modules (cogs)
├── services/       # External services integration
├── shared/         # Shared utilities and types
└── __main__.py     # Application entry point
```text

**Module Structure:**

```python
# modules/example/example.py
from tux.core.base_cog import BaseCog

class ExampleCog(BaseCog):
    """Example command module."""
    
    @commands.command()
    async def example(self, ctx):
        """Example command."""
        await ctx.send("Hello, world!")

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
```text

## Architecture Overview

### Core Components

**Bot Core:**

- `Bot` - Main bot class extending discord.py
- `BaseCog` - Base class for all command modules
- `DatabaseCoordinator` - Database access layer
- `PermissionSystem` - Role-based permissions

**Database Layer:**

- SQLModel (Pydantic + SQLAlchemy) for type-safe models
- Async PostgreSQL with connection pooling
- Alembic for database migrations
- Repository pattern for data access

**Command System:**

- Hybrid commands (slash + prefix)
- Automatic cog loading
- Permission-based access control
- Error handling and logging

### Design Patterns

**Repository Pattern:**

```python
# Database access through repositories
cases = await self.db.case.get_cases_by_user(user_id, guild_id)
```text

**Dependency Injection:**

```python
# Services injected through bot instance
class MyCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.db = bot.db  # Database coordinator
```text

**Error Handling:**

```python
# Global error handler with Sentry integration
@commands.Cog.listener()
async def on_command_error(self, ctx, error):
    # Automatic error categorization and user feedback
```text

## Adding Features

### Creating Commands

**Basic Command:**

```python
@commands.command()
async def hello(self, ctx, name: str = None):
    """Say hello to someone."""
    target = name or ctx.author.mention
    await ctx.send(f"Hello, {target}!")
```text

**Slash Command:**

```python
@app_commands.command()
async def info(self, interaction: discord.Interaction, user: discord.Member = None):
    """Get user information."""
    target = user or interaction.user
    embed = discord.Embed(title=f"Info for {target}")
    await interaction.response.send_message(embed=embed)
```text

**Hybrid Command:**

```python
@commands.hybrid_command()
async def ping(self, ctx):
    """Check bot latency."""
    latency = round(self.bot.latency * 1000)
    await ctx.send(f"Pong! {latency}ms")
```text

### Database Operations

**Creating Models:**

```python
from sqlmodel import SQLModel, Field
from datetime import datetime

class MyModel(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```text

**Database Operations:**

```python
# Create
item = await self.db.my_model.create(name="example")

# Read
item = await self.db.my_model.get_by_id(1)
items = await self.db.my_model.find_all(filters={"name": "example"})

# Update
updated = await self.db.my_model.update_by_id(1, name="new_name")

# Delete
success = await self.db.my_model.delete_by_id(1)
```text

### Adding Permissions

**Permission Levels:**

```python
from tux.core.checks import has_permission

@commands.command()
@has_permission("moderator")
async def moderate(self, ctx):
    """Moderator-only command."""
    pass
```text

**Custom Checks:**

```python
def is_guild_owner():
    def predicate(ctx):
        return ctx.author.id == ctx.guild.owner_id
    return commands.check(predicate)

@commands.command()
@is_guild_owner()
async def owner_only(self, ctx):
    """Guild owner only command."""
    pass
```text

## Testing

### Test Structure

**Test Organization:**

```text
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test data and fixtures
└── conftest.py     # Pytest configuration
```text

**Writing Tests:**

```python
import pytest
from tux.database.controllers import CaseController

@pytest.mark.asyncio
async def test_create_case(db_service):
    controller = CaseController(db_service)
    case = await controller.create_case(
        case_type="BAN",
        case_user_id=123,
        case_moderator_id=456,
        guild_id=789,
        case_reason="Test ban"
    )
    assert case.case_type == "BAN"
    assert case.case_user_id == 123
```text

**Test Commands:**

```bash
# Run all tests
uv run test run

# Run specific test file
uv run test run tests/unit/test_cases.py

# Run with specific markers
uv run test run -m "not slow"

# Generate coverage report
uv run test html
```text

### Mocking

**Database Mocking:**

```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.case.create_case.return_value = Case(case_id=1, ...)
    return db
```text

**Discord Mocking:**

```python
from unittest.mock import MagicMock

@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.author.id = 123
    ctx.guild.id = 456
    return ctx
```text

## Database Development

### Migrations

**Creating Migrations:**

```bash
# Generate migration
uv run db migrate-generate "add user table"

# Apply migrations
uv run db migrate-push

# Check migration status
uv run db migrate-status
```text

**Migration Best Practices:**

- Always review generated migrations
- Test migrations on development data
- Include rollback procedures
- Document breaking changes

### Database Patterns

**Repository Pattern:**

```python
class UserRepository:
    def __init__(self, db: DatabaseService):
        self.db = db
    
    async def get_user_by_discord_id(self, discord_id: int) -> User | None:
        return await self.db.user.find_one({"discord_id": discord_id})
```text

**Transaction Management:**

```python
async with self.db.case.with_session() as session:
    # Multiple operations in same transaction
    case = await self.db.case.create(...)
    await self.db.guild.update_case_count(guild_id)
```text

## Error Handling & Monitoring

### Error Handling Patterns

**Command Error Handling:**

```python
@commands.command()
async def risky_command(self, ctx):
    try:
        # Risky operation
        result = await some_operation()
        await ctx.send(f"Success: {result}")
    except SpecificError as e:
        await ctx.send(f"Error: {e}")
        logger.warning(f"Command failed: {e}", extra={"user_id": ctx.author.id})
    except Exception as e:
        await ctx.send("An unexpected error occurred.")
        logger.error(f"Unexpected error: {e}", exc_info=True)
```text

**Global Error Handler:**

```python
# Automatically handles uncaught command errors
# Provides user-friendly messages
# Logs errors to Sentry for monitoring
```text

### Logging

**Structured Logging:**

```python
import structlog

logger = structlog.get_logger()

# Context-aware logging
logger.info("Command executed", 
           command="ban", 
           user_id=ctx.author.id,
           guild_id=ctx.guild.id)
```text

**Log Levels:**

- `DEBUG` - Detailed diagnostic information
- `INFO` - General operational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages

### Sentry Integration

**Error Tracking:**

```python
import sentry_sdk

# Automatic error capture
# Performance monitoring
# Release tracking
# User context
```text

## Performance Considerations

### Database Optimization

**Query Optimization:**

```python
# Use specific filters
cases = await self.db.case.find_all(
    filters={"guild_id": guild_id, "case_status": True}
)

# Limit results
recent = await self.db.case.find_all(
    filters={"guild_id": guild_id},
    order_by=Case.created_at.desc(),
    limit=10
)
```text

**Connection Pooling:**

```python
# Configured automatically
# Monitor connection usage
# Tune pool size for load
```text

### Memory Management

**Caching Strategies:**

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(data):
    # Cache expensive operations
    return result
```text

**Resource Cleanup:**

```python
# Automatic cleanup in context managers
async with self.db.session() as session:
    # Session automatically closed
    pass
```text

## Contributing Guidelines

### Code Style

**Formatting:**

- Use Ruff for formatting and linting
- Follow PEP 8 guidelines
- Use type hints everywhere
- Document all public functions

**Naming Conventions:**

- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Descriptive names over short names

### Documentation

**Docstring Format:**

```python
async def create_case(self, case_type: str, user_id: int) -> Case:
    """Create a new moderation case.
    
    Args:
        case_type: Type of moderation action
        user_id: Discord user ID
        
    Returns:
        Created case instance
        
    Raises:
        ValueError: If case_type is invalid
    """
```text

**Code Comments:**

```python
# Explain why, not what
# Complex business logic
# Non-obvious optimizations
# Temporary workarounds
```text

### Pull Request Guidelines

**Before Submitting:**

1. Run all quality checks (`uv run dev all`)
2. Add tests for new functionality
3. Update documentation
4. Test manually in development environment

**PR Description:**

- Clear description of changes
- Link to related issues
- Screenshots for UI changes
- Breaking changes noted

This guide provides comprehensive information for contributing to Tux. For specific technical
details, see the developer documentation sections.
