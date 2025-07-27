# Contribution Guide

## Overview

This guide provides detailed instructions for contributing to the Tux Discord bot project, including code standards, development workflows, and best practices.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.11+
- Poetry for dependency management
- Docker and Docker Compose
- Git
- A Discord application and bot token for testing

### Dlopment Environment Setup

1. **Fork and clone the repository**:

   ```bash
   git clone https://github.com/yourusername/tux.git
   cd tux
   ```

2. **Set up the development environment**:

   ```bash
   # Install dependencies
   poetry install

   # Set up pre-commit hooks
   poetry run pre-commit install

   # Copy environment configuration
   cp .env.example .env
   # Edit .env with your bot token and database settings
   ```

3. **Start development services**:

   ```bash
   # Start database
   docker-compose up -d db

   # Run migrations
   poetry run prisma migrate dev

   # Start the bot in development mode
   poetry run python -m tux
   ```

## Development Workflow

### 1. Planning Your Contribution

Before starting work:

1. **Check existing issues** for similar work
2. **Create an issue** if one doesn't exist
3. **Discuss your approach** with maintainers
4. **Get approval** for significant changes

### 2. Creating a Feature Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### 3. Development Process

#### Test-Driven Development (TDD)

We follow TDD practices:

1. **Write failing tests first**:

   ```python
   # tests/unit/services/test_user_service.py
   import pytest
   from tux.services.user_service import UserService

   class TestUserService:
       async def test_create_user_success(self):
           service = UserService()
           user = await service.create_user("testuser")
           assert user.username == "testuser"
           assert user.id is not None
   ```

2. **Implement the minimum code to pass**:

   ```python
   # tux/services/user_service.py
   from tux.database.models import User

   class UserService:
       async def create_user(self, username: str) -> User:
           # Minimal implementation
           return User(username=username, id=1)
   ```

3. **Refactor and improve**:

   ```python
   # Improved implementation
   class UserService:
       def __init__(self, user_repo: UserRepository):
           self.user_repo = user_repo

       async def create_user(self, username: str) -> User:
           if await self.user_repo.exists_by_username(username):
               raise UserAlreadyExistsError(f"User {username} already exists")
           
           user = User(username=username)
           return await self.user_repo.create(user)
   ```

#### Code Structure Guidelines

##### Service Layer Implementation

Services contain business logic and orchestrate operations:

```python
from typing import Optional, List
from tux.database.repositories import UserRepository, GuildRepository
from tux.utils.exceptions import UserNotFoundError, ValidationError
import structlog

logger = structlog.get_logger(__name__)

class UserService:
    def __init__(self, user_repo: UserRepository, guild_repo: GuildRepository):
        self.user_repo = user_repo
        self.guild_repo = guild_repo

    async def get_user_profile(self, user_id: int, guild_id: int) -> UserProfile:
        """Get comprehensive user profile including guild-specific data."""
        logger.info("Fetching user profile", user_id=user_id, guild_id=guild_id)
        
        try:
            user = await self.user_repo.get_by_id(user_id)
            guild_member = await self.guild_repo.get_member(guild_id, user_id)
            
            return UserProfile(
                user=user,
                guild_member=guild_member,
                permissions=await self._calculate_permissions(user, guild_member)
            )
        except Exception as e:
            logger.error("Failed to fetch user profile", 
                        user_id=user_id, guild_id=guild_id, error=str(e))
            raise

    async def _calculate_permissions(self, user: User, member: GuildMember) -> List[str]:
        """Calculate user permissions based on roles and settings."""
        # Implementation here
        pass
```

##### Cog Implementation

Cogs handle Discord interactions and delegate to services:

```python
from discord.ext import commands
from discord import Interaction
from tux.services.user_service import UserService
from tux.ui.embeds import EmbedFactory
from tux.utils.exceptions import TuxError
import structlog

logger = structlog.get_logger(__name__)

class UserCog(commands.Cog):
    def __init__(self, bot, user_service: UserService):
        self.bot = bot
        self.user_service = user_service

    @commands.hybrid_command(name="profile")
    async def profile(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """Display user profile information."""
        target_user = user or ctx.author
        
        try:
            profile = await self.user_service.get_user_profile(
                target_user.id, ctx.guild.id
            )
            
            embed = EmbedFactory.create_user_profile_embed(profile)
            await ctx.send(embed=embed)
            
        except TuxError as e:
            if e.user_friendly:
                await ctx.send(e.message)
            else:
                logger.error("Unexpected error in profile command", 
                           user_id=target_user.id, error=str(e))
                await ctx.send("An unexpected error occurred.")
```

