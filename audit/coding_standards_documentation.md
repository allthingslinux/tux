# Coding Standards Documentation

## Overview

This document establishes comprehensive coding standards for the Tux Discord bot project. These standards ensure consistency, maintainability, and quality across the entire codebase while providing clear guidelines for contributors.

## 1. Python Code Standards

### 1.1 General Python Guidelines

#### Code Style and Formatting

```python
# Use Ruff for formatting - these are the key principles:

# Line length: 120 characters (configured in pyproject.toml)
def process_user_command(user_id: int, command: str, context: Optional[Context] = None) -> CommandResult:
    """Process user command with comprehensive error handling."""
    pass

# Import organization (handled by Ruff/isort)
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

from tux.dontrollers import DatabaseController
from tux.utils.embeds import EmbedFactory

# Use double quotes consistently
message = "This is the preferred quote style"
docstring = """This is a multi-line docstring
that follows the project standards."""
```

#### Naming Conventions

```python
# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30.0
API_BASE_URL = "https://api.example.com"

# Variables and functions: snake_case
user_id = 12345
command_name = "help"

def process_user_input(input_data: str) -> ProcessedInput:
    """Process user input data."""
    pass

async def fetch_user_data(user_id: int) -> Optional[UserData]:
    """Fetch user data from database."""
    pass

# Classes: PascalCase
class UserService:
    """Service for user-related operations."""
    pass

class CommandProcessor:
    """Process and execute user commands."""
    pass

# Private methods and attributes: leading underscore
class ExampleClass:
    def __init__(self):
        self._private_attribute = "internal use only"
    
    def _private_method(self) -> None:
        """Internal method not part of public API."""
        pass

# Type variables: PascalCase with T prefix
from typing import TypeVar
T = TypeVar('T')
UserT = TypeVar('UserT', bound='User')
```

#### Type Hints and Annotations

```python
from __future__ import annotations

from typing import Optional, Union, Dict, List, Any, Protocol, TypedDict
from collections.abc import Sequence, Mapping

# Function signatures with comprehensive type hints
async def get_user_by_id(
    user_id: int,
    *,
    include_roles: bool = False,
    timeout: float = 30.0,
) -> Optional[User]:
    """Retrieve user by ID with optional role information.
    
    Args:
        user_id: Discord user ID
        include_roles: Whether to include role information
        timeout: Request timeout in seconds
        
    Returns:
        User object if found, None otherwise
        
    Raises:
        DatabaseError: If database operation fails
        TimeoutError: If request times out
    """
    pass

# Use TypedDict for structured data
class UserData(TypedDict):
    id: int
    username: str
    discriminator: str
    avatar_url: Optional[str]
    roles: List[str]

# Use Protocol for interface definitions
class DatabaseProtocol(Protocol):
    async def get_user(self, user_id: int) -> Optional[User]: ...
    async def save_user(self, user: User) -> None: ...

# Generic types
from typing import Generic, TypeVar

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository pattern."""
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    async def save(self, entity: T) -> T:
        """Save entity to database."""
        pass
```

### 1.2 Documentation Standards

#### Docstring Format (Google/Numpy Style)

```python
def complex_calculation(
    data: List[float],
    threshold: float = 0.5,
    *,
    normalize: bool = True,
    method: str = "standard",
) -> Dict[str, Any]:
    """Perform complex calculation on numerical data.
    
    This function processes numerical data using various algorithms
    to produce statistical analysis results.
    
    Args:
        data: List of numerical values to process
        threshold: Minimum threshold for inclusion (default: 0.5)
        normalize: Whether to normalize results (default: True)
        method: Calculation method to use ("standard" or "advanced")
        
    Returns:
        Dictionary containing:
            - mean: Average value
            - std: Standard deviation
            - count: Number of processed items
            - outliers: List of outlier values
            
    Raises:
        ValueError: If data is empty or contains invalid values
        TypeError: If data contains non-numeric values
        
    Example:
        >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> result = complex_calculation(data, threshold=0.3)
        >>> print(result['mean'])
        3.0
        
    Note:
        This function modifies the input data if normalize=True.
        Make a copy if you need to preserve the original data.
    """
    pass

class UserService:
    """Service for managing user-related operations.
    
    This service provides a high-level interface for user management,
    including CRUD operations, validation, and business logic.
    
    Attributes:
        db: Database controller instance
        cache: User data cache
        
    Example:
        >>> service = UserService(db_controller)
        >>> user = await service.get_user(12345)
        >>> if user:
        ...     print(f"Found user: {user.username}")
    """
    
    def __init__(self, db: DatabaseController) -> None:
        """Initialize user service.
        
        Args:
            db: Database controller for data operations
        """
        self.db = db
        self.cache: Dict[int, User] = {}
```

