# Database Patterns & Standards

## Overview

This document establishes database interaction standards for the Tux Discord bot. Our architecture
uses **SQLModel** with **SQLAlchemy** for type-safe database operations, following clean
architecture principles with proper separation of concerns.

## Architecture Overview

### Core Components

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Commands/     │    │   Controllers    │    │  Database       │
│   Services      │───▶│   (Business      │───▶│  Service        │
│                 │    │    Logic)        │    │  (Session Mgmt) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │     Models       │    │   PostgreSQL    │
                       │   (SQLModel)     │    │   Database      │
                       └──────────────────┘    └─────────────────┘
```

### Layer Responsibilities

- **Commands/Services**: User interaction, validation, orchestration
- **Controllers**: Business logic, data transformation, error handling
- **Database Service**: Session management, connection handling
- **Models**: Data structure, relationships, validation

## Database Service Usage

### Dependency Injection Pattern

```python
# ✅ GOOD: Proper dependency injection
class MyCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.guild_controller = self.db.guild_config  # Injected via BaseCog

# ❌ BAD: Direct instantiation
class MyCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.guild_controller = GuildConfigController()  # Missing DB service
```

### Service Access Patterns

```python
# ✅ GOOD: Use injected controllers
async def my_command(self, ctx: commands.Context[Tux]) -> None:
    config = await self.db.guild_config.get_config_by_guild_id(ctx.guild.id)

# ✅ GOOD: Direct service access when needed
async def advanced_operation(self) -> None:
    async with self.db.session() as session:
        # Complex multi-table operations
        result = await session.execute(custom_query)
```

## Controller Patterns

### Standard Controller Structure

```python
from tux.database.controllers.base import BaseController
from tux.database.models import MyModel
from tux.database.service import DatabaseService

class MyController(BaseController[MyModel]):
    """Controller for MyModel with business logic."""
    
    def __init__(self, db: DatabaseService | None = None):
        super().__init__(MyModel, db)
    
    # Business logic methods
    async def get_by_name(self, name: str) -> MyModel | None:
        """Get model by name with business validation."""
        return await self.find_one(filters=MyModel.name == name)
    
    async def create_with_validation(self, **data) -> MyModel:
        """Create model with business rules."""
        # Validation logic
        if not self._validate_data(data):
            raise ValueError("Invalid data")
        
        return await self.create(**data)
```

### CRUD Operations

```python
# ✅ Standard CRUD patterns
class UserController(BaseController[User]):
    
    async def get_user(self, user_id: int) -> User | None:
        """Get user by ID."""
        return await self.get_by_id(user_id)
    
    async def create_user(self, **user_data) -> User:
        """Create new user."""
        return await self.create(**user_data)
    
    async def update_user(self, user_id: int, **updates) -> User | None:
        """Update existing user."""
        return await self.update_by_id(user_id, **updates)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        return await self.delete_by_id(user_id)
    
    async def find_users_by_guild(self, guild_id: int) -> list[User]:
        """Find users in specific guild."""
        return await self.find_all(filters=User.guild_id == guild_id)
```

## Error Handling Patterns

### Controller-Level Error Handling

```python
async def get_or_create_config(self, guild_id: int) -> GuildConfig | None:
    """Get or create guild config with proper error handling."""
    try:
        config = await self.get_by_id(guild_id)
        if config:
            return config
        
        # Create with defaults
        return await self.create(guild_id=guild_id, **DEFAULT_CONFIG)
        
    except IntegrityError as e:
        logger.warning(f"Guild {guild_id} config already exists: {e}")
        # Retry get operation
        return await self.get_by_id(guild_id)
    
    except Exception as e:
        logger.error(f"Failed to get/create config for guild {guild_id}: {e}")
        return None
```

### Transaction Error Handling

```python
async def complex_operation(self, data: dict) -> bool:
    """Complex multi-step operation with transaction."""
    try:
        async with self.db.transaction() as session:
            # Step 1
            user = await self.create_user(session, **data['user'])
            
            # Step 2
            config = await self.create_config(session, user_id=user.id)
            
            # Step 3
            await self.update_stats(session, user_id=user.id)
            
            return True
            
    except Exception as e:
        logger.error(f"Complex operation failed: {e}")
        # Transaction automatically rolled back
        return False
```

## Query Patterns

### Simple Queries

```python
# ✅ GOOD: Use controller methods
users = await self.db.user.find_all(
    filters=User.guild_id == guild_id,
    limit=10,
    order_by=User.created_at.desc()
)

# ✅ GOOD: Single record with fallback
user = await self.db.user.get_by_id(user_id)
if not user:
    user = await self.db.user.create(user_id=user_id, **defaults)
