# Coding Standards for Tux Discord Bot

## Overview

This documtablishes coding standards and best practices for the Tux Discord bot project. These standards ensure consistency, maintainability, and quality across the codebase.

## General Principles

### Code Quality Principles

1. **Readability**: Code should be self-documenting and easy to understand
2. **Consistency**: Follow established patterns and conventions throughout
3. **Simplicity**: Prefer simple, clear solutions over complex ones
4. **Maintainability**: Write code that is easy to modify and extend
5. **Testability**: Design code to be easily testable

### SOLID Principles

1. **Single Responsibility**: Each class should have one reason to change
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Subtypes must be substitutable for their base types
4. **Interface Segregation**: Clients shouldn't depend on interfaces they don't use
5. **Dependency Inversion**: Depend on abstractions, not concretions

## Python-Specific Standards

### Code Formatting

#### Line Length and Formatting

```python
# Maximum line length: 100 characters
# Use ruff for automatic formatting

# Good: Clear, readable formatting
def create_moderation_case(
    guild_id: int,
    user_id: int,
    moderator_id: int,
    case_type: CaseType,
    reason: str,
    expires_at: datetime | None = None,
) -> Case:
    """Create a moderation case with proper formatting."""
    pass

# Bad: Too long, hard to read
def create_moderation_case(guild_id: int, user_id: int, moderator_id: int, case_type: CaseType, reason: str, expires_at: datetime | None = None) -> Case:
    pass
```

#### Import Organization

```python
# Standard library imports (alphabetical)
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

# Third-party imports (alphabetical)
import discord
from discord.ext import commands
from loguru import logger
from prisma.enums import CaseType

# Local imports (alphabetical, grouped by module)
from tux.core.interfaces import IDatabaseService, IEmbedService
from tux.database.controllers import DatabaseController
from tux.utils.exceptions import ValidationError
```

### Naming Conventions

#### Variables and Functions

```python
# Use snake_case for variables and functions
user_id = 12345
guild_config = await get_guild_configuration(guild_id)

async def create_embed_message(title: str, description: str) -> discord.Embed:
    """Create an embed message with consistent styling."""
    pass

# Use descriptive names
# Good
def calculate_user_experience_points(user_id: int, message_count: int) -> int:
    pass

# Bad
def calc_xp(uid: int, mc: int) -> int:
    pass
```

#### Classes and Types

```python
# Use PascalCase for classes
class ModerationService:
    """Service for handling moderation operations."""
    pass

class UserRepository:
    """Repository for user data operations."""
    pass

# Use PascalCase for type aliases
UserID = int
GuildID = int
MessageContent = str
```

#### Constants

```python
# Use UPPER_SNAKE_CASE for constants
MAX_MESSAGE_LENGTH = 2000
DEFAULT_TIMEOUT_SECONDS = 30
EMBED_COLOR_SUCCESS = 0x00FF00

# Group related constants in classes
class EmbedColors:
    SUCCESS = 0x00FF00
    ERROR = 0xFF0000
    WARNING = 0xFFFF00
    INFO = 0x0099FF
```

#### Private Members

```python
class ServiceBase:
    def __init__(self):
        self._internal_cache = {}  # Private attribute
        self.__secret_key = "..."  # Name mangled attribute
    
    def _internal_method(self) -> None:
        """Private method for internal use."""
        pass
    
    def __private_method(self) -> None:
        """Highly private method with name mangling."""
        pass
```

### Type Annotations

#### Function Signatures

```python
# Always include type hints for parameters and return values
async def ban_user(
    guild_id: int,
    user_id: int,
    moderator_id: int,
    reason: str,
    duration: timedelta | None = None,
) -> ModerationResult:
    """Ban a user with optional duration."""
    pass

# Use Union types for multiple possible types
def process_user_input(input_data: str | int | discord.User) -> ProcessedInput:
    """Process various types of user input."""
    pass

# Use Optional for nullable values
def get_user_by_id(user_id: int) -> User | None:
    """Get user by ID, returns None if not found."""
    pass
```

#### Generic Types

```python
from typing import Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository pattern."""
    
    async def get_by_id(self, id: int) -> T | None:
        """Get entity by ID."""
        pass
    
    async def get_all(self) -> list[T]:
        """Get all entities."""
        pass

# Use specific collection types
def process_user_ids(user_ids: list[int]) -> dict[int, str]:
    """Process user IDs and return mapping."""
    pass
```