#### Inline Comments

```python
def process_command(command: str) -> CommandResult:
    """Process user command with validation and execution."""
    
    # Validate command format before processing
    if not command.strip():
        return CommandResult(success=False, error="Empty command")
    
    # Parse command components (name, arguments, flags)
    parts = command.split()
    command_name = parts[0].lower()
    arguments = parts[1:] if len(parts) > 1 else []
    
    # Check if command exists in registry
    if command_name not in COMMAND_REGISTRY:
        return CommandResult(
            success=False, 
            error=f"Unknown command: {command_name}"
        )
    
    # Execute command with error handling
    try:
        result = COMMAND_REGISTRY[command_name].execute(arguments)
        return CommandResult(success=True, data=result)
    except CommandError as e:
        # Log error for debugging but return user-friendly message
        logger.error("Command execution failed", command=command_name, error=e)
        return CommandResult(success=False, error="Command execution failed")
```

### 1.3 Error Handling Standards

#### Exception Hierarchy

```python
# Base exception for all Tux-related errors
class TuxError(Exception):
    """Base exception for Tux Discord bot."""
    
    def __init__(self, message: str, *, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code

# Specific exception categories
class ValidationError(TuxError):
    """Raised when input validation fails."""
    pass

class DatabaseError(TuxError):
    """Raised when database operations fail."""
    pass

class PermissionError(TuxError):
    """Raised when user lacks required permissions."""
    pass

class ExternalServiceError(TuxError):
    """Raised when external service calls fail."""
    pass

# Usage in functions
async def validate_user_input(input_data: str) -> ValidatedInput:
    """Validate user input with comprehensive checks."""
    if not input_data.strip():
        raise ValidationError("Input cannot be empty", code="EMPTY_INPUT")
    
    if len(input_data) > MAX_INPUT_LENGTH:
        raise ValidationError(
            f"Input too long (max {MAX_INPUT_LENGTH} characters)",
            code="INPUT_TOO_LONG"
        )
    
    # Additional validation logic...
    return ValidatedInput(data=input_data.strip())
```

#### Error Handling Patterns

```python
# Standard error handling pattern
async def safe_database_operation(user_id: int) -> Optional[User]:
    """Safely perform database operation with proper error handling."""
    try:
        user = await db.user.find_unique(where={"id": user_id})
        return user
    except PrismaError as e:
        logger.error(
            "Database operation failed",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise DatabaseError("Failed to retrieve user data") from e
    except Exception as e:
        logger.error(
            "Unexpected error in database operation",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise TuxError("Unexpected error occurred") from e

# Context manager for resource management
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_transaction():
    """Context manager for database transactions."""
    transaction = await db.tx()
    try:
        yield transaction
        await transaction.commit()
    except Exception:
        await transaction.rollback()
        raise
    finally:
        await transaction.disconnect()

# Usage
async def update_user_safely(user_id: int, data: UserUpdateData) -> User:
    """Update user with transaction safety."""
    async with database_transaction() as tx:
        user = await tx.user.find_unique(where={"id": user_id})
        if not user:
            raise ValidationError(f"User {user_id} not found")
        
        updated_user = await tx.user.update(
            where={"id": user_id},
            data=data.dict()
        )
        return updated_user
```

## 2. Discord Bot Specific Standards

### 2.1 Cog Structure Standards

#### Standard Cog Template

