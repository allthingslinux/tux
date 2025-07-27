# Database Access Patterns Analysis

## Database Architecture Overview

### Core Components

1. **DatabaseClient** (`tux/database/client.py`): Singleton Prisma client wrapper
2. **DatabaseController** (`tux/database/controllers/__init__.py`): Central controller hub
3. **Specialized Controllers**: Individual controllers for each data model
4. **Base Controllers**: Abstract base classes for common operations

### Connection Management

```python
# Singleton pattern with proper lifecycle management
class DatabaseClient:
    _instance = None
    _client: Prisma | None = None
    
    # Connection methods
    async def connect(self) -> None
    async def disconnect(self) -> None
    
    # Transaction support
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None]
```

## Controller Architecture

### Central DatabaseController

```python
class DatabaseController:
    def __init__(self) -> None:
        # Lazy-loaded controllers
        self._afk: AfkController | None = None
        self._case: CaseController | None = None
        self._guild: GuildController | None = None
        # ... 10 total controllers
    
    def __getattr__(self, name: str) -> Any:
        # Dynamic property access with lazy loading
        # Automatic Sentry instrumentation wrapping
```

### Controller Instantiation Patterns

#### Pattern 1: Direct Instantiation (35+ cogs)

```python
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()
```

**Usage Examples**:

```python
# In cog methods
await self.db.case.insert_case(...)
await self.db.snippet.get_snippet_by_name_and_guild_id(...)
await self.db.guild_config.get_jail_role_id(...)
```

#### Pattern 2: Base Class Inheritance (8+ cogs)

```python
# In ModerationCogBase
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()

# In child cogs
class Ban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
```

#### Pattern 3: Specialized Controller Access (3+ cogs)

```python
# In guild/config.py
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController().guild_config
```

## Database Operation Patterns

### Case Management (Moderation)

```python
# Create case
case_result = await self.db.case.insert_case(
    guild_id=ctx.guild.id,
    case_user_id=user.id,
    case_moderator_id=ctx.author.id,
    case_type=case_type,
    case_reason=reason,
    case_expires_at=expires_at,
)

# Query cases
case = await self.db.case.get_case_by_number(ctx.guild.id, case_number)
cases = await self.db.case.get_cases_by_options(ctx.guild.id, options)

# Check restrictions
is_banned = await self.db.case.is_user_under_restriction(
    guild_id=guild_id,
    user_id=user_id,
    active_restriction_type=CaseType.POLLBAN,
    inactive_restriction_type=CaseType.POLLUNBAN,
)
```

### Snippet Management

```python
# Create snippet
await self.db.snippet.create_snippet(
    snippet_name=name,
    snippet_content=content,
    snippet_created_at=created_at,
    snippet_user_id=author_id,
    guild_id=guild_id,
)

# Query snippets
snippet = await self.db.snippet.get_snippet_by_name_and_guild_id(name, guild_id)
snippets = await self.db.snippet.get_all_snippets_by_guild_id(guild_id)

# Create alias
await self.db.snippet.create_snippet_alias(
    snippet_name=name,
    snippet_alias=content,
    snippet_created_at=created_at,
    snippet_user_id=author_id,
    guild_id=guild_id,
)
```

### Guild Configuration

```python
# Role management
await self.db.guild_config.update_perm_level_role(guild_id, level, role_id)
role_id = await self.db.guild_config.get_perm_level_role(guild_id, perm_level)

# Channel management
await self.db.guild_config.update_jail_channel_id(guild_id, channel_id)
channel_id = await self.db.guild_config.get_jail_channel_id(guild_id)

# Log configuration
log_channel_id = await self.db.guild_config.get_log_channel(guild_id, log_type)
```

### Levels System

```python
# XP and level management
current_xp, current_level = await self.db.levels.get_xp_and_level(member.id, guild.id)
await self.db.levels.update_xp_and_level(member.id, guild.id, new_xp, new_level, timestamp)

# Blacklist management
is_blacklisted = await self.db.levels.is_blacklisted(member.id, guild.id)
last_message_time = await self.db.levels.get_last_message_time(member.id, guild.id)
```

## Transaction Handling Patterns

### Current State

