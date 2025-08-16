# Discord Bot Database Schema Design v2

## Overview

This document outlines the architecture for a modern Discord bot database schema using SQLModel as the ORM, Alembic for migrations, and Redis for caching. The design prioritizes maintainability, scalability, performance, and follows current best practices from the entire technology stack.

## Technology Stack

- **ORM**: SQLModel 0.0.24+ (SQLAlchemy 2.0.14+ with Pydantic 2.x integration)
- **Database**: PostgreSQL (primary), SQLite (development)
- **Migrations**: Alembic 1.16.5+ with PEP 621 support
- **Enum Management**: alembic-postgresql-enum 1.8.0+ for PostgreSQL enum handling
- **Async Driver**: AsyncPG 0.30.0+ for PostgreSQL connections
- **Caching**: Redis for frequently accessed data and rate limiting
- **Web API**: FastAPI integration for web dashboard
- **Validation**: Pydantic v2 with comprehensive field validation
- **Python**: 3.9+ (required by all components)

## Architecture

### Application Layers

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discord.py    │    │   Controllers   │    │    Services     │    │     Models      │
│   (Commands)    │───▶│   (Business     │───▶│   (Cache/DB)    │───▶│   (Database)    │
│                 │    │    Logic)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │      Redis      │
                                               │     (Cache)     │
                                               └─────────────────┘
```

### Project Structure

```
database/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── base.py          # Base model classes and mixins
│   ├── database.py      # Database connection management
│   └── exceptions.py    # Custom exceptions
├── models/
│   ├── __init__.py
│   ├── guild.py         # Guild and configuration models
│   ├── moderation.py    # Cases, notes, custom case types
│   ├── content.py       # Snippets, reminders
│   ├── social.py        # Levels, AFK, starboard
│   ├── permissions.py   # Access control and permissions
│   ├── web.py           # Web UI authentication
│   └── dynamic.py       # Dynamic configurations
├── controllers/
│   ├── __init__.py
│   ├── base.py          # Base controller
│   ├── moderation.py    # Moderation business logic
│   ├── guild_config.py  # Guild management
│   └── user_management.py
├── services/
│   ├── __init__.py
│   ├── database.py      # Database service layer
│   ├── cache.py         # Redis caching service
│   └── validation.py    # Business validation
├── migrations/
│   ├── env.py           # Alembic environment
│   ├── script.py.mako   # Migration template
│   └── versions/        # Migration files
└── schemas/
    ├── __init__.py
    └── api.py           # API response schemas
```

## Core Components

### Base Model System

```python
# database/core/base.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, DateTime, func, Boolean
from sqlalchemy.orm import declared_attr