### 4. Code Quality Standards

#### Type Hints

All functions must include comprehensive type hints:

```python
from typing import Optional, List, Dict, Any, Union
from discord import Member, Guild
from tux.database.models import User

async def process_user_data(
    user_id: int,
    guild: Guild,
    options: Optional[Dict[str, Any]] = None
) -> Union[User, None]:
    """Process user data with optional configuration."""
    pass
```

#### Error Handling

Use structured error handling with custom exceptions:

```python
from tux.utils.exceptions import TuxError, UserNotFoundError, ValidationError

class UserService:
    async def update_user(self, user_id: int, data: Dict[str, Any]) -> User:
        try:
            # Validate input
            validated_data = self._validate_user_data(data)
            
            # Get user
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            # Update user
            updated_user = await self.user_repo.update(user_id, validated_data)
            logger.info("User updated successfully", user_id=user_id)
            
            return updated_user
            
        except ValidationError as e:
            logger.warning("Invalid user data", user_id=user_id, error=str(e))
            raise TuxError(f"Invalid user data: {e.message}", user_friendly=True)
        except Exception as e:
            logger.error("Failed to update user", user_id=user_id, error=str(e))
            raise TuxError("Failed to update user")

    def _validate_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user data and return cleaned data."""
        # Validation logic here
        pass
```

#### Logging

Use structured logging throughout:

```python
import structlog

logger = structlog.get_logger(__name__)

class MyService:
    async def process_request(self, request_id: str, data: Dict[str, Any]):
        logger.info("Processing request", request_id=request_id, data_keys=list(data.keys()))
        
        try:
            result = await self._do_processing(data)
            logger.info("Request processed successfully", 
                       request_id=request_id, result_size=len(result))
            return result
        except Exception as e:
            logger.error("Request processing failed", 
                        request_id=request_id, error=str(e), exc_info=True)
            raise
```

### 5. Testing Guidelines

#### Unit Tests

Test individual components in isolation:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from tux.services.moderation_service import ModerationService
from tux.utils.exceptions import UserNotFoundError

class TestModerationService:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_case_repo(self):
        return AsyncMock()
    
    @pytest.fixture
    def moderation_service(self, mock_user_repo, mock_case_repo):
        return ModerationService(mock_user_repo, mock_case_repo)
    
    async def test_ban_user_success(self, moderation_service, mock_user_repo, mock_case_repo):
        # Arrange
        user_id = 123
        reason = "Spam"
        mock_user = MagicMock(id=user_id, username="testuser")
        mock_user_repo.get_by_id.return_value = mock_user
        mock_case_repo.create.return_value = MagicMock(id=1)
        
        # Act
        result = await moderation_service.ban_user(user_id, reason)
        
        # Assert
        assert result.user_id == user_id
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_case_repo.create.assert_called_once()
    
    async def test_ban_user_not_found(self, moderation_service, mock_user_repo):
        # Arrange
        mock_user_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await moderation_service.ban_user(123, "reason")
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
        controller = DatabaseController(test_mode=True)
        await controller.connect()
        yield controller
        await controller.cleanup()
        await controller.disconnect()
    
    @pytest.fixture
    def user_service(self, db_controller):
        return UserService(db_controller.user_repository)
    
    async def test_user_lifecycle(self, user_service):
        # Create user
        user = await user_service.create_user("testuser")
        assert user.username == "testuser"
        
        # Update user
        updated_user = await user_service.update_user(user.id, {"bio": "Test bio"})
        assert updated_user.bio == "Test bio"
        
        # Get user
        retrieved_user = await user_service.get_user(user.id)
        assert retrieved_user.bio == "Test bio"
        
        # Delete user
        await user_service.delete_user(user.id)
        with pytest.raises(UserNotFoundError):
            await user_service.get_user(user.id)
```

#### Test Configuration

Use proper test configuration:

```python
# conftest.py
import pytest
import asyncio
from tux.core.container import Container
from tux.database.controllers import DatabaseController

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_container():
    """Create a test container with mocked dependencies."""
    container = Container()
    # Register test dependencies
    yield container
    await container.cleanup()

@pytest.fixture
async def test_db():
    """Create a test database connection."""
    db = DatabaseController(test_mode=True)
    await db.connect()
    yield db
    await db.cleanup()
    await db.disconnect()
