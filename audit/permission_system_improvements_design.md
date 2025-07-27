# Permission System Improvements Design

## Overview

This document outlines the design for enhancing the existing permission system in the Tux Discord bot. The current system provides a solid foundation with numeric permission levels (0-9), but lacks granular control, comprehensive audit trails, and context-aware permission checks. This design addresses these limitations while maintaining backward compatibility.

## Current System Analysis

### Existing Permission Architecture

The current permission system (`tux/utils/checks.py`) implements:

1. **Numeric Permission Levels (0-9)**:
   - 0: Member (default)
   - 1: Support
   - 2: Junior Moderator
   - 3: Moderator
   - 4: Senior Moderator
   - 5: Administrator
   - 6: Head Administrator
   - 7: Server Owner
   - 8: Sys Admin
   - 9: Bot Owner

2. **Role-Based Access Control**:
   - Guild-specific role assignments for levels 0-7
   - System-wide assignments for levels 8-9
   - Database-stored role mappings per guild

3. **Decorator-Based Checks**:
   - `@checks.has_pl(level)` for prefix commands
   - `@checks.ac_has_pl(level)` for slash commands
   - Support for "or higher" permission checks

### Current Strengths

1. **Simple and Intuitive**: Easy to understand numeric hierarchy
2. **Guild-Specific**: Configurable per Discord server
3. **Comprehensive Coverage**: Used across all sensitive commands
4. **Performance**: Efficient database queries with caching
5. **Error Handling**: Clear error messages for permission failures

### Identified Limitations

1. **Lack of Granularity**: Only broad permission levels, no specific permissions
2. **Limited Context Awareness**: No consideration of target objects or channels
3. **Minimal Audit Trail**: Basic logging without comprehensive tracking
4. **No Temporary Permissions**: Cannot grant time-limited access
5. **Static Role Mapping**: No dynamic permission assignment
6. **Limited Delegation**: No ability to delegate specific permissions

## Enhanced Permission System Design

### Core Architecture

```python
# tux/security/permissions/__init__.py
from .engine import PermissionEngine
from .models import Permission, PermissionGrant, PermissionContext
from .decorators import requires_permission, requires_level
from .audit import PermissionAuditLogger
from .exceptions import PermissionDeniedError, InvalidPermissionError

__all__ = [
    "PermissionEngine",
    "Permission",
    "PermissionGrant", 
    "PermissionContext",
    "requires_permission",
    "requires_level",
    "PermissionAuditLogger",
    "PermissionDeniedError",
    "InvalidPermissionError"
]
```

### Permission Model

