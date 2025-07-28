# Service Interfaces Design

## Overview

This document defines the detailed interfaces and contracts for the service layer architecture. Each interface represents a clear boundary between different business domains and provides a contract for implementation.

## Base Service Infrastructure

### Core Interfaces

```python
from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class ServiceResult(Generic[T]):
    """Standard result wrapper for service operations"""
    
    def __init__(self, success: bool, data: Optional[T] = None, error: Optional['ServiceError'] = None):
        self.success = success
        self.data = data
        self.error = error
    
    @classmethod
    def success(cls, data: T) -> 'ServiceResult[T]':
        return cls(success=True, data=data)
    
    @classmethod
    def failure(cls, error: 'ServiceError') -> 'ServiceResult[T]':
        return cls(success=False, error=error)

class ErrorType(Enum):
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    DATABASE_ERROR = "database_error"
    RATE_LIMITED = "rate_limited"

class ServiceError:
    """Standard error structure for service operations"""
    
    def __init__(self, message: str, error_type: ErrorType, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}

class IService(Protocol):
    """Base interface for all services"""
    pass
```

## Domain Service Interfaces

### 1. Moderation Services

```python
from prisma.enums import CaseType
from dataclasses import dataclass

@dataclass
class ModerationResult:
    case_number: Optional[int]
    success: bool
    dm_sent: bool
    message: str

@dataclass
class UserRestrictions:
    is_banned: bool
    is_jailed: bool
    is_timed_out: bool
    is_poll_banned: bool
    is_snippet_banned: bool
    active_cases: List[int]

@dataclass
class CaseInfo:
    case_id: int
    case_number: int
    case_type: CaseType
    user_id: int
    moderator_id: int
    reason: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool

class IModerationService(IService):
    """Service for handling moderation actions"""
    
    @abstractmethod
    async def ban_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        duration: Optional[datetime] = None,
        purge_days: int = 0,
        silent: bool = False
    ) -> ServiceResult[ModerationResult]:
        """Ban a user from the guild"""
        pass
    
    @abstractmethod
    async def unban_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str
    ) -> ServiceResult[ModerationResult]:
        """Unban a user from the guild"""
        pass
    
    @abstractmethod
    async def kick_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        silent: bool = False
    ) -> ServiceResult[ModerationResult]:
        """Kick a user from the guild"""
        pass
    
    @abstractmethod
    async def timeout_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        duration: datetime,
        silent: bool = False
    ) -> ServiceResult[ModerationResult]:
        """Timeout a user in the guild"""
        pass
    
    @abstractmethod
    async def warn_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        silent: bool = False
    ) -> ServiceResult[ModerationResult]:
        """Issue a warning to a user"""
        pass
    
    @abstractmethod
    async def check_user_restrictions(
        self,
        guild_id: int,
        user_id: int
    ) -> ServiceResult[UserRestrictions]:
        """Check all active restrictions for a user"""
        pass
    
    @abstractmethod
    async def get_user_cases(
        self,
        guild_id: int,
        user_id: int,
        limit: int = 10,
        case_type: Optional[CaseType] = None
    ) -> ServiceResult[List[CaseInfo]]:
        """Get cases for a specific user"""
        pass

class ICaseService(IService):
    """Service for managing moderation cases"""
    
    @abstractmethod
    async def create_case(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        case_type: CaseType,
        reason: str,
        expires_at: Optional[datetime] = None
    ) -> ServiceResult[CaseInfo]:
        """Create a new moderation case"""
        pass
    
    @abstractmethod
    async def get_case(
        self,
        guild_id: int,
        case_number: int
    ) -> ServiceResult[CaseInfo]:
        """Get a specific case by number"""
        pass
    
    @abstractmethod
    async def update_case_reason(
        self,
        guild_id: int,
        case_number: int,
        new_reason: str,
        moderator_id: int
    ) -> ServiceResult[CaseInfo]:
        """Update the reason for a case"""
        pass
    
    @abstractmethod
    async def get_guild_cases(
        self,
        guild_id: int,
        limit: int = 50,
        offset: int = 0,
        case_type: Optional[CaseType] = None
    ) -> ServiceResult[List[CaseInfo]]:
        """Get cases for a guild with pagination"""
        pass
```

### 2. Snippet Services