```

### Complex Queries

```python
# ✅ GOOD: Custom queries when needed
async def get_top_users_by_activity(self, guild_id: int, limit: int = 10) -> list[User]:
    """Get most active users with custom query."""
    async with self.db.session() as session:
        query = (
            select(User)
            .where(User.guild_id == guild_id)
            .order_by(User.message_count.desc(), User.last_active.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return result.scalars().all()
```

### Relationship Queries

```python
# ✅ GOOD: Eager loading for relationships
async def get_user_with_cases(self, user_id: int) -> User | None:
    """Get user with all moderation cases."""
    return await self.db.user.find_one(
        filters=User.id == user_id,
        options=[selectinload(User.cases)]
    )

# ✅ GOOD: Relationship filtering
async def get_users_with_active_cases(self, guild_id: int) -> list[User]:
    """Get users with active moderation cases."""
    return await self.db.user.find_all(
        filters=and_(
            User.guild_id == guild_id,
            User.cases.any(Case.is_active == True)
        )
    )
```

## Transaction Management

### Automatic Transactions

```python
# ✅ GOOD: Controller methods use automatic transactions
async def update_user_stats(self, user_id: int, **stats) -> User | None:
    """Update user statistics (automatically transactional)."""
    return await self.db.user.update_by_id(user_id, **stats)
```

### Manual Transactions

```python
# ✅ GOOD: Manual transactions for complex operations
async def transfer_points(self, from_user: int, to_user: int, points: int) -> bool:
    """Transfer points between users."""
    try:
        async with self.db.transaction() as session:
            # Deduct from sender
            sender = await session.get(User, from_user)
            if sender.points < points:
                raise ValueError("Insufficient points")
            
            sender.points -= points
            
            # Add to receiver
            receiver = await session.get(User, to_user)
            receiver.points += points
            
            # Log transaction
            await session.merge(PointsTransaction(
                from_user=from_user,
                to_user=to_user,
                amount=points
            ))
            
            return True
            
    except Exception as e:
        logger.error(f"Points transfer failed: {e}")
        return False
```

## Performance Patterns

### Efficient Queries

```python
# ✅ GOOD: Use pagination for large datasets
async def get_all_users_paginated(self, guild_id: int, page: int = 1) -> PaginationResult[User]:
    """Get users with pagination."""
    return await self.db.user.paginate(
        filters=User.guild_id == guild_id,
        page=page,
        per_page=50
    )

# ✅ GOOD: Bulk operations
async def update_multiple_users(self, updates: list[dict]) -> int:
    """Bulk update users."""
    return await self.db.user.bulk_update(updates)
```

### Caching Patterns

```python
from functools import lru_cache
from typing import Optional

class GuildConfigController(BaseController[GuildConfig]):
    
    @lru_cache(maxsize=128)
    async def get_cached_config(self, guild_id: int) -> GuildConfig | None:
        """Get guild config with caching."""
        return await self.get_by_id(guild_id)
    
    async def update_config(self, guild_id: int, **updates) -> GuildConfig | None:
        """Update config and invalidate cache."""
        result = await self.update_by_id(guild_id, **updates)
        # Clear cache for this guild
        self.get_cached_config.cache_clear()
        return result
```

## Model Patterns

### Model Definition

```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional

class User(SQLModel, table=True):
    """User model with proper typing and validation."""
    
    __tablename__ = "users"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Required fields
    discord_id: int = Field(unique=True, index=True)
    guild_id: int = Field(index=True)
    username: str = Field(max_length=100)
    
    # Optional fields with defaults
    points: int = Field(default=0, ge=0)  # Validation: >= 0
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    cases: list["Case"] = Relationship(back_populates="user")
    
    # Validation
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        return v.strip()
```

### Relationship Patterns

```python
# ✅ GOOD: Proper relationship definition
class Guild(SQLModel, table=True):
    id: int = Field(primary_key=True)
    discord_id: int = Field(unique=True)
    
    # One-to-many
    users: list[User] = Relationship(back_populates="guild")
    cases: list[Case] = Relationship(back_populates="guild")

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    guild_id: int = Field(foreign_key="guilds.id")
    
    # Many-to-one
    guild: Guild = Relationship(back_populates="users")
    cases: list[Case] = Relationship(back_populates="user")
```

## Migration Patterns

### Migration Structure

```python
"""Add user points system

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add points column to users table."""
    op.add_column('users', sa.Column('points', sa.Integer(), nullable=False, server_default='0'))
    op.create_index('ix_users_points', 'users', ['points'])

def downgrade() -> None:
    """Remove points column from users table."""
    op.drop_index('ix_users_points', 'users')
    op.drop_column('users', 'points')
```

### Data Migration

```python
def upgrade() -> None:
    """Migrate old data format to new format."""
    # Schema changes first
    op.add_column('users', sa.Column('new_field', sa.String(100)))
    
    # Data migration
    connection = op.get_bind()
    connection.execute(
        text("UPDATE users SET new_field = CONCAT('prefix_', old_field)")
    )
    
    # Cleanup
    op.drop_column('users', 'old_field')
```

## Testing Patterns

### Controller Testing

```python
import pytest
from tux.database.service import DatabaseService
from tux.database.controllers import UserController

@pytest.fixture
async def user_controller(db_service: DatabaseService):
    """Create user controller for testing."""
    return UserController(db_service)

async def test_create_user(user_controller: UserController):
    """Test user creation."""
    user_data = {
        "discord_id": 123456789,
        "guild_id": 987654321,
        "username": "testuser"
    }
    
    user = await user_controller.create_user(**user_data)
    
    assert user.discord_id == 123456789
    assert user.username == "testuser"
    assert user.points == 0  # Default value

async def test_get_nonexistent_user(user_controller: UserController):
    """Test getting non-existent user."""
    user = await user_controller.get_user(999999)
    assert user is None
```

### Integration Testing

```python
async def test_user_points_transfer(db_service: DatabaseService):
    """Test points transfer between users."""
    user_controller = UserController(db_service)
    
    # Setup
    sender = await user_controller.create_user(
        discord_id=111, guild_id=1, username="sender", points=100
    )
    receiver = await user_controller.create_user(
        discord_id=222, guild_id=1, username="receiver", points=0
    )
    
    # Transfer
    success = await user_controller.transfer_points(sender.id, receiver.id, 50)
    
    # Verify
    assert success is True
    
    updated_sender = await user_controller.get_user(sender.id)
    updated_receiver = await user_controller.get_user(receiver.id)
    
    assert updated_sender.points == 50
    assert updated_receiver.points == 50
```

## Anti-Patterns to Avoid

### ❌ Direct Session Usage in Commands

```python
# BAD: Direct session management in commands
@commands.command()
async def bad_command(self, ctx):
    async with self.bot.db.session() as session:
        user = await session.get(User, ctx.author.id)
        # Complex logic here...
```

### ❌ Missing Error Handling

```python
# BAD: No error handling
async def create_user(self, **data):
    return await self.db.user.create(**data)  # Can fail silently

# GOOD: Proper error handling
async def create_user(self, **data):
    try:
        return await self.db.user.create(**data)
    except IntegrityError:
        logger.warning(f"User already exists: {data.get('discord_id')}")
        return None
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise
```

### ❌ N+1 Query Problems

```python
# BAD: N+1 queries
users = await self.db.user.find_all()
for user in users:
    cases = await self.db.case.find_all(filters=Case.user_id == user.id)

# GOOD: Eager loading
users = await self.db.user.find_all(
    options=[selectinload(User.cases)]
)
```

## Performance Guidelines

### Query Optimization

1. **Use indexes** for frequently queried fields
2. **Limit result sets** with pagination
3. **Eager load** relationships when needed
4. **Use bulk operations** for multiple records
5. **Cache frequently accessed** data

### Connection Management

1. **Use connection pooling** (handled by DatabaseService)
2. **Close sessions properly** (automatic with context managers)
3. **Avoid long-running transactions**
4. **Monitor connection usage**

## Security Considerations

### Input Validation

```python
# ✅ GOOD: Validate inputs
async def update_user_points(self, user_id: int, points: int) -> User | None:
    if points < 0:
        raise ValueError("Points cannot be negative")
    
    if points > MAX_POINTS:
        raise ValueError(f"Points cannot exceed {MAX_POINTS}")
    
    return await self.update_by_id(user_id, points=points)
```

### SQL Injection Prevention

```python
# ✅ GOOD: Use parameterized queries (SQLAlchemy handles this)
users = await self.find_all(filters=User.username == username)

# ❌ BAD: Never use string formatting for queries
# query = f"SELECT * FROM users WHERE username = '{username}'"  # NEVER DO THIS
```

---

## Quick Reference

### Common Operations

```python
# Get single record
user = await self.db.user.get_by_id(user_id)

# Create record
user = await self.db.user.create(discord_id=123, username="test")

# Update record
user = await self.db.user.update_by_id(user_id, points=100)

# Delete record
success = await self.db.user.delete_by_id(user_id)

# Find with filters
users = await self.db.user.find_all(
    filters=User.guild_id == guild_id,
    limit=10
)

# Pagination
result = await self.db.user.paginate(page=1, per_page=20)

# Transaction
async with self.db.transaction() as session:
    # Multiple operations
    pass
```

### Error Handling Checklist

- [ ] Handle `IntegrityError` for unique constraints
- [ ] Handle `NoResultFound` for required records
- [ ] Log errors with appropriate context
- [ ] Provide meaningful error messages
- [ ] Use transactions for multi-step operations
- [ ] Validate inputs before database operations

---

*This guide should be followed for all database interactions in the Tux codebase. Regular reviews
should ensure these patterns are consistently applied.*