class TimestampMixin(SQLModel):
    """Automatic created_at and updated_at timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

class SoftDeleteMixin(SQLModel):
    """Soft delete functionality"""
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[int] = Field(default=None, sa_column=BigInteger())
    
    def soft_delete(self, deleted_by_user_id: Optional[int] = None):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id

class AuditMixin(SQLModel):
    """Track who created/modified records"""
    created_by: Optional[int] = Field(default=None, sa_column=BigInteger())
    updated_by: Optional[int] = Field(default=None, sa_column=BigInteger())

class CRUDMixin(SQLModel):
    """Basic CRUD operations"""
    @classmethod
    async def create(cls, session, **kwargs):
        instance = cls(**kwargs)
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        return instance
    
    @classmethod
    async def get_by_id(cls, session, record_id):
        return await session.get(cls, record_id)

class DiscordIDMixin(SQLModel):
    """Discord snowflake ID validation and utilities"""
    def validate_snowflake(self, snowflake_id: int, field_name: str = "id") -> int:
        if not isinstance(snowflake_id, int) or snowflake_id <= 0:
            raise ValueError(f"{field_name} must be a positive integer")
        if snowflake_id < 4194304:  # Minimum Discord snowflake
            raise ValueError(f"{field_name} is not a valid Discord snowflake")
        return snowflake_id

class BaseModel(
    SQLModel,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    CRUDMixin,
    DiscordIDMixin
):
    """Full-featured base model for all entities"""
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
```

### Database Connection Management

```python
# database/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, Session, create_engine
from contextlib import asynccontextmanager

class DatabaseManager:
    def __init__(self, database_url: str, echo: bool = False):
        if database_url.startswith(('postgresql+asyncpg', 'sqlite+aiosqlite')):
            # Async engine
            self.engine = create_async_engine(database_url, echo=echo)
            self.async_session_factory = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            self.is_async = True
        else:
            # Sync engine (SQLModel's standard pattern)
            self.engine = create_engine(database_url, echo=echo)
            self.is_async = False
    
    @asynccontextmanager
    async def get_session(self):
        if self.is_async:
            async with self.async_session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        else:
            with Session(self.engine) as session:
                try:
                    yield session
                    session.commit()
                except Exception:
                    session.rollback()
                    raise
    
    def create_tables(self):
        SQLModel.metadata.create_all(self.engine)
```

## Data Models

### Core Discord Entities

```python
# database/models/guild.py
from typing import List, Optional
from sqlmodel import Field, Relationship
from sqlalchemy import BigInteger, Index
from database.core.base import BaseModel

class Guild(BaseModel, table=True):
    """Main guild table"""
    guild_id: int = Field(primary_key=True, sa_column=BigInteger())
    guild_joined_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    case_count: int = Field(default=0)
    
    # Relationships
    guild_config: Optional["GuildConfig"] = Relationship(back_populates="guild")
    cases: List["Case"] = Relationship(back_populates="guild")
    snippets: List["Snippet"] = Relationship(back_populates="guild")
    notes: List["Note"] = Relationship(back_populates="guild")
    
    __table_args__ = (Index("idx_guild_id", "guild_id"),)

class GuildConfig(BaseModel, table=True):
    """Guild configuration settings"""
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", sa_column=BigInteger())
    prefix: Optional[str] = Field(default=None, max_length=10)
    
    # Channel configurations
    mod_log_id: Optional[int] = Field(default=None, sa_column=BigInteger())
    audit_log_id: Optional[int] = Field(default=None, sa_column=BigInteger())
    
    # Permission level roles (0-7)
    perm_level_0_role_id: Optional[int] = Field(default=None, sa_column=BigInteger())
    perm_level_1_role_id: Optional[int] = Field(default=None, sa_column=BigInteger())
    # ... additional permission levels
    
    # Relationship
    guild: Guild = Relationship(back_populates="guild_config")
```

### Moderation System

```python
# database/models/moderation.py
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship
from sqlalchemy import BigInteger, Index, ARRAY, JSON
from database.core.base import BaseModel

class CaseType(str, Enum):
    """Standard moderation case types"""
    BAN = "BAN"
    UNBAN = "UNBAN"
    HACKBAN = "HACKBAN"
    TEMPBAN = "TEMPBAN"
    KICK = "KICK"
    TIMEOUT = "TIMEOUT"
    UNTIMEOUT = "UNTIMEOUT"
    WARN = "WARN"
    JAIL = "JAIL"
    UNJAIL = "UNJAIL"

class Case(BaseModel, table=True):
    """Moderation cases with support for custom types"""
    case_id: int = Field(primary_key=True, sa_column=BigInteger())
    case_status: Optional[bool] = Field(default=True)
    
    # Support both built-in and custom case types
    case_type: Optional[CaseType] = Field(default=None)
    custom_case_type_id: Optional[int] = Field(default=None, foreign_key="customcasetype.id")
    
    case_reason: str = Field(max_length=2000)
    case_moderator_id: int = Field(sa_column=BigInteger())
    case_user_id: int = Field(sa_column=BigInteger())
    case_user_roles: List[int] = Field(default_factory=list, sa_column=ARRAY(BigInteger()))
    case_number: Optional[int] = Field(default=None)
    case_expires_at: Optional[datetime] = Field(default=None)
    case_metadata: Optional[dict] = Field(default=None, sa_column=JSON())
    
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column=BigInteger())
    
    # Relationships
    guild: Guild = Relationship(back_populates="cases")
    custom_case_type: Optional["CustomCaseType"] = Relationship()
    
    __table_args__ = (
        Index("idx_case_guild_user", "guild_id", "case_user_id"),
        Index("idx_case_guild_moderator", "guild_id", "case_moderator_id"),
        Index("idx_case_created_desc", "case_created_at"),
    )

class CustomCaseType(BaseModel, table=True):
    """Custom case types for guilds"""
    id: int = Field(primary_key=True, sa_column=BigInteger())
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column=BigInteger())
    type_name: str = Field(max_length=50)
    display_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    severity_level: int = Field(default=1)  # 1-10 scale
    requires_duration: bool = Field(default=False)
    
    guild: Guild = Relationship()

class Note(BaseModel, table=True):
    """User notes with proper numbering"""
    note_id: int = Field(primary_key=True, sa_column=BigInteger())
    note_content: str = Field(max_length=2000)
    note_moderator_id: int = Field(sa_column=BigInteger())
    note_user_id: int = Field(sa_column=BigInteger())
    note_number: Optional[int] = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column=BigInteger())
    
    guild: Guild = Relationship(back_populates="notes")
```

### Content Management

```python
# database/models/content.py
from typing import Optional
from sqlmodel import Field, Relationship
from sqlalchemy import BigInteger, Index
from database.core.base import BaseModel

class Snippet(BaseModel, table=True):
    """Code snippets with usage tracking"""
    snippet_id: int = Field(primary_key=True, sa_column=BigInteger())
    snippet_name: str = Field(max_length=100)
    snippet_content: Optional[str] = Field(default=None, max_length=4000)
    snippet_user_id: int = Field(sa_column=BigInteger())
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column=BigInteger())
    uses: int = Field(default=0)
    locked: bool = Field(default=False)
    alias: Optional[str] = Field(default=None, max_length=100)
    
    guild: Guild = Relationship(back_populates="snippets")
    
    __table_args__ = (
        Index("idx_snippet_name_guild", "snippet_name", "guild_id", unique=True),
    )

class Reminder(BaseModel, table=True):
    """User reminders"""
    reminder_id: int = Field(primary_key=True, sa_column=BigInteger())
    reminder_content: str = Field(max_length=2000)
    reminder_expires_at: datetime = Field()
    reminder_channel_id: int = Field(sa_column=BigInteger())
    reminder_user_id: int = Field(sa_column=BigInteger())
    reminder_sent: bool = Field(default=False)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column=BigInteger())
    
    guild: Guild = Relationship(back_populates="reminders")
```

### Social Features

```python
# database/models/social.py
from typing import Optional
from sqlmodel import Field, Relationship
from sqlalchemy import BigInteger, Index, Float
from database.core.base import BaseModel

class AFK(BaseModel, table=True):
    """AFK status tracking"""
    member_id: int = Field(primary_key=True, sa_column=BigInteger())
    nickname: str = Field(max_length=100)
    reason: str = Field(max_length=500)
    since: datetime = Field(default_factory=datetime.utcnow)
    until: Optional[datetime] = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column=BigInteger())
    enforced: bool = Field(default=False)
    perm_afk: bool = Field(default=False)
    
    guild: Guild = Relationship(back_populates="afk_members")
    
    __table_args__ = (
        Index("idx_afk_member_guild", "member_id", "guild_id", unique=True),
    )

class Levels(BaseModel, table=True):
    """XP and leveling system"""
    member_id: int = Field(primary_key=True, sa_column=BigInteger())
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", sa_column=BigInteger())
    xp: float = Field(default=0.0, sa_column=Float())
    level: int = Field(default=0)
    blacklisted: bool = Field(default=False)
    last_message: datetime = Field(default_factory=datetime.utcnow)
    
    guild: Guild = Relationship(back_populates="levels")
    
    __table_args__ = (
        Index("idx_levels_guild_xp", "guild_id", "xp"),
    )
```

## Advanced Features

### Permission System

```python
# database/models/permissions.py
from enum import Enum
from typing import Optional
from sqlmodel import Field, Relationship
from sqlalchemy import BigInteger, Index
from database.core.base import BaseModel

class PermissionType(str, Enum):
    MEMBER = "member"
    CHANNEL = "channel"
    CATEGORY = "category"
    ROLE = "role"
    COMMAND = "command"
    MODULE = "module"

class AccessType(str, Enum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    IGNORE = "ignore"

class GuildPermission(BaseModel, table=True):
    """Flexible permission system"""
    id: int = Field(primary_key=True, sa_column=BigInteger())
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column=BigInteger())
    permission_type: PermissionType = Field()
    access_type: AccessType = Field()
    target_id: int = Field(sa_column=BigInteger())
    target_name: Optional[str] = Field(default=None, max_length=100)
    command_name: Optional[str] = Field(default=None, max_length=100)
    module_name: Optional[str] = Field(default=None, max_length=100)
    expires_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    
    guild: Guild = Relationship()
    
    __table_args__ = (
        Index("idx_guild_perm_guild_type", "guild_id", "permission_type"),
        Index("idx_guild_perm_target", "target_id", "permission_type"),
    )
```

### Web UI Integration

```python
# database/models/web.py
from typing import List, Optional
from sqlmodel import Field, Relationship
from sqlalchemy import BigInteger, Index
from database.core.base import BaseModel

class WebUser(BaseModel, table=True):
    """Web dashboard authentication"""
    user_id: int = Field(primary_key=True, sa_column=BigInteger())
    discord_username: str = Field(max_length=100)
    discord_avatar: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    last_login: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    
    sessions: List["WebSession"] = Relationship(back_populates="user")
    guild_permissions: List["WebGuildPermission"] = Relationship(back_populates="user")

class WebSession(BaseModel, table=True):
    """Web dashboard sessions"""
    session_id: str = Field(primary_key=True, max_length=128)
    user_id: int = Field(foreign_key="webuser.user_id", sa_column=BigInteger())
    expires_at: datetime = Field()
    ip_address: Optional[str] = Field(default=None, max_length=45)
    is_active: bool = Field(default=True)
    
    user: WebUser = Relationship(back_populates="sessions")
```

## Services Layer

### Redis Caching Service

```python
# services/cache.py
import redis.asyncio as redis
import json
from typing import Optional, List, Any
from datetime import timedelta

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def get_guild_config(self, guild_id: int) -> Optional[dict]:
        """Get cached guild configuration"""
        key = f"guild_config:{guild_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set_guild_config(self, guild_id: int, config: dict, ttl: int = 3600):
        """Cache guild configuration"""
        key = f"guild_config:{guild_id}"
        await self.redis.setex(key, ttl, json.dumps(config))
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded"""
        current = await self.redis.get(f"rate_limit:{key}")
        if current is None:
            await self.redis.setex(f"rate_limit:{key}", window, 1)
            return False
        
        if int(current) >= limit:
            return True
        
        await self.redis.incr(f"rate_limit:{key}")
        return False
    
    async def update_xp_leaderboard(self, guild_id: int, user_id: int, xp: float):
        """Update XP leaderboard"""
        key = f"xp_leaderboard:{guild_id}"
        await self.redis.zadd(key, {str(user_id): xp})
        await self.redis.expire(key, 3600)