#### Complex Types

```python
from typing import Callable, Awaitable, Protocol

# Use Protocol for structural typing
class Moderatable(Protocol):
    id: int
    name: str
    
    async def ban(self, reason: str) -> None:
        """Ban this entity."""
        ...

# Use Callable for function parameters
async def execute_with_retry(
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 3,
) -> T:
    """Execute operation with retry logic."""
    pass
```

### Error Handling

#### Exception Hierarchy

```python
# Create specific exception types
class TuxError(Exception):
    """Base exception for Tux bot."""
    pass

class ValidationError(TuxError):
    """Raised when validation fails."""
    
    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        super().__init__(f"Validation failed for {field}: {message}")

class DatabaseError(TuxError):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, original_error: Exception):
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"Database operation '{operation}' failed: {original_error}")
```

#### Exception Handling Patterns

```python
# Use specific exception types
try:
    user = await user_repository.get_by_id(user_id)
except UserNotFoundError:
    logger.warning(f"User {user_id} not found")
    return None
except DatabaseError as e:
    logger.error(f"Database error retrieving user {user_id}: {e}")
    raise ServiceError("Failed to retrieve user") from e

# Always log errors with context
try:
    result = await risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        operation="risky_operation",
        user_id=user_id,
        guild_id=guild_id,
        error=str(e),
        exc_info=True
    )
    raise
```

#### Error Recovery

```python
async def robust_operation(user_id: int) -> Result:
    """Operation with graceful error handling."""
    try:
        return await primary_operation(user_id)
    except TemporaryError as e:
        logger.warning(f"Temporary error, retrying: {e}")
        await asyncio.sleep(1)
        return await fallback_operation(user_id)
    except PermanentError as e:
        logger.error(f"Permanent error, cannot recover: {e}")
        return ErrorResult(str(e))
```

### Async Programming

#### Async/Await Usage

```python
# Use async/await for I/O operations
async def fetch_user_data(user_id: int) -> UserData:
    """Fetch user data from database."""
    async with database.transaction():
        user = await database.user.find_unique(where={"id": user_id})
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return UserData.from_db(user)

# Don't use async for CPU-bound operations
def calculate_experience_points(messages: int, reactions: int) -> int:
    """Calculate experience points (CPU-bound)."""
    return messages * 10 + reactions * 5
```

#### Concurrency Patterns

```python
# Use asyncio.gather for concurrent operations
async def process_multiple_users(user_ids: list[int]) -> list[UserResult]:
    """Process multiple users concurrently."""
    tasks = [process_user(user_id) for user_id in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions in results
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Failed to process user: {result}")
            processed_results.append(ErrorResult(str(result)))
        else:
            processed_results.append(result)
    
    return processed_results
```

#### Resource Management

```python
# Use async context managers for resource cleanup
async def process_with_lock(user_id: int) -> None:
    """Process user with exclusive lock."""
    async with user_lock_manager.acquire(user_id):
        await perform_exclusive_operation(user_id)

# Proper database transaction handling
async def create_user_with_profile(user_data: UserData) -> User:
    """Create user and profile in single transaction."""
    async with database.transaction():
        user = await database.user.create(data=user_data.to_dict())
        profile = await database.profile.create(
            data={"user_id": user.id, "created_at": datetime.utcnow()}
        )
        return User(user, profile)
```

## Architecture Patterns

### Dependency Injection

#### Service Registration

```python
# Register services in container
def configure_services(container: ServiceContainer) -> None:
    """Configure dependency injection container."""
    # Singletons for stateful services
    container.register_singleton(IDatabaseService, DatabaseService)
    container.register_singleton(IConfigurationService, ConfigurationService)
    
    # Transients for stateless services
    container.register_transient(IValidationService, ValidationService)
    container.register_transient(IEmbedService, EmbedService)
    
    # Instances for pre-configured objects
    logger_instance = configure_logger()
    container.register_instance(ILogger, logger_instance)
```

#### Service Consumption