- **Limited Transaction Usage**: Most operations are single queries
- **Available Infrastructure**: DatabaseClient provides transaction context manager
- **Inconsistent Application**: Not consistently used across cogs

### Examples of Transaction Needs

```python
# Moderation actions that should be atomic
async with self.db.transaction():
    # Create case
    case = await self.db.case.insert_case(...)
    # Update user status
    await self.db.guild.update_user_status(...)
    # Log action
    await self.db.audit.log_action(...)
```

## Error Handling Patterns

### Controller Level (Good)

```python
# In DatabaseController._get_controller()
try:
    result = await original_method(*args, **kwargs)
except Exception as e:
    span.set_status("internal_error")
    span.set_data("error", str(e))
    raise
```

### Cog Level (Inconsistent)

```python
# Pattern 1: Try/catch with logging
try:
    case_result = await self.db.case.insert_case(...)
except Exception as e:
    logger.error(f"Failed to create case: {e}")
    case_result = None

# Pattern 2: Let exceptions bubble up
case = await self.db.case.get_case_by_number(ctx.guild.id, case_number)
if not case:
    await ctx.send("Case not found.")
    return

# Pattern 3: Base class error handling
await self.send_error_response(ctx, "Database operation failed")
```

## Performance Considerations

### Strengths

- **Lazy Loading**: Controllers instantiated only when needed
- **Connection Pooling**: Prisma handles connection management
- **Async Operations**: Proper async/await usage throughout

### Potential Issues

- **N+1 Queries**: Some operations could benefit from batching
- **Repeated Instantiation**: Each cog creates its own DatabaseController
- **No Caching**: No application-level caching for frequently accessed data

### Optimization Opportunities

```python
# Current: Multiple queries
for user_id in user_ids:
    level = await self.db.levels.get_level(user_id, guild_id)

# Better: Batch query
levels = await self.db.levels.get_levels_batch(user_ids, guild_id)
```

## Monitoring and Observability

### Sentry Integration (Excellent)

```python
# Automatic instrumentation in DatabaseController
with sentry_sdk.start_span(
    op=f"db.controller.{method_name}",
    description=f"{controller_name}.{method_name}",
) as span:
    span.set_tag("db.controller", controller_name)
    span.set_tag("db.operation", method_name)
```

### Logging Patterns

```python
# Inconsistent across cogs
logger.info(f"Created case #{case.case_number}")
logger.error(f"Failed to create case: {e}")
logger.debug(f"User {user} leveled up to {level}")
```

## Data Model Relationships

### Case System

- **Case** → **Guild** (guild_id)
- **Case** → **User** (case_user_id, case_moderator_id)
- **Case** → **CaseType** (enum)

### Snippet System

- **Snippet** → **Guild** (guild_id)
- **Snippet** → **User** (snippet_user_id)
- **Snippet** → **Snippet** (alias relationship)

### Guild Configuration

- **GuildConfig** → **Guild** (guild_id)
- **GuildConfig** → **Channels** (various channel_id fields)
- **GuildConfig** → **Roles** (various role_id fields)

### Levels System

- **Levels** → **Guild** (guild_id)
- **Levels** → **User** (user_id)
- **Levels** → **XP/Level** (calculated fields)

## Anti-Patterns Identified

1. **Repeated Controller Instantiation**: Every cog creates DatabaseController()
2. **Inconsistent Error Handling**: No standardized approach across cogs
3. **Missing Transactions**: Operations that should be atomic aren't
4. **No Caching Strategy**: Frequently accessed data re-queried
5. **Direct Model Access**: Some cogs bypass controller abstractions

## Improvement Recommendations

### High Priority

1. **Dependency Injection**: Inject database controller instead of instantiating
2. **Standardize Error Handling**: Consistent error handling across all cogs
3. **Transaction Boundaries**: Identify and implement proper transaction scopes

### Medium Priority

1. **Caching Layer**: Implement application-level caching for hot data
2. **Batch Operations**: Add batch query methods for common operations
3. **Connection Monitoring**: Add metrics for connection pool usage

### Low Priority

1. **Query Optimization**: Analyze and optimize slow queries
2. **Data Migration Tools**: Better tools for schema changes
3. **Backup Integration**: Automated backup verification