```

### Controller Layer

```python
# controllers/moderation.py
from typing import Optional, List
from database.models.moderation import Case, CaseType
from database.models.guild import Guild
from services.cache import CacheService
from services.database import DatabaseService

class ModerationController:
    def __init__(self, db: DatabaseService, cache: CacheService):
        self.db = db
        self.cache = cache
    
    async def create_case(
        self, 
        guild_id: int,
        user_id: int,
        moderator_id: int,
        case_type: CaseType,
        reason: str,
        duration: Optional[int] = None
    ) -> Case:
        """Create a moderation case with business logic"""
        
        async with self.db.get_session() as session:
            # Create case with audit tracking
            case = await Case.create(
                session,
                case_type=case_type,
                case_reason=reason,
                case_user_id=user_id,
                case_moderator_id=moderator_id,
                guild_id=guild_id,
                case_expires_at=self._calculate_expiry(case_type, duration),
                created_by=moderator_id
            )
            
            # Cache invalidation
            await self.cache.delete(f"user_cases:{guild_id}:{user_id}")
            
            return case
    
    async def get_user_cases(self, guild_id: int, user_id: int) -> List[Case]:
        """Get user cases with caching"""
        cache_key = f"user_cases:{guild_id}:{user_id}"
        
        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return [Case.from_dict(case_data) for case_data in cached]
        
        # Database query
        async with self.db.get_session() as session:
            cases = await Case.get_all(
                session, 
                filters={'guild_id': guild_id, 'case_user_id': user_id},
                order_by='case_created_at DESC'
            )
            
            # Cache results
            await self.cache.set(
                cache_key, 
                [case.to_dict() for case in cases], 
                ttl=1800
            )
            
            return cases