```python
# tux/security/permissions/models.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

class PermissionScope(Enum):
    """Defines the scope where a permission applies."""
    GLOBAL = "global"           # Bot-wide permission
    GUILD = "guild"             # Guild-specific permission
    CHANNEL = "channel"         # Channel-specific permission
    CATEGORY = "category"       # Category-specific permission
    THREAD = "thread"           # Thread-specific permission

class Permission(Enum):
    """Granular permissions for specific actions."""
    
    # Moderation permissions
    MODERATE_MESSAGES = "moderate.messages"
    MODERATE_MEMBERS = "moderate.members"
    MODERATE_CHANNELS = "moderate.channels"
    MODERATE_ROLES = "moderate.roles"
    
    # Administrative permissions
    MANAGE_GUILD_CONFIG = "admin.guild_config"
    MANAGE_BOT_CONFIG = "admin.bot_config"
    MANAGE_PERMISSIONS = "admin.permissions"
    MANAGE_AUDIT_LOGS = "admin.audit_logs"
    
    # Utility permissions
    USE_EVAL = "utility.eval"
    USE_SYSTEM_COMMANDS = "utility.system"
    MANAGE_SNIPPETS = "utility.snippets"
    
    # Service permissions
    MANAGE_STARBOARD = "service.starboard"
    MANAGE_LEVELS = "service.levels"
    MANAGE_AFK = "service.afk"
    
    # View permissions
    VIEW_AUDIT_LOGS = "view.audit_logs"
    VIEW_SYSTEM_INFO = "view.system_info"
    VIEW_USER_INFO = "view.user_info"

@dataclass
class PermissionContext:
    """Context information for permission checks."""
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    category_id: Optional[int] = None
    thread_id: Optional[int] = None
    target_user_id: Optional[int] = None
    target_role_id: Optional[int] = None
    additional_data: Dict[str, Any] = None

@dataclass
class PermissionGrant:
    """Represents a granted permission."""
    user_id: int
    permission: Permission
    scope: PermissionScope
    scope_id: Optional[int] = None  # Guild/Channel/etc ID
    granted_by: int = None
    granted_at: datetime = None
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = None
    
    def is_expired(self) -> bool:
        """Check if this permission grant has expired."""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at
    
    def is_valid_for_context(self, context: PermissionContext) -> bool:
        """Check if this grant applies to the given context."""
        if self.scope == PermissionScope.GLOBAL:
            return True
        elif self.scope == PermissionScope.GUILD:
            return self.scope_id == context.guild_id
        elif self.scope == PermissionScope.CHANNEL:
            return self.scope_id == context.channel_id
        elif self.scope == PermissionScope.CATEGORY:
            return self.scope_id == context.category_id
        elif self.scope == PermissionScope.THREAD:
            return self.scope_id == context.thread_id
        return False

class PermissionLevel(Enum):
    """Traditional permission levels for backward compatibility."""
    MEMBER = 0
    SUPPORT = 1
    JUNIOR_MODERATOR = 2
    MODERATOR = 3
    SENIOR_MODERATOR = 4
    ADMINISTRATOR = 5
    HEAD_ADMINISTRATOR = 6
    SERVER_OWNER = 7
    SYS_ADMIN = 8
    BOT_OWNER = 9
```

### Permission Engine