```python
@dataclass
class SnippetInfo:
    snippet_id: int
    name: str
    content: str
    author_id: int
    guild_id: int
    created_at: datetime
    uses: int
    locked: bool
    alias: Optional[str] = None

@dataclass
class SnippetStats:
    total_snippets: int
    total_uses: int
    most_used: Optional[SnippetInfo]
    recent_snippets: List[SnippetInfo]

class ISnippetService(IService):
    """Service for managing code snippets"""
    
    @abstractmethod
    async def create_snippet(
        self,
        guild_id: int,
        name: str,
        content: str,
        author_id: int
    ) -> ServiceResult[SnippetInfo]:
        """Create a new snippet"""
        pass
    
    @abstractmethod
    async def create_snippet_alias(
        self,
        guild_id: int,
        alias_name: str,
        target_name: str,
        author_id: int
    ) -> ServiceResult[SnippetInfo]:
        """Create an alias for an existing snippet"""
        pass
    
    @abstractmethod
    async def get_snippet(
        self,
        guild_id: int,
        name: str
    ) -> ServiceResult[SnippetInfo]:
        """Get a snippet by name (including aliases)"""
        pass
    
    @abstractmethod
    async def update_snippet(
        self,
        guild_id: int,
        snippet_id: int,
        new_content: str,
        user_id: int
    ) -> ServiceResult[SnippetInfo]:
        """Update snippet content"""
        pass
    
    @abstractmethod
    async def delete_snippet(
        self,
        guild_id: int,
        snippet_id: int,
        user_id: int
    ) -> ServiceResult[bool]:
        """Delete a snippet"""
        pass
    
    @abstractmethod
    async def list_snippets(
        self,
        guild_id: int,
        limit: int = 20,
        offset: int = 0,
        author_id: Optional[int] = None
    ) -> ServiceResult[List[SnippetInfo]]:
        """List snippets with pagination"""
        pass
    
    @abstractmethod
    async def toggle_snippet_lock(
        self,
        guild_id: int,
        snippet_id: int,
        user_id: int
    ) -> ServiceResult[SnippetInfo]:
        """Toggle snippet lock status"""
        pass
    
    @abstractmethod
    async def increment_usage(
        self,
        guild_id: int,
        snippet_id: int
    ) -> ServiceResult[bool]:
        """Increment snippet usage counter"""
        pass
    
    @abstractmethod
    async def get_snippet_stats(
        self,
        guild_id: int
    ) -> ServiceResult[SnippetStats]:
        """Get snippet statistics for a guild"""
        pass

class ISnippetValidationService(IService):
    """Service for validating snippet operations"""
    
    @abstractmethod
    async def validate_snippet_name(
        self,
        name: str,
        guild_id: int
    ) -> ServiceResult[bool]:
        """Validate snippet name format and uniqueness"""
        pass
    
    @abstractmethod
    async def validate_snippet_content(
        self,
        content: str
    ) -> ServiceResult[bool]:
        """Validate snippet content"""
        pass
    
    @abstractmethod
    async def can_user_create_snippet(
        self,
        user_id: int,
        guild_id: int
    ) -> ServiceResult[bool]:
        """Check if user can create snippets"""
        pass
    
    @abstractmethod
    async def can_user_modify_snippet(
        self,
        user_id: int,
        snippet_id: int,
        guild_id: int
    ) -> ServiceResult[bool]:
        """Check if user can modify a specific snippet"""
        pass
```

### 3. Level Services

```python
@dataclass
class UserLevel:
    user_id: int
    guild_id: int
    level: int
    experience: int
    experience_to_next: int
    total_experience: int
    rank: Optional[int] = None

@dataclass
class LevelResult:
    previous_level: int
    new_level: int
    experience_gained: int
    level_up: bool
    new_total_experience: int

@dataclass
class LeaderboardEntry:
    user_id: int
    level: int
    total_experience: int
    rank: int

class ILevelService(IService):
    """Service for managing user levels and experience"""
    
    @abstractmethod
    async def add_experience(
        self,
        guild_id: int,
        user_id: int,
        amount: int
    ) -> ServiceResult[LevelResult]:
        """Add experience to a user"""
        pass
    
    @abstractmethod
    async def get_user_level(
        self,
        guild_id: int,
        user_id: int
    ) -> ServiceResult[UserLevel]:
        """Get user's current level information"""
        pass
    
    @abstractmethod
    async def set_user_level(
        self,
        guild_id: int,
        user_id: int,
        level: int,
        moderator_id: int
    ) -> ServiceResult[UserLevel]:
        """Set user's level (admin function)"""
        pass
    
    @abstractmethod
    async def get_leaderboard(
        self,
        guild_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> ServiceResult[List[LeaderboardEntry]]:
        """Get guild leaderboard"""
        pass
    
    @abstractmethod
    async def get_user_rank(
        self,
        guild_id: int,
        user_id: int
    ) -> ServiceResult[int]:
        """Get user's rank in the guild"""
        pass
    
    @abstractmethod
    async def calculate_level_from_experience(
        self,
        experience: int
    ) -> int:
        """Calculate level from total experience"""
        pass
    
    @abstractmethod
    async def calculate_experience_for_level(
        self,
        level: int
    ) -> int:
        """Calculate total experience needed for a level"""
        pass

class ILevelEventService(IService):
    """Service for handling level-related events"""
    
    @abstractmethod
    async def handle_level_up(
        self,
        guild_id: int,
        user_id: int,
        old_level: int,
        new_level: int
    ) -> ServiceResult[bool]:
        """Handle level up event"""
        pass
    
    @abstractmethod
    async def should_award_experience(
        self,
        guild_id: int,
        user_id: int,
        message_content: str
    ) -> ServiceResult[bool]:
        """Determine if experience should be awarded for a message"""
        pass
```

