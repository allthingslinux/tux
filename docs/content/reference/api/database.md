# Database API

Tux uses a sophisticated database layer built on SQLModel (Pydantic + SQLAlchemy) with PostgreSQL.
The architecture provides type-safe database operations with both async and sync support.

## Architecture Overview

```text
Bot → DatabaseCoordinator → Controllers → BaseController → Specialized Services
```text

- **DatabaseService**: Connection management and session handling
- **DatabaseCoordinator**: Central access point for all controllers
- **Controllers**: Model-specific database operations
- **BaseController**: Composed interface with specialized operations

## Quick Start

### Accessing the Database

```python
from tux.core.base_cog import BaseCog

class MyCog(BaseCog):
    async def some_command(self, ctx):
        # Access database through self.db
        case = await self.db.case.create_case(
            case_type="BAN",
            case_user_id=123,
            case_moderator_id=456,
            guild_id=ctx.guild.id,
            case_reason="Spam"
        )
```text

### Available Controllers

Access controllers through `self.db.<controller>`:

- `self.db.case` - Moderation cases
- `self.db.guild` - Guild settings
- `self.db.guild_config` - Guild configuration
- `self.db.afk` - AFK status tracking
- `self.db.levels` - User leveling system
- `self.db.snippet` - Code snippets
- `self.db.starboard` - Starboard messages
- `self.db.reminder` - User reminders

## Core Operations

### CRUD Operations

All controllers inherit these basic operations:

```python
# Create
user_case = await self.db.case.create(
    case_type="WARN",
    case_user_id=user_id,
    case_moderator_id=mod_id,
    guild_id=guild_id,
    case_reason="Warning message"
)

# Read
case = await self.db.case.get_by_id(case_id)
cases = await self.db.case.find_all(filters={"guild_id": guild_id})
case = await self.db.case.find_one(filters={"case_number": 42, "guild_id": guild_id})

# Update
updated_case = await self.db.case.update_by_id(case_id, case_reason="Updated reason")

# Delete
success = await self.db.case.delete_by_id(case_id)

# Count
total_cases = await self.db.case.count(filters={"guild_id": guild_id})
```text

### Advanced Query Operations

```python
# Complex filtering
active_bans = await self.db.case.find_all(
    filters=(Case.case_type == "BAN") & (Case.case_status == True) & (Case.guild_id == guild_id)
)

# Ordering and limiting
recent_cases = await self.db.case.find_all(
    filters={"guild_id": guild_id},
    order_by=Case.case_created_at.desc(),
    limit=10
)

# Get or create pattern
guild, created = await self.db.guild.get_or_create(
    guild_id=guild_id,
    defaults={"guild_name": guild.name}
)
```text

### Bulk Operations

```python
# Bulk updates (when needed)
updated_count = await self.db.case.update_where(
    filters={"guild_id": guild_id, "case_status": True},
    values={"case_status": False}
)

# Bulk delete
deleted_count = await self.db.case.delete_where(
    filters={"guild_id": guild_id, "case_type": "TEMP"}
)
```text

### Upsert Operations

```python
# Update existing or create new
config, created = await self.db.guild_config.get_or_create(
    guild_id=guild_id,
    defaults={"prefix": "!", "log_channel_id": None}
)

# Advanced upsert
permission, created = await self.db.guild_permissions.upsert(
    filters={"guild_id": guild_id, "user_id": user_id},
    defaults={"permission_level": "MEMBER"},
    permission_level="MODERATOR"
)
```text

## Models

### Core Models

#### Case

Moderation case tracking:

```python
case = Case(
    case_id=1,                    # Auto-generated
    case_number=42,               # Guild-specific number
    case_type="BAN",              # BAN, KICK, WARN, etc.
    case_user_id=123456789,       # Target user
    case_moderator_id=987654321,  # Moderating user
    guild_id=111222333,           # Guild ID
    case_reason="Spam",           # Reason
    case_status=True,             # Active/inactive
    case_created_at=datetime.now()
)
```text

#### Guild

Guild information:

```python
guild = Guild(
    guild_id=111222333,
    guild_name="My Server",
    case_count=42  # Auto-incremented
)
```text

#### GuildConfig

Guild-specific configuration:

```python
config = GuildConfig(
    guild_id=111222333,
    prefix="!",
    log_channel_id=444555666,
    jail_channel_id=777888999,
    jail_role_id=123123123
)
```text

### Enums

```python
from tux.database.models import CaseType

# Available case types
CaseType.BAN
CaseType.KICK  
CaseType.WARN
CaseType.TIMEOUT
CaseType.JAIL
CaseType.TEMPBAN
CaseType.POLLBAN
CaseType.SNIPPETBAN
```text

## Controller-Specific Methods

### CaseController

```python
# Create a moderation case with auto-generated case number
case = await self.db.case.create_case(
    case_type="BAN",
    case_user_id=user_id,
    case_moderator_id=mod_id,
    guild_id=guild_id,
    case_reason="Violation of rules"
)

# Get cases for a specific user
user_cases = await self.db.case.get_cases_by_user(user_id, guild_id)

# Get active cases only
active_cases = await self.db.case.get_active_cases_by_user(user_id, guild_id)

# Get case by guild-specific case number
case = await self.db.case.get_case_by_number(42, guild_id)

# Get recent cases with limit
recent = await self.db.case.get_recent_cases(guild_id, limit=10)
```text

### GuildConfigController

