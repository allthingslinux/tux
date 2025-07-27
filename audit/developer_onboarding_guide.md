# Developer Onboarding Guide

## Welcome to Tux Discord Bot Development

This guide will help you get started contributing to the Tux Discord bot project, understand our architectural patterns, and follow our development practices.

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- Docker and Docker Compose
- Git

### Environment Setup

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd tux
   ```

2. **Install dependencies**:

   ```bash
   poetry install
   ```

3. **Set up environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the database**:

   ```bash
   docker-compose up -d db
   ```

5. **Run database migrations**:

   ```bash
   poetry run prisma migrate dev
   ```

6. **Start the bot**:

   ```bash
   poetry run python -m tux
   ```

## Architecture Overview

### Current Architecture (Legacy)

The Tux bot currently uses a cog-based architecture with theing patterns:

```python
# Legacy cog pattern
class MyCog(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()  # Direct instantiation
```

### New Architecture (Target)

We're migrating to a service-oriented architecture with dependency injection:

```python
# New cog pattern with dependency injection
class MyCog(commands.Cog):
    def __init__(self, bot: Tux, user_service: UserService, logger: Logger) -> None:
        self.bot = bot
        self.user_service = user_service
        self.logger = logger
```

### Key Architectural Patterns

#### 1. Dependency Injection

**Purpose**: Reduce coupling and improve testability

**Implementation**:

```python
from tux.core.container import Container

# Service registration
container = Container()
container.register(UserService, UserService)
container.register(DatabaseController, DatabaseController)

# Service resolution
user_service = container.resolve(UserService)
```

#### 2. Repository Pattern

**Purpose**: Abstract data access and improve testability

**Implementation**:

```python
from tux.database.repositories import UserRepository

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_user(self, user_id: int) -> User:
        return await self.user_repo.get_by_id(user_id)
```

#### 3. Service Layer

**Purpose**: Separate business logic from presentation logic

**Structure**:

- **Presentation Layer**: Cogs handle Discord interactions
- **Application Layer**: Services orchestrate business workflows
- **Domain Layer**: Core business logic and rules
- **Infrastructure Layer**: Database, external APIs, utilities

## Development Workflow

### 1. Creating a New Feature

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Write tests first** (TDD approach):

   ```python
   # tests/unit/services/test_my_service.py
   import pytest
   from tux.services.my_service import MyService

   class TestMyService:
       async def test_my_method(self):
           service = MyService()
           result = await service.my_method()
           assert result is not None
   ```

3. **Implement the service**:

   ```python
   # tux/services/my_service.py
   class MyService:
       async def my_method(self):
           # Implementation here
           pass
   ```

4. **Create the cog**:

   ```python
   # tux/cogs/my_cog.py
   from discord.ext import commands
   from tux.services.my_service import MyService

   class MyCog(commands.Cog):
       def __init__(self, bot, my_service: MyService):
           self.bot = bot
           self.my_service = my_service

       @commands.command()
       async def my_command(self, ctx):
           result = await self.my_service.my_method()
           await ctx.send(f"Result: {result}")
   ```

### 2. Code Quality Standards

#### Type Hints

All functions must include type hints:

```python
async def process_user(user_id: int, guild_id: int) -> Optional[User]:
    pass
```

#### Error Handling

Use structured error handling:

```python
from tux.utils.exceptions import TuxError, UserNotFoundError

try:
    user = await self.user_service.get_user(user_id)
except UserNotFoundError:
    raise TuxError("User not found", user_friendly=True)
```

#### Logging

Use structured logging:

```python
import structlog

logger = structlog.get_logger(__name__)

async def my_method(self, user_id: int):
    logger.info("Processing user", user_id=user_id)
    try:
        # Process user
        logger.info("User processed successfully", user_id=user_id)
    except Exception as e:
        logger.error("Failed to process user", user_id=user_id, error=str(e))
        raise
```

### 3. Testing Guidelines

#### Unit Tests

Test individual components in isolation:

```python
import pytest
from unittest.mock import AsyncMock
from tux.services.user_service import UserService

class TestUserService:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_user_repo):
        return UserService(mock_user_repo)
    
    async def test_get_user_success(self, user_service, mock_user_repo):
        # Arrange
        mock_user_repo.get_by_id.return_value = User(id=1, name="test")
        
        # Act
        result = await user_service.get_user(1)
        
        # Assert
        assert result.id == 1
        mock_user_repo.get_by_id.assert_called_once_with(1)
```

#### Integration Tests

Test component interactions:

```python
import pytest
from tux.database.controllers import DatabaseController
from tux.services.user_service import UserService

class TestUserServiceIntegration:
    @pytest.fixture
    async def db_controller(self):
        controller = DatabaseController()
        await controller.connect()
        yield controller
        await controller.disconnect()
    
    async def test_user_creation_flow(self, db_controller):
        user_service = UserService(db_controller.user_repository)
        user = await user_service.create_user("test_user")
        assert user.name == "test_user"
```

### 4. Database Patterns

#### Using Repositories

```python
from tux.database.repositories import UserRepository

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_active_users(self) -> List[User]:
        return await self.user_repo.find_by_status("active")
```

#### Transaction Management

```python
from tux.database.unit_of_work import UnitOfWork