```python
"""Example cog demonstrating standard patterns and practices."""

from __future__ import annotations

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.services.user_service import UserService
from tux.utils.embeds import EmbedFactory
from tux.utils.exceptions import TuxError, ValidationError

logger = logging.getLogger(__name__)

class ExampleCog(commands.Cog):
    """Example cog demonstrating standard patterns.
    
    This cog provides example commands and demonstrates proper
    error handling, logging, and user interaction patterns.
    """
    
    def __init__(self, bot: Tux) -> None:
        """Initialize the example cog.
        
        Args:
            bot: The Tux bot instance
        """
        self.bot = bot
        
        # Use dependency injection for services
        self.user_service = bot.container.get(UserService)
        self.embed_factory = bot.container.get(EmbedFactory)
        
        # Direct database access should be avoided in favor of services
        self.db = bot.container.get(DatabaseController)
    
    @app_commands.command(name="example", description="Example command demonstrating best practices")
    @app_commands.describe(
        user="The user to perform the action on",
        option="Optional parameter with default value"
    )
    async def example_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        option: Optional[str] = None,
    ) -> None:
        """Example command with proper error handling and user feedback.
        
        Args:
            interaction: Discord interaction object
            user: Target user for the command
            option: Optional parameter
        """
        # Defer response for operations that might take time
        await interaction.response.defer(ephemeral=False)
        
        try:
            # Validate inputs
            if user.bot:
                raise ValidationError("Cannot perform action on bot users")
            
            # Perform business logic through service layer
            result = await self.user_service.process_user_action(
                user_id=user.id,
                action_type="example",
                options={"option": option} if option else None
            )
            
            # Create success response
            embed = self.embed_factory.create_success_embed(
                title="Action Completed",
                description=f"Successfully processed action for {user.mention}",
                fields=[
                    ("Result", result.summary, False),
                    ("Details", result.details, True),
                ]
            )
            
            await interaction.followup.send(embed=embed)
            
        except ValidationError as e:
            # Handle validation errors with user-friendly messages
            embed = self.embed_factory.create_error_embed(
                title="Invalid Input",
                description=str(e)
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except TuxError as e:
            # Handle known application errors
            logger.warning(
                "Command execution failed",
                command="example",
                user_id=interaction.user.id,
                target_user_id=user.id,
                error=str(e)
            )
            
            embed = self.embed_factory.create_error_embed(
                title="Command Failed",
                description="An error occurred while processing your request."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(
                "Unexpected error in example command",
                command="example",
                user_id=interaction.user.id,
                target_user_id=user.id,
                error=str(e),
                exc_info=True
            )
            
            embed = self.embed_factory.create_error_embed(
                title="Unexpected Error",
                description="An unexpected error occurred. Please try again later."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Handle member join events.
        
        Args:
            member: The member who joined
        """
        try:
            # Process new member through service layer
            await self.user_service.handle_member_join(member)
            
            logger.info(
                "New member processed",
                guild_id=member.guild.id,
                user_id=member.id,
                username=member.name
            )
            
        except Exception as e:
            logger.error(
                "Failed to process new member",
                guild_id=member.guild.id,
                user_id=member.id,
                error=str(e),
                exc_info=True
            )

async def setup(bot: Tux) -> None:
    """Set up the example cog.
    
    Args:
        bot: The Tux bot instance
    """
    await bot.add_cog(ExampleCog(bot))
```

### 2.2 Database Interaction Standards

#### Repository Pattern Implementation