```python
class ModerationCog(BaseCog):
    """Moderation cog with dependency injection."""
    
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Services injected via BaseCog
    
    @commands.hybrid_command()
    async def ban(self, ctx: commands.Context, user: discord.User, *, reason: str) -> None:
        """Ban a user from the server."""
        # Use injected services
        if not self.validation_service.validate_reason(reason):
            raise ValidationError("reason", reason, "Reason is too short")
        
        result = await self.moderation_service.ban_user(
            guild_id=ctx.guild.id,
            user_id=user.id,
            moderator_id=ctx.author.id,
            reason=reason
        )
        
        embed = self.embed_service.create_success_embed(
            title="User Banned",
            description=f"{user.mention} has been banned."
        )
        await ctx.send(embed=embed)
```

### Repository Pattern

#### Interface Definition

```python
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    """Interface for user data operations."""
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def create(self, user_data: UserCreateData) -> User:
        """Create new user."""
        pass
    
    @abstractmethod
    async def update(self, user_id: int, updates: UserUpdateData) -> User:
        """Update existing user."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        pass
```

#### Repository Implementation

```python
class UserRepository(IUserRepository):
    """Prisma-based user repository implementation."""
    
    def __init__(self, db_client: DatabaseClient) -> None:
        self.db = db_client
    
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        try:
            db_user = await self.db.client.user.find_unique(
                where={"id": user_id},
                include={"profile": True, "cases": True}
            )
            return User.from_db(db_user) if db_user else None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise RepositoryError("Failed to retrieve user") from e
    
    async def create(self, user_data: UserCreateData) -> User:
        """Create new user."""
        try:
            db_user = await self.db.client.user.create(
                data=user_data.to_dict(),
                include={"profile": True}
            )
            return User.from_db(db_user)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise RepositoryError("Failed to create user") from e
```

### Service Layer Pattern

#### Service Interface

```python
class IModerationService(ABC):
    """Interface for moderation operations."""
    
    @abstractmethod
    async def ban_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        duration: timedelta | None = None,
    ) -> ModerationResult:
        """Ban a user from the guild."""
        pass
    
    @abstractmethod
    async def unban_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
    ) -> ModerationResult:
        """Unban a user from the guild."""
        pass
```

#### Service Implementation

```python
class ModerationService(IModerationService):
    """Service for moderation operations."""
    
    def __init__(
        self,
        user_repo: IUserRepository,
        case_repo: ICaseRepository,
        notification_service: INotificationService,
        validation_service: IValidationService,
    ) -> None:
        self.user_repo = user_repo
        self.case_repo = case_repo
        self.notification_service = notification_service
        self.validation_service = validation_service
    
    async def ban_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        duration: timedelta | None = None,
    ) -> ModerationResult:
        """Ban a user from the guild."""
        # Validate inputs
        if not self.validation_service.validate_reason(reason):
            raise ValidationError("reason", reason, "Invalid ban reason")
        
        # Check if user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        # Create moderation case
        case = await self.case_repo.create_case(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            case_type=CaseType.BAN,
            reason=reason,
            expires_at=datetime.utcnow() + duration if duration else None,
        )
        
        # Send notification
        await self.notification_service.notify_user_banned(user, reason)
        
        return ModerationResult(success=True, case=case)
```

## Documentation Standards

### Docstring Format

#### Function Documentation

```python
def calculate_user_level(experience_points: int, bonus_multiplier: float = 1.0) -> int:
    """Calculate user level based on experience points.
    
    Args:
        experience_points: Total experience points earned by the user
        bonus_multiplier: Multiplier for bonus experience (default: 1.0)
    
    Returns:
        The calculated user level as an integer
    
    Raises:
        ValueError: If experience_points is negative
        TypeError: If bonus_multiplier is not a number
    
    Example:
        >>> calculate_user_level(1000)
        10
        >>> calculate_user_level(1000, 1.5)
        12
    """
    if experience_points < 0:
        raise ValueError("Experience points cannot be negative")
    
    if not isinstance(bonus_multiplier, (int, float)):
        raise TypeError("Bonus multiplier must be a number")
    
    adjusted_xp = experience_points * bonus_multiplier
    return int(adjusted_xp ** 0.5)
```

#### Class Documentation