```python
# tux/security/permissions/engine.py
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from tux.database.controllers import DatabaseController
from .models import Permission, PermissionGrant, PermissionContext, PermissionScope, PermissionLevel
from .audit import PermissionAuditLogger
from .cache import PermissionCache

class PermissionEngine:
    """Core permission checking and management engine."""
    
    def __init__(self):
        self.db = DatabaseController()
        self.audit_logger = PermissionAuditLogger()
        self.cache = PermissionCache()
        self._permission_mappings = self._initialize_permission_mappings()
    
    def _initialize_permission_mappings(self) -> Dict[PermissionLevel, Set[Permission]]:
        """Map traditional permission levels to granular permissions."""
        return {
            PermissionLevel.MEMBER: set(),
            PermissionLevel.SUPPORT: {
                Permission.VIEW_USER_INFO,
            },
            PermissionLevel.JUNIOR_MODERATOR: {
                Permission.MODERATE_MESSAGES,
                Permission.MANAGE_AFK,
                Permission.VIEW_USER_INFO,
            },
            PermissionLevel.MODERATOR: {
                Permission.MODERATE_MESSAGES,
                Permission.MODERATE_MEMBERS,
                Permission.MANAGE_AFK,
                Permission.MANAGE_SNIPPETS,
                Permission.VIEW_USER_INFO,
                Permission.VIEW_AUDIT_LOGS,
            },
            PermissionLevel.SENIOR_MODERATOR: {
                Permission.MODERATE_MESSAGES,
                Permission.MODERATE_MEMBERS,
                Permission.MODERATE_CHANNELS,
                Permission.MANAGE_AFK,
                Permission.MANAGE_SNIPPETS,
                Permission.MANAGE_LEVELS,
                Permission.VIEW_USER_INFO,
                Permission.VIEW_AUDIT_LOGS,
            },
            PermissionLevel.ADMINISTRATOR: {
                Permission.MODERATE_MESSAGES,
                Permission.MODERATE_MEMBERS,
                Permission.MODERATE_CHANNELS,
                Permission.MODERATE_ROLES,
                Permission.MANAGE_GUILD_CONFIG,
                Permission.MANAGE_AFK,
                Permission.MANAGE_SNIPPETS,
                Permission.MANAGE_LEVELS,
                Permission.MANAGE_STARBOARD,
                Permission.VIEW_USER_INFO,
                Permission.VIEW_AUDIT_LOGS,
                Permission.VIEW_SYSTEM_INFO,
            },
            PermissionLevel.HEAD_ADMINISTRATOR: {
                Permission.MODERATE_MESSAGES,
                Permission.MODERATE_MEMBERS,
                Permission.MODERATE_CHANNELS,
                Permission.MODERATE_ROLES,
                Permission.MANAGE_GUILD_CONFIG,
                Permission.MANAGE_PERMISSIONS,
                Permission.MANAGE_AFK,
                Permission.MANAGE_SNIPPETS,
                Permission.MANAGE_LEVELS,
                Permission.MANAGE_STARBOARD,
                Permission.VIEW_USER_INFO,
                Permission.VIEW_AUDIT_LOGS,
                Permission.VIEW_SYSTEM_INFO,
                Permission.MANAGE_AUDIT_LOGS,
            },
            PermissionLevel.SERVER_OWNER: {
                # All guild-scoped permissions
                Permission.MODERATE_MESSAGES,
                Permission.MODERATE_MEMBERS,
                Permission.MODERATE_CHANNELS,
                Permission.MODERATE_ROLES,
                Permission.MANAGE_GUILD_CONFIG,
                Permission.MANAGE_PERMISSIONS,
                Permission.MANAGE_AFK,
                Permission.MANAGE_SNIPPETS,
                Permission.MANAGE_LEVELS,
                Permission.MANAGE_STARBOARD,
                Permission.VIEW_USER_INFO,
                Permission.VIEW_AUDIT_LOGS,
                Permission.VIEW_SYSTEM_INFO,
                Permission.MANAGE_AUDIT_LOGS,
            },
            PermissionLevel.SYS_ADMIN: {
                # All permissions except bot owner exclusive
                Permission.MODERATE_MESSAGES,
                Permission.MODERATE_MEMBERS,
                Permission.MODERATE_CHANNELS,
                Permission.MODERATE_ROLES,
                Permission.MANAGE_GUILD_CONFIG,
                Permission.MANAGE_PERMISSIONS,
                Permission.MANAGE_AFK,
                Permission.MANAGE_SNIPPETS,
                Permission.MANAGE_LEVELS,
                Permission.MANAGE_STARBOARD,
                Permission.VIEW_USER_INFO,
                Permission.VIEW_AUDIT_LOGS,
                Permission.VIEW_SYSTEM_INFO,
                Permission.MANAGE_AUDIT_LOGS,
                Permission.USE_EVAL,
                Permission.USE_SYSTEM_COMMANDS,
            },
            PermissionLevel.BOT_OWNER: {
                # All permissions
                *Permission.__members__.values()
            }
        }
    
    async def check_permission(
        self, 
        user_id: int, 
        permission: Permission, 
        context: PermissionContext
    ) -> bool:
        """Check if a user has a specific permission in the given context."""
        
        # Check cache first
        cache_key = f"{user_id}:{permission.value}:{hash(str(context))}"
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            # Check explicit permission grants
            grants = await self._get_user_permission_grants(user_id, permission)
            for grant in grants:
                if not grant.is_expired() and grant.is_valid_for_context(context):
                    await self.cache.set(cache_key, True, ttl=300)  # Cache for 5 minutes
                    await self.audit_logger.log_permission_check(
                        user_id, permission, context, True, "explicit_grant"
                    )
                    return True
            
            # Check traditional permission level
            user_level = await self._get_user_permission_level(user_id, context.guild_id)
            if user_level is not None:
                level_permissions = self._permission_mappings.get(user_level, set())
                has_permission = permission in level_permissions
                
                await self.cache.set(cache_key, has_permission, ttl=300)
                await self.audit_logger.log_permission_check(
                    user_id, permission, context, has_permission, f"level_{user_level.value}"
                )
                return has_permission
            
            # Default deny
            await self.cache.set(cache_key, False, ttl=300)
            await self.audit_logger.log_permission_check(
                user_id, permission, context, False, "default_deny"
            )
            return False
            
        except Exception as e:
            logger.error(f"Error checking permission {permission} for user {user_id}: {e}")
            await self.audit_logger.log_permission_error(user_id, permission, context, str(e))
            return False
    
    async def grant_permission(
        self,
        user_id: int,
        permission: Permission,
        scope: PermissionScope,
        scope_id: Optional[int] = None,
        granted_by: Optional[int] = None,
        duration: Optional[timedelta] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> PermissionGrant:
        """Grant a specific permission to a user."""
        
        expires_at = None
        if duration:
            expires_at = datetime.utcnow() + duration
        
        grant = PermissionGrant(
            user_id=user_id,
            permission=permission,
            scope=scope,
            scope_id=scope_id,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            conditions=conditions
        )
        
        # Store in database
        await self._store_permission_grant(grant)
        
        # Invalidate cache
        await self.cache.invalidate_user(user_id)
        
        # Log the grant
        await self.audit_logger.log_permission_grant(grant, granted_by)
        
        return grant
    
    async def revoke_permission(
        self,
        user_id: int,
        permission: Permission,
        scope: PermissionScope,
        scope_id: Optional[int] = None,
        revoked_by: Optional[int] = None
    ) -> bool:
        """Revoke a specific permission from a user."""
        
        success = await self._remove_permission_grant(user_id, permission, scope, scope_id)
        
        if success:
            # Invalidate cache
            await self.cache.invalidate_user(user_id)
            
            # Log the revocation
            await self.audit_logger.log_permission_revocation(
                user_id, permission, scope, scope_id, revoked_by
            )
        
        return success
    
    async def get_user_permissions(
        self, 
        user_id: int, 
        context: PermissionContext
    ) -> Set[Permission]:
        """Get all permissions a user has in the given context."""
        
        permissions = set()
        
        # Get explicit grants
        all_grants = await self._get_all_user_permission_grants(user_id)
        for grant in all_grants:
            if not grant.is_expired() and grant.is_valid_for_context(context):
                permissions.add(grant.permission)
        
        # Get level-based permissions
        user_level = await self._get_user_permission_level(user_id, context.guild_id)
        if user_level:
            level_permissions = self._permission_mappings.get(user_level, set())
            permissions.update(level_permissions)
        
        return permissions
    
    async def cleanup_expired_permissions(self) -> int:
        """Clean up expired permission grants."""
        count = await self._remove_expired_grants()
        if count > 0:
            logger.info(f"Cleaned up {count} expired permission grants")
            await self.audit_logger.log_cleanup(count)
        return count
    
    # Private helper methods
    async def _get_user_permission_grants(
        self, 
        user_id: int, 
        permission: Permission
    ) -> List[PermissionGrant]:
        """Get specific permission grants for a user."""
        # Implementation would query the database
        pass
    
    async def _get_all_user_permission_grants(self, user_id: int) -> List[PermissionGrant]:
        """Get all permission grants for a user."""
        # Implementation would query the database
        pass
    
    async def _get_user_permission_level(
        self, 
        user_id: int, 
        guild_id: Optional[int]
    ) -> Optional[PermissionLevel]:
        """Get the traditional permission level for a user."""
        # Implementation would use existing permission level logic
        pass
    
    async def _store_permission_grant(self, grant: PermissionGrant) -> None:
        """Store a permission grant in the database."""
        # Implementation would insert into database
        pass
    
    async def _remove_permission_grant(
        self,
        user_id: int,
        permission: Permission,
        scope: PermissionScope,
        scope_id: Optional[int]
    ) -> bool:
        """Remove a permission grant from the database."""
        # Implementation would delete from database
        pass
    
    async def _remove_expired_grants(self) -> int:
        """Remove expired permission grants from the database."""
        # Implementation would delete expired grants
        pass
```