```python
"""User repository implementing standard database patterns."""

from __future__ import annotations

import logging
from typing import Optional, List
from datetime import datetime

from prisma.errors import PrismaError

from tux.database.controllers import DatabaseController
from tux.database.models import User, UserCreateData, UserUpdateData
from tux.utils.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for user data operations.
    
    Provides a clean interface for user-related database operations
    with proper error handling and logging.
    """
    
    def __init__(self, db: DatabaseController) -> None:
        """Initialize user repository.
        
        Args:
            db: Database controller instance
        """
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            User object if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            user = await self.db.user.find_unique(where={"id": user_id})
            return user
        except PrismaError as e:
            logger.error(
                "Failed to retrieve user by ID",
                user_id=user_id,
                error=str(e)
            )
            raise DatabaseError(f"Failed to retrieve user {user_id}") from e
    
    async def create(self, user_data: UserCreateData) -> User:
        """Create new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            ValidationError: If user data is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Validate required fields
            if not user_data.username:
                raise ValidationError("Username is required")
            
            user = await self.db.user.create(data=user_data.dict())
            
            logger.info(
                "User created successfully",
                user_id=user.id,
                username=user.username
            )
            
            return user
            
        except PrismaError as e:
            logger.error(
                "Failed to create user",
                username=user_data.username,
                error=str(e)
            )
            raise DatabaseError("Failed to create user") from e
    
    async def update(self, user_id: int, user_data: UserUpdateData) -> User:
        """Update existing user.
        
        Args:
            user_id: User ID to update
            user_data: Updated user data
            
        Returns:
            Updated user object
            
        Raises:
            ValidationError: If user not found or data invalid
            DatabaseError: If database operation fails
        """
        try:
            # Check if user exists
            existing_user = await self.get_by_id(user_id)
            if not existing_user:
                raise ValidationError(f"User {user_id} not found")
            
            # Update with timestamp
            update_data = user_data.dict()
            update_data["updated_at"] = datetime.utcnow()
            
            user = await self.db.user.update(
                where={"id": user_id},
                data=update_data
            )
            
            logger.info(
                "User updated successfully",
                user_id=user_id,
                updated_fields=list(user_data.dict().keys())
            )
            
            return user
            
        except ValidationError:
            raise
        except PrismaError as e:
            logger.error(
                "Failed to update user",
                user_id=user_id,
                error=str(e)
            )
            raise DatabaseError(f"Failed to update user {user_id}") from e
    
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if user was deleted, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.user.delete(where={"id": user_id})
            
            if result:
                logger.info("User deleted successfully", user_id=user_id)
                return True
            else:
                logger.warning("User not found for deletion", user_id=user_id)
                return False
                
        except PrismaError as e:
            logger.error(
                "Failed to delete user",
                user_id=user_id,
                error=str(e)
            )
            raise DatabaseError(f"Failed to delete user {user_id}") from e
    
    async def find_by_username(self, username: str) -> List[User]:
        """Find users by username pattern.
        
        Args:
            username: Username pattern to search for
            
        Returns:
            List of matching users
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            users = await self.db.user.find_many(
                where={"username": {"contains": username, "mode": "insensitive"}}
            )
            return users
        except PrismaError as e:
            logger.error(
                "Failed to search users by username",
                username=username,
                error=str(e)
            )
            raise DatabaseError("Failed to search users") from e
```

### 2.3 Service Layer Standards

#### Service Implementation Pattern

```python
"""User service implementing business logic layer."""

from __future__ import annotations

import logging
from typing import Optional, List
from datetime import datetime, timedelta

import discord

from tux.database.repositories.user_repository import UserRepository
from tux.database.models import User, UserCreateData, UserUpdateData
from tux.utils.exceptions import ValidationError, BusinessLogicError
from tux.utils.cache import CacheManager

logger = logging.getLogger(__name__)

class UserService:
    """Service for user-related business logic.
    
    Provides high-level operations for user management,
    including validation, caching, and business rules.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        cache_manager: CacheManager,
    ) -> None:
        """Initialize user service.
        
        Args:
            user_repository: Repository for user data operations
            cache_manager: Cache manager for performance optimization
        """
        self.user_repo = user_repository
        self.cache = cache_manager
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user with caching.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            User object if found, None otherwise
        """
        # Check cache first
        cache_key = f"user:{user_id}"
        cached_user = await self.cache.get(cache_key)
        if cached_user:
            return cached_user
        
        # Fetch from database
        user = await self.user_repo.get_by_id(user_id)
        if user:
            # Cache for 5 minutes
            await self.cache.set(cache_key, user, ttl=300)
        
        return user
    
    async def create_user_from_discord(self, discord_user: discord.User) -> User:
        """Create user from Discord user object.
        
        Args:
            discord_user: Discord user object
            
        Returns:
            Created user object
            
        Raises:
            ValidationError: If user data is invalid
            BusinessLogicError: If user already exists
        """
        # Check if user already exists
        existing_user = await self.get_user(discord_user.id)
        if existing_user:
            raise BusinessLogicError(f"User {discord_user.id} already exists")
        
        # Create user data
        user_data = UserCreateData(
            id=discord_user.id,
            username=discord_user.name,
            discriminator=discord_user.discriminator,
            avatar_url=discord_user.avatar.url if discord_user.avatar else None,
            created_at=datetime.utcnow(),
        )
        
        # Validate business rules
        await self._validate_user_creation(user_data)
        
        # Create user
        user = await self.user_repo.create(user_data)
        
        # Invalidate cache
        await self.cache.delete(f"user:{user.id}")
        
        logger.info(
            "User created from Discord",
            user_id=user.id,
            username=user.username
        )
        
        return user
    
    async def update_user_activity(self, user_id: int) -> None:
        """Update user's last activity timestamp.
        
        Args:
            user_id: User ID to update
        """
        update_data = UserUpdateData(last_activity=datetime.utcnow())
        await self.user_repo.update(user_id, update_data)
        
        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")
    
    async def handle_member_join(self, member: discord.Member) -> User:
        """Handle new member joining the server.
        
        Args:
            member: Discord member object
            
        Returns:
            User object (created or existing)
        """
        try:
            # Try to get existing user
            user = await self.get_user(member.id)
            if user:
                # Update existing user info
                update_data = UserUpdateData(
                    username=member.name,
                    discriminator=member.discriminator,
                    avatar_url=member.avatar.url if member.avatar else None,
                    last_seen=datetime.utcnow(),
                )
                user = await self.user_repo.update(member.id, update_data)
            else:
                # Create new user
                user = await self.create_user_from_discord(member)
            
            # Apply welcome logic
            await self._apply_welcome_logic(member, user)
            
            return user
            
        except Exception as e:
            logger.error(
                "Failed to handle member join",
                guild_id=member.guild.id,
                user_id=member.id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _validate_user_creation(self, user_data: UserCreateData) -> None:
        """Validate user creation data.
        
        Args:
            user_data: User data to validate
            
        Raises:
            ValidationError: If validation fails
        """
        if not user_data.username:
            raise ValidationError("Username cannot be empty")
        
        if len(user_data.username) > 32:
            raise ValidationError("Username too long (max 32 characters)")
        
        # Additional business rule validations...
    
    async def _apply_welcome_logic(self, member: discord.Member, user: User) -> None:
        """Apply welcome logic for new members.
        
        Args:
            member: Discord member object
            user: User database object
        """
        # Welcome message, role assignment, etc.
        logger.info(
            "Welcome logic applied",
            guild_id=member.guild.id,
            user_id=user.id
        )
```