async def transfer_points(self, from_user_id: int, to_user_id: int, points: int):
    async with UnitOfWork() as uow:
        from_user = await uow.users.get_by_id(from_user_id)
        to_user = await uow.users.get_by_id(to_user_id)
        
        from_user.points -= points
        to_user.points += points
        
        await uow.users.update(from_user)
        await uow.users.update(to_user)
        await uow.commit()
```

## Common Patterns and Examples

### 1. Creating Embeds

Use the centralized embed factory:

```python
from tux.ui.embeds import EmbedFactory

embed = EmbedFactory.create_success_embed(
    title="Operation Successful",
    description="The operation completed successfully",
    fields=[("Field 1", "Value 1", True)]
)
await ctx.send(embed=embed)
```

### 2. Input Validation

Use validation utilities:

```python
from tux.utils.validation import validate_user_input, ValidationError

try:
    validated_input = validate_user_input(user_input, max_length=100)
except ValidationError as e:
    await ctx.send(f"Invalid input: {e.message}")
    return
```

### 3. Permission Checking

Use consistent permission patterns:

```python
from tux.utils.permissions import require_permissions, PermissionLevel

@require_permissions(PermissionLevel.MODERATOR)
@commands.command()
async def moderate_command(self, ctx):
    # Command implementation
    pass
```

## Migration Guide

### Migrating Existing Cogs

1. **Update constructor to use dependency injection**:

   ```python
   # Before
   def __init__(self, bot: Tux) -> None:
       self.bot = bot
       self.db = DatabaseController()
   
   # After
   def __init__(self, bot: Tux, user_service: UserService, logger: Logger) -> None:
       self.bot = bot
       self.user_service = user_service
       self.logger = logger
   ```

2. **Extract business logic to services**:

   ```python
   # Before (in cog)
   @commands.command()
   async def ban_user(self, ctx, user_id: int):
       user = await self.db.user.get_by_id(user_id)
       user.status = "banned"
       await self.db.user.update(user)
       await ctx.send("User banned")
   
   # After (service)
   class ModerationService:
       async def ban_user(self, user_id: int) -> User:
           user = await self.user_repo.get_by_id(user_id)
           user.status = "banned"
           return await self.user_repo.update(user)
   
   # After (cog)
   @commands.command()
   async def ban_user(self, ctx, user_id: int):
       try:
           user = await self.moderation_service.ban_user(user_id)
           embed = EmbedFactory.create_success_embed(
               title="User Banned",
               description=f"User {user.name} has been banned"
           )
           await ctx.send(embed=embed)
       except UserNotFoundError:
           await ctx.send("User not found")
   ```

3. **Update error handling**:

   ```python
   # Before
   try:
       # Some operation
       pass
   except Exception as e:
       await ctx.send(f"Error: {e}")
   
   # After
   try:
       # Some operation
       pass
   except TuxError as e:
       if e.user_friendly:
           await ctx.send(e.message)
       else:
           self.logger.error("Unexpected error", error=str(e))
           await ctx.send("An unexpected error occurred")
   ```

## Troubleshooting

### Common Issues

#### 1. Dependency Injection Errors

```
Error: Cannot resolve dependency 'UserService'
```

**Solution**: Ensure the service is registered in the container:

```python
container.register(UserService, UserService)
```

#### 2. Database Connection Issues

```
Error: Database connection failed
```

**Solution**: Check your `.env` file and ensure the database is running:

```bash
docker-compose up -d db
```

#### 3. Import Errors

```
ModuleNotFoundError: No module named 'tux.services'
```

**Solution**: Ensure you're running commands with Poetry:

```bash
poetry run python -m tux
```

### Getting Help

1. **Check the documentation**: Review this guide and the design documents
2. **Look at examples**: Check existing cogs that have been migrated
3. **Ask for help**: Reach out to the development team
4. **Create an issue**: If you find a bug or need clarification

## Contributing Guidelines

### Code Review Process

1. **Create a pull request** with a clear description
2. **Ensure all tests pass** and coverage is maintained
3. **Follow the code style** enforced by our linting tools
4. **Include documentation** for new features
5. **Address review feedback** promptly

### Quality Gates

Before merging, ensure:

- [ ] All tests pass
- [ ] Code coverage is maintained or improved
- [ ] Static analysis checks pass
- [ ] Documentation is updated
- [ ] Migration guide is provided (if needed)

### Best Practices

1. **Keep changes small and focused**
2. **Write tests before implementation**
3. **Use meaningful commit messages**
4. **Update documentation with changes**
5. **Consider backward compatibility**

## Resources

- [Design Document](.kiro/specs/codebase-improvements/design.md)
- [Requirements Document](.kiro/specs/codebase-improvements/requirements.md)
- [Architecture Decision Records](docs/adr/)
- [API Documentation](docs/api/)
- [Testing Guide](tests/README.md)

## Next Steps

1. **Set up your development environment** following the quick start guide
2. **Read the architecture overview** to understand the patterns
3. **Look at existing examples** in the codebase
4. **Start with a small contribution** to get familiar with the workflow
5. **Ask questions** if you need help or clarification

Welcome to the team! We're excited to have you contribute to making Tux better.