### Enhanced Decorators

```python
# tux/security/permissions/decorators.py
from functools import wraps
from typing import Optional, Dict, Any, Callable, Union
import discord
from discord.ext import commands

from .engine import PermissionEngine
from .models import Permission, PermissionContext, PermissionLevel
from .exceptions import PermissionDeniedError, InvalidPermissionError

def requires_permission(
    permission: Permission,
    *,
    context_from: Optional[str] = None,
    target_user_from: Optional[str] = None,
    target_role_from: Optional[str] = None,
    additional_checks: Optional[Callable] = None
):
    """Decorator to require a specific permission for command execution."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context and user information
            ctx_or_interaction = args[0] if args else None
            
            if isinstance(ctx_or_interaction, commands.Context):
                user = ctx_or_interaction.author
                guild = ctx_or_interaction.guild
                channel = ctx_or_interaction.channel
            elif isinstance(ctx_or_interaction, discord.Interaction):
                user = ctx_or_interaction.user
                guild = ctx_or_interaction.guild
                channel = ctx_or_interaction.channel
            else:
                raise InvalidPermissionError("Invalid context type for permission check")
            
            # Build permission context
            context = PermissionContext(
                guild_id=guild.id if guild else None,
                channel_id=channel.id if channel else None,
                category_id=channel.category.id if hasattr(channel, 'category') and channel.category else None
            )
            
            # Add target information if specified
            if target_user_from and target_user_from in kwargs:
                target_user = kwargs[target_user_from]
                if hasattr(target_user, 'id'):
                    context.target_user_id = target_user.id
            
            if target_role_from and target_role_from in kwargs:
                target_role = kwargs[target_role_from]
                if hasattr(target_role, 'id'):
                    context.target_role_id = target_role.id
            
            # Check permission
            engine = PermissionEngine()
            has_permission = await engine.check_permission(user.id, permission, context)
            
            if not has_permission:
                error_msg = f"You don't have permission to use this command. Required: {permission.value}"
                if isinstance(ctx_or_interaction, commands.Context):
                    await ctx_or_interaction.send(f"❌ {error_msg}")
                    return
                else:
                    raise PermissionDeniedError(error_msg)
            
            # Run additional checks if provided
            if additional_checks:
                additional_result = await additional_checks(ctx_or_interaction, context, *args, **kwargs)
                if not additional_result:
                    error_msg = "Additional permission checks failed"
                    if isinstance(ctx_or_interaction, commands.Context):
                        await ctx_or_interaction.send(f"❌ {error_msg}")
                        return
                    else:
                        raise PermissionDeniedError(error_msg)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def requires_level(
    level: Union[int, PermissionLevel],
    *,
    or_higher: bool = True,
    context_checks: Optional[Callable] = None
):
    """Decorator to require a traditional permission level (backward compatibility)."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would integrate with the existing permission level system
            # while also logging through the new audit system
            
            # Implementation would call existing has_permission logic
            # but also log through the new PermissionAuditLogger
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Convenience decorators for common permission patterns
def requires_moderation(target_user_from: str = "target"):
    """Require moderation permissions with target user context."""
    return requires_permission(
        Permission.MODERATE_MEMBERS,
        target_user_from=target_user_from,
        additional_checks=_check_moderation_hierarchy
    )

def requires_admin():
    """Require administrative permissions."""
    return requires_permission(Permission.MANAGE_GUILD_CONFIG)

def requires_system_access():
    """Require system-level access."""
    return requires_permission(Permission.USE_SYSTEM_COMMANDS)

async def _check_moderation_hierarchy(
    ctx_or_interaction,
    context: PermissionContext,
    *args,
    **kwargs
) -> bool:
    """Additional check to ensure moderation hierarchy is respected."""
    if context.target_user_id:
        # Check that the user can moderate the target
        # Implementation would verify role hierarchy
        pass
    return True
```