## 3. Architecture Decision Records (ADRs)

### 3.1 ADR Template

```markdown
# ADR-XXX: [Decision Title]

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-YYY]

## Context
Describe the problem that needs to be solved and the constraints that exist.

## Decision
Describe the solution that was chosen and why.

## Consequences
### Positive
- List the positive outcomes of this decision

### Negative
- List the negative outcomes or trade-offs

### Neutral
- List neutral consequences or implementation details

## Alternatives Considered
Describe other options that were considered and why they were rejected.

## Implementation Notes
Any specific implementation details or requirements.

## References
- Links to relevant documentation
- Related ADRs
- External resources
```

### 3.2 Key ADRs for Tux Project

#### ADR-001: Dependency Injection Container

```markdown
# ADR-001: Dependency Injection Container Selection

## Status
Accepted

## Context
The Tux codebase has repetitive initialization patterns where every cog manually instantiates its dependencies (DatabaseController, services, etc.). This creates tight coupling and makes testing difficult.

## Decision
Implement a lightweight dependency injection container that:
- Manages service lifecycles automatically
- Enables constructor injection for better testability
- Reduces boilerplate code across cogs
- Provides clear dependency graphs

## Consequences
### Positive
- Reduced code duplication in cog initialization
- Improved testability through dependency injection
- Clearer separation of concerns
- Easier to mock dependencies for testing

### Negative
- Additional complexity in service registration
- Learning curve for contributors
- Potential performance overhead (minimal)

### Neutral
- Requires refactoring existing cogs gradually
- Need to establish service registration patterns

## Alternatives Considered
1. **Manual dependency management**: Current approach, leads to tight coupling
2. **Full DI framework (dependency-injector)**: Too heavy for our needs
3. **Factory pattern**: More complex than needed for our use case

## Implementation Notes
- Use simple container with get/register methods
- Support singleton and transient lifetimes
- Integrate with bot initialization process
- Provide clear migration path for existing cogs
```

#### ADR-002: Error Handling Strategy