### 4. Guild Services

```python
@dataclass
class GuildConfig:
    guild_id: int
    prefix: str
    log_channels: Dict[str, int]
    disabled_commands: List[str]
    level_system_enabled: bool
    moderation_settings: Dict[str, Any]

@dataclass
class GuildStats:
    member_count: int
    total_messages: int
    total_commands_used: int
    active_users_today: int
    top_commands: List[tuple[str, int]]

class IGuildService(IService):
    """Service for managing guild settings and information"""
    
    @abstractmethod
    async def get_guild_config(
        self,
        guild_id: int
    ) -> ServiceResult[GuildConfig]:
        """Get guild configuration"""
        pass
    
    @abstractmethod
    async def update_guild_config(
        self,
        guild_id: int,
        config_updates: Dict[str, Any],
        moderator_id: int
    ) -> ServiceResult[GuildConfig]:
        """Update guild configuration"""
        pass
    
    @abstractmethod
    async def set_log_channel(
        self,
        guild_id: int,
        log_type: str,
        channel_id: int,
        moderator_id: int
    ) -> ServiceResult[bool]:
        """Set a log channel for specific events"""
        pass
    
    @abstractmethod
    async def get_guild_stats(
        self,
        guild_id: int
    ) -> ServiceResult[GuildStats]:
        """Get guild statistics"""
        pass
    
    @abstractmethod
    async def is_command_disabled(
        self,
        guild_id: int,
        command_name: str
    ) -> ServiceResult[bool]:
        """Check if a command is disabled in the guild"""
        pass
```

## Utility Services

### 1. Embed Service

```python
import discord
from tux.ui.embeds import EmbedType

class IEmbedService(IService):
    """Service for creating standardized embeds"""
    
    @abstractmethod
    def create_success_embed(
        self,
        title: str,
        description: str,
        user_name: Optional[str] = None,
        user_avatar: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Create a success embed"""
        pass
    
    @abstractmethod
    def create_error_embed(
        self,
        title: str,
        description: str,
        user_name: Optional[str] = None,
        user_avatar: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Create an error embed"""
        pass
    
    @abstractmethod
    def create_info_embed(
        self,
        title: str,
        description: str,
        user_name: Optional[str] = None,
        user_avatar: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Create an info embed"""
        pass
    
    @abstractmethod
    def create_moderation_embed(
        self,
        case_type: CaseType,
        case_number: int,
        moderator: str,
        target: str,
        reason: str,
        duration: Optional[str] = None,
        dm_sent: bool = False,
        **kwargs
    ) -> discord.Embed:
        """Create a moderation action embed"""
        pass
    
    @abstractmethod
    def create_case_embed(
        self,
        case_info: CaseInfo,
        **kwargs
    ) -> discord.Embed:
        """Create an embed for displaying case information"""
        pass
    
    @abstractmethod
    def create_snippet_embed(
        self,
        snippet: SnippetInfo,
        **kwargs
    ) -> discord.Embed:
        """Create an embed for displaying snippet information"""
        pass
    
    @abstractmethod
    def create_level_embed(
        self,
        user_level: UserLevel,
        level_up: bool = False,
        **kwargs
    ) -> discord.Embed:
        """Create an embed for level information"""
        pass
```

### 2. Validation Service