```

### 6. Documentation Standards

#### Docstrings

Use comprehensive docstrings:

```python
async def calculate_user_level(
    self, 
    user_id: int, 
    guild_id: int, 
    include_bonus: bool = True
) -> UserLevel:
    """Calculate user level based on experience points.
    
    Args:
        user_id: The Discord user ID
        guild_id: The Discord guild ID
        include_bonus: Whether to include bonus experience in calculation
        
    Returns:
        UserLevel object containing level, experience, and progress information
        
    Raises:
        UserNotFoundError: If the user doesn't exist in the database
        GuildNotFoundError: If the guild doesn't exist in the database
        
    Example:
        >>> level = await service.calculate_user_level(123456789, 987654321)
        >>> print(f"User is level {level.current_level}")
    """
    pass
```

#### Code Comments

Add comments for complex logic:

```python
async def _calculate_experience_multiplier(self, user: User, guild: Guild) -> float:
    """Calculate experience multiplier based on user status and guild settings."""
    base_multiplier = 1.0
    
    # Premium users get 1.5x experience
    if user.is_premium:
        base_multiplier *= 1.5
    
    # Guild boosters get additional 1.2x multiplier
    if user.is_guild_booster(guild.id):
        base_multiplier *= 1.2
    
    # Apply guild-specific multipliers (events, special periods)
    guild_multiplier = await self._get_guild_multiplier(guild.id)
    base_multiplier *= guild_multiplier
    
    return min(base_multiplier, 3.0)  # Cap at 3x multiplier
```

### 7. Database Patterns

#### Repository Pattern

Implement repositories for data access:

```python
from typing import Optional, List
from tux.database.models import User
from tux.database.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.db.user.find_first(
            where={"username": username}
        )
    
    async def get_active_users(self, guild_id: int) -> List[User]:
        """Get all active users in a guild."""
        return await self.db.user.find_many(
            where={
                "guild_members": {
                    "some": {
                        "guild_id": guild_id,
                        "is_active": True
                    }
                }
            }
        )
    
    async def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search users by username or display name."""
        return await self.db.user.find_many(
            where={
                "OR": [
                    {"username": {"contains": query, "mode": "insensitive"}},
                    {"display_name": {"contains": query, "mode": "insensitive"}}
                ]
            },
            take=limit
        )
```

#### Unit of Work Pattern

Use unit of work for transactions:

```python
from tux.database.unit_of_work import UnitOfWork

async def transfer_points(self, from_user_id: int, to_user_id: int, points: int):
    """Transfer points between users atomically."""
    async with UnitOfWork() as uow:
        # Get users
        from_user = await uow.users.get_by_id(from_user_id)
        to_user = await uow.users.get_by_id(to_user_id)
        
        # Validate transfer
        if from_user.points < points:
            raise InsufficientPointsError("Not enough points for transfer")
        
        # Update points
        from_user.points -= points
        to_user.points += points
        
        # Save changes
        await uow.users.update(from_user)
        await uow.users.update(to_user)
        
        # Create transaction record
        transaction = Transaction(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=points,
            type="transfer"
        )
        await uow.transactions.create(transaction)
        
        # Commit all changes
        await uow.commit()
```

## Code Review Process

### Submitting a Pull Request

1. **Ensure your branch is up to date**:

   ```bash
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run all quality checks**:

   ```bash
   # Run tests
   poetry run pytest

   # Run linting
   poetry run ruff check .
   poetry run ruff format .

   # Run type checking
   poetry run mypy .

   # Run security checks
   poetry run bandit -r tux/
   ```

3. **Create a comprehensive PR description**:

   ```markdown
   ## Description
   Brief description of changes

   ## Changes Made
   - [ ] Added new feature X
   - [ ] Fixed bug Y
   - [ ] Updated documentation

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests pass
   - [ ] Manual testing completed

   ## Breaking Changes
   None / List any breaking changes

   ## Migration Guide
   None required / Steps for migration
   ```

### Review Criteria

Reviewers will check for:

1. **Code Quality**:
   - Follows established patterns
   - Proper error handling
   - Comprehensive type hints
   - Clear and concise code

2. **Testing**:
   - Adequate test coverage
   - Tests are meaningful and comprehensive
   - Edge cases are covered

3. **Documentation**:
   - Code is well-documented
   - Public APIs have docstrings
   - Complex logic is explained

4. **Performance**:
   - No obvious performance issues
   - Database queries are optimized
   - Async patterns are used correctly

5. **Security**:
   - Input validation is present
   - No security vulnerabilities
   - Sensitive data is handled properly

### Addressing Review Feedback

1. **Respond promptly** to review comments
2. **Ask for clarification** if feedback is unclear
3. **Make requested changes** in separate commits
4. **Update tests** if implementation changes
5. **Re-request review** after addressing feedback

## Common Patterns and Examples

### 1. Command Implementation

```python
@commands.hybrid_command(name="warn")
@require_permissions(PermissionLevel.MODERATOR)
async def warn_user(
    self, 
    ctx: commands.Context, 
    user: discord.Member, 
    *, 
    reason: str
):
    """Warn a user for rule violations."""
    try:
        warning = await self.moderation_service.warn_user(
            user_id=user.id,
            guild_id=ctx.guild.id,
            moderator_id=ctx.author.id,
            reason=reason
        )
        
        embed = EmbedFactory.create_warning_embed(warning)
        await ctx.send(embed=embed)
        
        # Send DM to user
        try:
            dm_embed = EmbedFactory.create_warning_dm_embed(warning, ctx.guild)
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send DM to user", ephemeral=True)
            
    except TuxError as e:
        await ctx.send(f"❌ {e.message}")
    except Exception as e:
        logger.error("Unexpected error in warn command", error=str(e))
        await ctx.send("❌ An unexpected error occurred")
```

### 2. Event Handling

```python
@commands.Cog.listener()
async def on_member_join(self, member: discord.Member):
    """Handle new member joins."""
    try:
        # Create user record
        user = await self.user_service.create_or_update_user(
            user_id=member.id,
            username=member.name,
            display_name=member.display_name
        )
        
        # Add to guild
        await self.guild_service.add_member(member.guild.id, member.id)
        
        # Send welcome message
        welcome_channel = await self.guild_service.get_welcome_channel(member.guild.id)
        if welcome_channel:
            embed = EmbedFactory.create_welcome_embed(member, member.guild)
            await welcome_channel.send(embed=embed)
            
        logger.info("New member processed", 
                   user_id=member.id, guild_id=member.guild.id)
                   
    except Exception as e:
        logger.error("Failed to process new member", 
                    user_id=member.id, guild_id=member.guild.id, error=str(e))
```

### 3. Background Tasks

```python
from discord.ext import tasks

class MaintenanceCog(commands.Cog):
    def __init__(self, bot, maintenance_service: MaintenanceService):
        self.bot = bot
        self.maintenance_service = maintenance_service
        self.cleanup_task.start()
    
    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Daily cleanup task."""
        try:
            logger.info("Starting daily cleanup")
            
            # Clean expired data
            expired_count = await self.maintenance_service.cleanup_expired_data()
            
            # Update statistics
            await self.maintenance_service.update_statistics()
            
            # Generate reports
            await self.maintenance_service.generate_daily_reports()
            
            logger.info("Daily cleanup completed", expired_items=expired_count)
            
        except Exception as e:
            logger.error("Daily cleanup failed", error=str(e))
    
    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        self.cleanup_task.cancel()