```markdown
# ADR-002: Standardized Error Handling Strategy

## Status
Accepted

## Context
Error handling across the codebase is inconsistent, leading to poor user experience and difficult debugging. Different cogs handle errors differently, and there's no standard way to present errors to users.

## Decision
Implement a structured error handling system with:
- Custom exception hierarchy for different error types
- Centralized error processing and logging
- Consistent user-facing error messages
- Proper Sentry integration with context

## Consequences
### Positive
- Consistent error handling across all cogs
- Better user experience with clear error messages
- Improved debugging with structured logging
- Better error tracking and monitoring

### Negative
- Requires refactoring existing error handling
- Additional complexity in error processing
- Need to train contributors on new patterns

### Neutral
- Establishes clear error handling patterns
- Requires documentation and examples

## Implementation Notes
- Create TuxError base class with error codes
- Implement error middleware for Discord interactions
- Standardize error message formatting
- Integrate with existing Sentry setup
```

## 4. Development Workflow Standards

### 4.1 Git Workflow

#### Branch Naming Conventions

```bash
# Feature branches
feat/user-profile-command
feat/database-migration-system
feat/advanced-moderation-tools

# Bug fix branches
fix/database-connection-timeout
fix/command-permission-bypass
fix/memory-leak-in-cache

# Refactoring branches
refactor/extract-user-service
refactor/simplify-embed-creation
refactor/improve-error-handling

# Documentation branches
docs/update-api-documentation
docs/add-deployment-guide
docs/improve-contribution-guide

# Maintenance branches
chore/update-dependencies
chore/improve-ci-pipeline
chore/cleanup-deprecated-code
```

#### Commit Message Standards

```bash
# Format: type(scope): description
# 
# Types: feat, fix, docs, style, refactor, test, chore
# Scope: Optional, indicates the area of change
# Description: Imperative mood, lowercase, no period

# Examples:
feat(commands): add user profile display command
fix(database): resolve connection pool exhaustion
refactor(services): extract user validation logic
docs(readme): update installation instructions
test(integration): add user command integration tests
chore(deps): update discord.py to v2.4.0

# For breaking changes:
feat(api)!: change user service interface

BREAKING CHANGE: UserService.get_user() now returns Optional[User] instead of User
```

### 4.2 Code Review Workflow

#### Pre-Review Checklist

```markdown
## Author Checklist (before requesting review)
- [ ] All tests pass locally
- [ ] Code follows project style guidelines
- [ ] Documentation updated for public API changes
- [ ] Self-review completed
- [ ] PR description is complete and accurate
- [ ] Breaking changes documented
- [ ] Performance impact assessed
```

#### Review Process

1. **Automated Checks**: All CI checks must pass
2. **Self Review**: Author reviews their own changes
3. **Peer Review**: At least one team member review required
4. **Specialized Review**: Security/performance review for relevant changes
5. **Final Approval**: Maintainer approval for merge

### 4.3 Testing Standards

#### Test Organization

```python
# tests/unit/services/test_user_service.py
"""Unit tests for UserService."""

import pytest
from unittest.mock import AsyncMock, Mock

from tux.services.user_service import UserService
from tux.utils.exceptions import ValidationError, BusinessLogicError

class TestUserService:
    """Test suite for UserService."""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_cache(self):
        """Mock cache manager."""
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_user_repo, mock_cache):
        """UserService instance with mocked dependencies."""
        return UserService(mock_user_repo, mock_cache)
    
    async def test_get_user_from_cache(self, user_service, mock_cache):
        """Test getting user from cache."""
        # Arrange
        user_id = 12345
        cached_user = Mock()
        mock_cache.get.return_value = cached_user
        
        # Act
        result = await user_service.get_user(user_id)
        
        # Assert
        assert result == cached_user
        mock_cache.get.assert_called_once_with(f"user:{user_id}")
    
    async def test_create_user_already_exists(self, user_service):
        """Test creating user that already exists."""
        # Arrange
        discord_user = Mock()
        discord_user.id = 12345
        user_service.get_user = AsyncMock(return_value=Mock())
        
        # Act & Assert
        with pytest.raises(BusinessLogicError, match="already exists"):
            await user_service.create_user_from_discord(discord_user)
```

#### Test Categories

- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test performance characteristics
- **Security Tests**: Test security measures

This comprehensive coding standards documentation provides clear guidelines for maintaining consistency and quality across the Tux Discord bot codebase while supporting effective collaboration and contribution.