```

## Migration Configuration

### Alembic Setup with PostgreSQL Enum Support

```python
# database/migrations/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel
from alembic import context
import alembic_postgresql_enum

# Configure PostgreSQL enum management
alembic_postgresql_enum.set_configuration(
    alembic_postgresql_enum.Config(
        add_type_ignore=True,
        drop_unused_enums=True,
        detect_enum_values_changes=True,
        ignore_enum_values_order=False,
    )
)

config = context.config
target_metadata = SQLModel.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True  # SQLite compatibility
    )
    
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### PEP 621 Configuration

```toml
# pyproject.toml
[tool.alembic]
script_location = "database/migrations"
version_locations = ["database/migrations/versions"]
prepend_sys_path = ["."]
file_template = "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s"

[tool.alembic.post_write_hooks]
hooks = ["black", "ruff"]

[tool.alembic.post_write_hooks.black]
type = "console_scripts"
entrypoint = "black"
options = "-l 79 REVISION_SCRIPT_FILENAME"

[tool.alembic.post_write_hooks.ruff]
type = "module"
module = "ruff"
options = "check --fix REVISION_SCRIPT_FILENAME"
```

## Configuration and Deployment

### Environment Configuration

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/discord_bot"
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Cache TTLs
    GUILD_CONFIG_TTL: int = 3600
    USER_CASES_TTL: int = 1800
    XP_LEADERBOARD_TTL: int = 3600
    WEB_SESSION_TTL: int = 86400
    
    # Rate Limiting
    COMMAND_RATE_LIMIT: int = 10
    COMMAND_RATE_WINDOW: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Production Considerations

1. **Connection Pooling**: Use proper pool sizes for AsyncPG (10-20 connections)
2. **Redis Clustering**: Use Redis Cluster or Sentinel for high availability
3. **Migration Strategy**: Use blue-green deployments for zero-downtime migrations
4. **Monitoring**: Implement comprehensive logging and metrics collection
5. **Security**: Use environment variables for sensitive configuration
6. **Backup Strategy**: Regular automated backups with point-in-time recovery

## Key Benefits

1. **Type Safety**: Full type safety with SQLModel and Pydantic validation
2. **Performance**: Redis caching and optimized database queries
3. **Maintainability**: Clean separation of concerns with controllers and services
4. **Scalability**: Async operations and connection pooling
5. **Flexibility**: Dynamic configurations and custom case types
6. **Developer Experience**: Automatic migrations, code formatting, and comprehensive testing
7. **Modern Stack**: Uses latest versions and best practices from all components

This architecture provides a solid foundation for a production-ready Discord bot with room for growth and feature expansion.