### Audit System

```python
# tux/security/permissions/audit.py
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from tux.database.controllers import DatabaseController
from .models import Permission, PermissionContext, PermissionGrant

class AuditEventType(Enum):
    PERMISSION_CHECK = "permission_check"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOCATION = "permission_revocation"
    PERMISSION_ERROR = "permission_error"
    CLEANUP = "cleanup"

@dataclass
class AuditEvent:
    event_type: AuditEventType
    user_id: int
    permission: Optional[Permission] = None
    context: Optional[PermissionContext] = None
    result: Optional[bool] = None
    reason: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class PermissionAuditLogger:
    """Handles logging of permission-related events for security auditing."""
    
    def __init__(self):
        self.db = DatabaseController()
    
    async def log_permission_check(
        self,
        user_id: int,
        permission: Permission,
        context: PermissionContext,
        result: bool,
        reason: str
    ) -> None:
        """Log a permission check event."""
        
        event = AuditEvent(
            event_type=AuditEventType.PERMISSION_CHECK,
            user_id=user_id,
            permission=permission,
            context=context,
            result=result,
            reason=reason
        )
        
        await self._store_audit_event(event)
    
    async def log_permission_grant(
        self,
        grant: PermissionGrant,
        granted_by: Optional[int]
    ) -> None:
        """Log a permission grant event."""
        
        event = AuditEvent(
            event_type=AuditEventType.PERMISSION_GRANT,
            user_id=grant.user_id,
            permission=grant.permission,
            additional_data={
                "scope": grant.scope.value,
                "scope_id": grant.scope_id,
                "granted_by": granted_by,
                "expires_at": grant.expires_at.isoformat() if grant.expires_at else None
            }
        )
        
        await self._store_audit_event(event)
    
    async def log_permission_revocation(
        self,
        user_id: int,
        permission: Permission,
        scope,
        scope_id: Optional[int],
        revoked_by: Optional[int]
    ) -> None:
        """Log a permission revocation event."""
        
        event = AuditEvent(
            event_type=AuditEventType.PERMISSION_REVOCATION,
            user_id=user_id,
            permission=permission,
            additional_data={
                "scope": scope.value,
                "scope_id": scope_id,
                "revoked_by": revoked_by
            }
        )
        
        await self._store_audit_event(event)
    
    async def log_permission_error(
        self,
        user_id: int,
        permission: Permission,
        context: PermissionContext,
        error: str
    ) -> None:
        """Log a permission system error."""
        
        event = AuditEvent(
            event_type=AuditEventType.PERMISSION_ERROR,
            user_id=user_id,
            permission=permission,
            context=context,
            additional_data={"error": error}
        )
        
        await self._store_audit_event(event)
    
    async def log_cleanup(self, count: int) -> None:
        """Log a permission cleanup event."""
        
        event = AuditEvent(
            event_type=AuditEventType.CLEANUP,
            user_id=0,  # System event
            additional_data={"expired_grants_removed": count}
        )
        
        await self._store_audit_event(event)
    
    async def get_audit_events(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> list[AuditEvent]:
        """Retrieve audit events based on filters."""
        # Implementation would query the database with filters
        pass
    
    async def _store_audit_event(self, event: AuditEvent) -> None:
        """Store an audit event in the database."""
        # Implementation would insert into audit log table
        pass
```