```python
class UserService:
    """Service for managing user operations and data.
    
    This service provides high-level operations for user management,
    including creation, updates, and retrieval of user information.
    It handles business logic and coordinates between repositories
    and external services.
    
    Attributes:
        user_repo: Repository for user data operations
        validation_service: Service for input validation
        cache_service: Service for caching user data
    
    Example:
        >>> user_service = UserService(user_repo, validation_service, cache_service)
        >>> user = await user_service.create_user(user_data)
        >>> updated_user = await user_service.update_user(user.id, updates)
    """
    
    def __init__(
        self,
        user_repo: IUserRepository,
        validation_service: IValidationService,
        cache_service: ICacheService,
    ) -> None:
        """Initialize the user service.
        
        Args:
            user_repo: Repository for user data operations
            validation_service: Service for input validation
            cache_service: Service for caching user data
        """
        self.user_repo = user_repo
        self.validation_service = validation_service
        self.cache_service = cache_service
```

### Code Comments

#### When to Comment

```python
# Good: Explain complex business logic
def calculate_moderation_score(user_history: list[Case]) -> float:
    """Calculate moderation score based on user history."""
    # Weight recent cases more heavily using exponential decay
    score = 0.0
    current_time = datetime.utcnow()
    
    for case in user_history:
        # Calculate time decay factor (cases older than 30 days have less impact)
        days_old = (current_time - case.created_at).days
        decay_factor = math.exp(-days_old / 30.0)
        
        # Apply case type multiplier
        case_weight = CASE_TYPE_WEIGHTS.get(case.case_type, 1.0)
        score += case_weight * decay_factor
    
    return score

# Bad: Obvious comments
def get_user_id(user: discord.User) -> int:
    # Get the user ID
    return user.id  # Return the ID
```

#### TODO and FIXME Comments

```python
# TODO: Implement caching for frequently accessed users
# TODO(username): Add support for custom ban durations
# FIXME: Race condition in concurrent user updates
# HACK: Temporary workaround for Discord API rate limiting
# NOTE: This behavior is required by Discord's ToS
```

## Testing Standards

### Test Organization

```python
# tests/unit/services/test_moderation_service.py
import pytest
from unittest.mock import AsyncMock, Mock

from tux.services.moderation import ModerationService
from tux.exceptions import ValidationError, UserNotFoundError

class TestModerationService:
    """Test suite for ModerationService."""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_case_repo(self):
        """Mock case repository."""
        return AsyncMock()
    
    @pytest.fixture
    def moderation_service(self, mock_user_repo, mock_case_repo):
        """Create moderation service with mocked dependencies."""
        return ModerationService(
            user_repo=mock_user_repo,
            case_repo=mock_case_repo,
            notification_service=AsyncMock(),
            validation_service=Mock(),
        )
```

### Test Naming and Structure

```python
class TestUserBanning:
    """Test user banning functionality."""
    
    async def test_ban_user_success(self, moderation_service, mock_user_repo):
        """Test successful user banning."""
        # Arrange
        guild_id = 12345
        user_id = 67890
        moderator_id = 11111
        reason = "Spam violation"
        
        mock_user = Mock()
        mock_user_repo.get_by_id.return_value = mock_user
        
        # Act
        result = await moderation_service.ban_user(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            reason=reason
        )
        
        # Assert
        assert result.success is True
        assert result.case is not None
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
    
    async def test_ban_user_invalid_reason_raises_validation_error(
        self, moderation_service
    ):
        """Test that invalid reason raises ValidationError."""
        # Arrange
        moderation_service.validation_service.validate_reason.return_value = False
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await moderation_service.ban_user(
                guild_id=12345,
                user_id=67890,
                moderator_id=11111,
                reason=""  # Invalid empty reason
            )
        
        assert "Invalid ban reason" in str(exc_info.value)
```

## Performance Guidelines

### Database Optimization

```python
# Good: Use select/include to fetch related data in one query
async def get_user_with_cases(user_id: int) -> UserWithCases:
    """Get user with all related cases."""
    user = await db.user.find_unique(
        where={"id": user_id},
        include={
            "cases": {
                "order_by": {"created_at": "desc"},
                "take": 50  # Limit to recent cases
            },
            "profile": True
        }
    )
    return UserWithCases.from_db(user)

# Bad: Multiple queries (N+1 problem)
async def get_user_with_cases_bad(user_id: int) -> UserWithCases:
    """Get user with cases (inefficient)."""
    user = await db.user.find_unique(where={"id": user_id})
    cases = await db.case.find_many(where={"user_id": user_id})
    profile = await db.profile.find_unique(where={"user_id": user_id})
    return UserWithCases(user, cases, profile)
```