```python
from typing import Union
import discord

@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None

class IValidationService(IService):
    """Service for common validation operations"""
    
    @abstractmethod
    async def validate_user_permissions(
        self,
        user: discord.Member,
        required_level: int,
        guild_id: int
    ) -> ValidationResult:
        """Validate user has required permission level"""
        pass
    
    @abstractmethod
    def validate_string_length(
        self,
        text: str,
        min_length: int = 0,
        max_length: int = 2000,
        field_name: str = "input"
    ) -> ValidationResult:
        """Validate string length"""
        pass
    
    @abstractmethod
    def validate_snippet_name(
        self,
        name: str
    ) -> ValidationResult:
        """Validate snippet name format"""
        pass
    
    @abstractmethod
    def validate_reason(
        self,
        reason: str
    ) -> ValidationResult:
        """Validate moderation reason"""
        pass
    
    @abstractmethod
    async def validate_moderation_target(
        self,
        moderator: discord.Member,
        target: Union[discord.Member, discord.User],
        action: str
    ) -> ValidationResult:
        """Validate moderation action target"""
        pass
    
    @abstractmethod
    def validate_duration_string(
        self,
        duration: str
    ) -> ValidationResult:
        """Validate duration string format"""
        pass
```

### 3. Notification Service

```python
import discord

@dataclass
class NotificationResult:
    sent: bool
    error_message: Optional[str] = None

class INotificationService(IService):
    """Service for sending notifications and DMs"""
    
    @abstractmethod
    async def send_moderation_dm(
        self,
        user: Union[discord.Member, discord.User],
        action: str,
        reason: str,
        guild_name: str,
        duration: Optional[str] = None
    ) -> NotificationResult:
        """Send a moderation action DM to a user"""
        pass
    
    @abstractmethod
    async def send_level_up_notification(
        self,
        user: discord.Member,
        old_level: int,
        new_level: int,
        channel: discord.TextChannel
    ) -> NotificationResult:
        """Send a level up notification"""
        pass
    
    @abstractmethod
    async def send_reminder_notification(
        self,
        user: discord.User,
        reminder_text: str,
        created_at: datetime
    ) -> NotificationResult:
        """Send a reminder notification"""
        pass
    
    @abstractmethod
    async def log_to_channel(
        self,
        guild_id: int,
        log_type: str,
        embed: discord.Embed
    ) -> NotificationResult:
        """Send a log message to the appropriate channel"""
        pass
```

### 4. Cache Service

```python
from typing import Any, Optional
from datetime import timedelta

class ICacheService(IService):
    """Service for caching frequently accessed data"""
    
    @abstractmethod
    async def get(
        self,
        key: str
    ) -> Optional[Any]:
        """Get a value from cache"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set a value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        key: str
    ) -> bool:
        """Delete a value from cache"""
        pass
    
    @abstractmethod
    async def clear_pattern(
        self,
        pattern: str
    ) -> int:
        """Clear all keys matching a pattern"""
        pass
    
    @abstractmethod
    async def get_user_level_cached(
        self,
        guild_id: int,
        user_id: int
    ) -> Optional[UserLevel]:
        """Get cached user level data"""
        pass
    
    @abstractmethod
    async def cache_user_level(
        self,
        user_level: UserLevel,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Cache user level data"""
        pass
    
    @abstractmethod
    async def invalidate_user_cache(
        self,
        guild_id: int,
        user_id: int
    ) -> bool:
        """Invalidate all cached data for a user"""
        pass
```

## Service Implementation Guidelines

### 1. Error Handling

All services should:

- Return `ServiceResult` objects instead of raising exceptions
- Use appropriate `ErrorType` enums for categorization
- Include detailed error messages and context
- Log errors appropriately with structured logging

### 2. Validation

Services should:

- Validate all input parameters
- Use the `IValidationService` for common validations
- Return validation errors through `ServiceResult`
- Sanitize input data appropriately

### 3. Logging

Services should:

- Use structured logging with service context
- Include correlation IDs for request tracking
- Log performance metrics for slow operations
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

### 4. Caching

Services should:

- Use the `ICacheService` for frequently accessed data
- Implement appropriate cache invalidation strategies
- Consider cache warming for critical data
- Monitor cache hit rates and performance

### 5. Transactions

Services should:

- Use database transactions for multi-step operations
- Implement proper rollback mechanisms
- Handle transaction conflicts appropriately
- Use the repository pattern for data access

## Interface Evolution

### Versioning Strategy

- Interfaces should be versioned when breaking changes are needed
- Use semantic versioning for interface changes
- Maintain backward compatibility where possible
- Provide migration guides for breaking changes

### Extension Points

- Interfaces should be designed for extension
- Use composition over inheritance where appropriate
- Provide plugin mechanisms for custom behavior
- Support configuration-driven behavior changes

This interface design provides a comprehensive foundation for the service layer architecture, ensuring clear contracts, proper error handling, and extensibility for future requirements.