## Database Schema Extensions

### New Tables

```sql
-- Permission grants table
CREATE TABLE permission_grants (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    permission VARCHAR(100) NOT NULL,
    scope VARCHAR(20) NOT NULL,
    scope_id BIGINT,
    granted_by BIGINT,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    conditions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permission audit log table
CREATE TABLE permission_audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    permission VARCHAR(100),
    context JSONB,
    result BOOLEAN,
    reason VARCHAR(200),
    additional_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_permission_grants_user_id ON permission_grants(user_id);
CREATE INDEX idx_permission_grants_permission ON permission_grants(permission);
CREATE INDEX idx_permission_grants_scope ON permission_grants(scope, scope_id);
CREATE INDEX idx_permission_grants_expires_at ON permission_grants(expires_at);

CREATE INDEX idx_permission_audit_log_user_id ON permission_audit_log(user_id);
CREATE INDEX idx_permission_audit_log_event_type ON permission_audit_log(event_type);
CREATE INDEX idx_permission_audit_log_timestamp ON permission_audit_log(timestamp);
```

## Migration Strategy

### Phase 1: Foundation (Weeks 1-2)

1. **Create new permission models** and database schema
2. **Implement core PermissionEngine** with basic functionality
3. **Add audit logging system** with database storage
4. **Create comprehensive unit tests** for new components