```

## Troubleshooting

### Common Development Issues

#### 1. Import Errors

```
ModuleNotFoundError: No module named 'tux.services'
```

**Solution**: Ensure you're using Poetry and the virtual environment:

```bash
poetry shell
poetry run python -m tux
```

#### 2. Database Connection Issues

```
prisma.errors.PrismaError: Can't reach database server
```

**Solution**: Start the database container:

```bash
docker-compose up -d db
```

#### 3. Test Failures

```
AssertionError: Expected call not found
```

**Solution**: Check mock setup and ensure async mocks are used:

```python
mock_service = AsyncMock()
mock_service.method.return_value = expected_value
```

#### 4. Type Checking Errors

```
error: Argument 1 to "method" has incompatible type
```

**Solution**: Add proper type hints and imports:

```python
from typing import Optional, List, Dict, Any
```

### Getting Help

1. **Check existing documentation** and examples
2. **Search closed issues** for similar problems
3. **Ask in development channels** for quick questions
4. **Create an issue** for bugs or feature requests
5. **Request code review** for complex changes

## Best Practices Summary

### Do's

- ✅ Write tests before implementation
- ✅ Use type hints everywhere
- ✅ Follow the established architecture patterns
- ✅ Handle errors gracefully
- ✅ Use structured logging
- ✅ Keep functions small and focused
- ✅ Document complex logic
- ✅ Use meaningful variable names

### Don'ts

- ❌ Don't bypass the service layer
- ❌ Don't use direct database access in cogs
- ❌ Don't ignore type checking errors
- ❌ Don't commit without running tests
- ❌ Don't use bare except clauses
- ❌ Don't hardcode configuration values
- ❌ Don't skip documentation for public APIs

## Resources

- [Developer Onboarding Guide](developer_onboarding_guide.md)
- [Architecture Documentation](.kiro/specs/codebase-improvements/design.md)
- [Testing Guide](tests/README.md)
- [API Documentation](docs/api/)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)

Thank you for contributing to Tux! Your efforts help make the bot better for everyone.