### Caching Strategies

```python
from functools import lru_cache
import asyncio

class UserService:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_user_cached(self, user_id: int) -> User | None:
        """Get user with caching."""
        cache_key = f"user:{user_id}"
        
        # Check cache first
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cached_data
        
        # Fetch from database
        user = await self.user_repo.get_by_id(user_id)
        
        # Cache the result
        self._cache[cache_key] = (user, time.time())
        
        return user
    
    @lru_cache(maxsize=1000)
    def calculate_level(self, experience_points: int) -> int:
        """Calculate level with LRU cache for expensive computation."""
        return int(experience_points ** 0.5)
```

### Async Best Practices

```python
# Good: Use asyncio.gather for concurrent operations
async def process_multiple_guilds(guild_ids: list[int]) -> list[GuildResult]:
    """Process multiple guilds concurrently."""
    tasks = [process_guild(guild_id) for guild_id in guild_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# Good: Use async context managers for resource management
async def batch_update_users(updates: list[UserUpdate]) -> None:
    """Batch update users in transaction."""
    async with database.transaction():
        for update in updates:
            await database.user.update(
                where={"id": update.user_id},
                data=update.data
            )

# Bad: Sequential processing of async operations
async def process_guilds_sequential(guild_ids: list[int]) -> list[GuildResult]:
    """Process guilds sequentially (slow)."""
    results = []
    for guild_id in guild_ids:
        result = await process_guild(guild_id)  # Blocks other operations
        results.append(result)
    return results
```

## Security Guidelines

### Input Validation

```python
def validate_user_input(input_data: str) -> str:
    """Validate and sanitize user input."""
    # Check length
    if len(input_data) > MAX_INPUT_LENGTH:
        raise ValidationError("Input too long")
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>&"\'`]', '', input_data)
    
    # Check for SQL injection patterns
    dangerous_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT']
    upper_input = sanitized.upper()
    for pattern in dangerous_patterns:
        if pattern in upper_input:
            raise SecurityError("Potentially dangerous input detected")
    
    return sanitized.strip()

# Use parameterized queries (Prisma handles this automatically)
async def get_user_by_name(name: str) -> User | None:
    """Get user by name safely."""
    # Prisma automatically parameterizes queries
    return await db.user.find_first(
        where={"name": {"equals": name, "mode": "insensitive"}}
    )
```

### Permission Checks

```python
async def check_moderation_permissions(
    ctx: commands.Context,
    target_user: discord.User,
    action: str
) -> bool:
    """Check if user has permission to perform moderation action."""
    # Check if user is trying to moderate themselves
    if ctx.author.id == target_user.id:
        raise PermissionError(f"Cannot {action} yourself")
    
    # Check if target is server owner
    if target_user.id == ctx.guild.owner_id:
        raise PermissionError(f"Cannot {action} server owner")
    
    # Check role hierarchy
    if isinstance(target_user, discord.Member):
        if target_user.top_role >= ctx.author.top_role:
            raise PermissionError(f"Cannot {action} user with equal or higher role")
    
    return True
```

### Logging Security Events

```python
async def log_security_event(
    event_type: str,
    user_id: int,
    guild_id: int,
    details: dict[str, Any],
    severity: str = "INFO"
) -> None:
    """Log security-related events."""
    logger.log(
        severity,
        f"Security event: {event_type}",
        user_id=user_id,
        guild_id=guild_id,
        event_type=event_type,
        details=details,
        timestamp=datetime.utcnow().isoformat(),
        extra={
            "security_event": True,
            "requires_audit": severity in ["WARNING", "ERROR", "CRITICAL"]
        }
    )
```

## Conclusion

These coding standards provide a foundation for consistent, maintainable, and high-quality code in the Tux Discord bot project. All contributors should familiarize themselves with these standards and apply them consistently in their work.

Regular reviews and updates of these standards ensure they remain relevant and effective as the project evolves.