### Phase 2: Integration (Weeks 3-4)

1. **Implement new decorators** with backward compatibility
2. **Create permission management commands** for administrators
3. **Add caching layer** for performance optimization
4. **Integrate with existing permission level system**

### Phase 3: Migration (Weeks 5-6)

1. **Migrate high-priority commands** to new system
2. **Add granular permissions** to critical operations
3. **Implement temporary permission features**
4. **Create administrative tools** for permission management

### Phase 4: Enhancement (Weeks 7-8)

1. **Add advanced context-aware checks**
2. **Implement permission delegation features**
3. **Create comprehensive audit reporting**
4. **Add automated permission cleanup**

## Usage Examples

### Basic Permission Check

```python
from tux.security.permissions import requires_permission, Permission

class ModerationCog(commands.Cog):
    @commands.command()
    @requires_permission(Permission.MODERATE_MESSAGES)
    async def purge(self, ctx: commands.Context, amount: int):
        """Purge messages with granular permission check."""
        # Implementation here
        pass
```

### Context-Aware Permission

```python
@commands.command()
@requires_permission(
    Permission.MODERATE_MEMBERS,
    target_user_from="target"
)
async def timeout(self, ctx: commands.Context, target: discord.Member, duration: str):
    """Timeout a member with hierarchy checks."""
    # Implementation here
    pass
```

### Temporary Permission Grant

```python
@commands.command()
@requires_permission(Permission.MANAGE_PERMISSIONS)
async def temp_mod(self, ctx: commands.Context, user: discord.Member, duration: str):
    """Grant temporary moderation permissions."""
    engine = PermissionEngine()
    
    duration_delta = parse_duration(duration)  # Helper function
    
    await engine.grant_permission(
        user_id=user.id,
        permission=Permission.MODERATE_MESSAGES,
        scope=PermissionScope.GUILD,
        scope_id=ctx.guild.id,
        granted_by=ctx.author.id,
        duration=duration_delta
    )
    
    await ctx.send(f"✅ Granted temporary moderation permissions to {user.mention} for {duration}")
```

## Benefits

### Security Improvements

1. **Granular Control**: Specific permissions instead of broad levels
2. **Context Awareness**: Permissions can be scoped to specific channels/guilds
3. **Comprehensive Auditing**: Full audit trail of all permission operations
4. **Temporary Access**: Time-limited permission grants
5. **Hierarchy Enforcement**: Automatic checks for role hierarchy

### Operational Benefits

1. **Flexible Administration**: Fine-grained permission management
2. **Better Compliance**: Comprehensive audit logs for security reviews
3. **Reduced Risk**: Principle of least privilege enforcement
4. **Easier Troubleshooting**: Detailed logs for permission issues

### Developer Experience

1. **Backward Compatibility**: Existing code continues to work
2. **Clear Intent**: Permission names clearly indicate what they allow
3. **Easy Integration**: Simple decorators for common patterns
4. **Comprehensive Testing**: Full test coverage for permission logic

This enhanced permission system provides a robust foundation for fine-grained access control while maintaining the simplicity and effectiveness of the current system.