```python
# Get guild configuration
config = await self.db.guild_config.get_config_by_guild_id(guild_id)

# Update specific config field
await self.db.guild_config.update_config(
    guild_id, 
    log_channel_id=new_channel_id
)

# Get specific config field with default
prefix = await self.db.guild_config.get_config_field(
    guild_id, 
    "prefix", 
    default="!"
)
```text

### AfkController

```python
# Set user as AFK
await self.db.afk.set_member_afk(
    user_id=user_id,
    guild_id=guild_id,
    afk_message="Gone for lunch"
)

# Check if user is AFK
is_afk = await self.db.afk.is_member_afk(user_id, guild_id)

# Remove AFK status
await self.db.afk.remove_member_afk(user_id, guild_id)

# Get AFK information
afk_info = await self.db.afk.get_afk_by_member(user_id, guild_id)
```text

## Database Service

### Connection Management

The database service handles connection lifecycle automatically:

```python
# Service is initialized in bot setup
self.db_service = DatabaseService()
await self.db_service.connect(CONFIG.database_url)

# Check connection status
if self.db_service.is_connected():
    print("Database connected!")

# Cleanup on shutdown
await self.db_service.disconnect()
```text

### Session Handling

Sessions are managed automatically, but you can use manual sessions when needed:

```python
# Manual session (advanced usage)
async with self.db.case.with_session() as session:
    # Multiple operations in same session
    case1 = await self.db.case.create(...)
    case2 = await self.db.case.create(...)
    # Automatically committed
```text

## Migrations

Database schema changes are handled through Alembic migrations:

```bash
# Generate migration
uv run db migrate-generate "add new field"

# Apply migrations
uv run db migrate-push

# Check database health
uv run db health
```text

## Testing

### Using Test Database

Tests use a separate test database with automatic cleanup:

```python
import pytest
from tux.database.service import DatabaseService

@pytest.fixture
async def db_service():
    service = DatabaseService()
    await service.connect("postgresql://test_url")
    yield service
    await service.disconnect()

async def test_case_creation(db_service):
    controller = CaseController(db_service)
    case = await controller.create_case(...)
    assert case.case_id is not None
```text

### Mocking Database Operations

```python
from unittest.mock import AsyncMock

async def test_with_mock():
    mock_db = AsyncMock()
    mock_db.case.create_case.return_value = Case(case_id=1, ...)
    
    # Test your logic with mocked database
    result = await some_function(mock_db)
    assert result is not None
```text

## Performance Considerations

### Query Optimization

```python
# Use specific filters to leverage indexes
cases = await self.db.case.find_all(
    filters={"guild_id": guild_id, "case_user_id": user_id}
)

# Limit results when possible
recent = await self.db.case.find_all(
    filters={"guild_id": guild_id},
    order_by=Case.case_created_at.desc(),
    limit=50
)

# Use count() instead of len(find_all())
total = await self.db.case.count(filters={"guild_id": guild_id})
```text

### Using Bulk Operations

For large datasets, use bulk operations:

```python
# Instead of multiple individual updates
for case_id in case_ids:
    await self.db.case.update_by_id(case_id, case_status=False)

# Use bulk update
await self.db.case.update_where(
    filters={"case_id": {"in": case_ids}},
    values={"case_status": False}
)
```text

## Error Handling

```python
from tux.database.service import DatabaseConnectionError

try:
    case = await self.db.case.create_case(...)
except DatabaseConnectionError:
    # Handle connection issues
    await ctx.send("Database temporarily unavailable")
except Exception as e:
    # Handle other database errors
    logger.error(f"Database error: {e}")
    await ctx.send("An error occurred")
```text

## Best Practices

### 1. Use Type Hints

```python
from tux.database.models import Case

async def get_user_cases(self, user_id: int, guild_id: int) -> list[Case]:
    return await self.db.case.get_cases_by_user(user_id, guild_id)
```text

### 2. Handle None Results

```python
case = await self.db.case.get_by_id(case_id)
if case is None:
    await ctx.send("Case not found")
    return

# Continue with case operations
```text

### 3. Use Transactions for Related Operations

```python
async with self.db.case.with_session() as session:
    # Create case
    case = await self.db.case.create(...)
    
    # Update guild case count
    await self.db.guild.update_by_id(guild_id, case_count=guild.case_count + 1)
    
    # Both operations committed together
```text

### 4. Validate Input Data

```python
if not isinstance(user_id, int) or user_id <= 0:
    raise ValueError("Invalid user ID")

case = await self.db.case.create_case(
    case_user_id=user_id,
    # ... other fields
)
```text

## Common Patterns

### Pagination

```python
async def get_cases_paginated(self, guild_id: int, page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page
    cases = await self.db.case.find_all(
        filters={"guild_id": guild_id},
        order_by=Case.case_created_at.desc(),
        limit=per_page,
        offset=offset
    )
    total = await self.db.case.count(filters={"guild_id": guild_id})
    return cases, total
```text

### Soft Delete Pattern

```python
# Instead of deleting, mark as inactive
await self.db.case.update_by_id(case_id, case_status=False)

# Filter out inactive cases
active_cases = await self.db.case.find_all(
    filters={"guild_id": guild_id, "case_status": True}
)
```text

### Configuration with Defaults

```python
async def get_guild_prefix(self, guild_id: int) -> str:
    config = await self.db.guild_config.get_config_by_guild_id(guild_id)
    return config.prefix if config else "!"
```text

This database layer provides a robust, type-safe foundation for all data operations in Tux while
maintaining clean separation of concerns and excellent performance.
