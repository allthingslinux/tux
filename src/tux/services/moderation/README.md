# Moderation Service Documentation

## Overview

The Moderation Service is a comprehensive, service-oriented architecture designed to handle all moderation operations in the Tux Discord bot. This system replaces the previous mixin-based approach with a clean, testable, and maintainable service composition pattern.

## Architecture

### Service-Oriented Design

The moderation system is built around a service-oriented architecture with four main components:

- **CaseService**: Database operations for moderation cases
- **CommunicationService**: DM sending, embed creation, and user notifications
- **ExecutionService**: Retry logic, circuit breakers, and execution management
- **ModerationCoordinator**: Main orchestrator that coordinates all services

**Supporting Components**:

- **ConditionChecker**: Utility class for permission validation and hierarchy checks
- **ModerationCogBase**: Base class providing service initialization for moderation commands

### Key Benefits

- **Separation of Concerns**: Each service has a single responsibility
- **Testability**: Services can be easily unit tested in isolation
- **Maintainability**: Clear interfaces and dependency injection
- **Resilience**: Circuit breaker patterns and retry logic
- **Extensibility**: Easy to add new moderation actions and features

## Core Services

### CaseService

**Location**: `src/tux/services/moderation/case_service.py`

**Responsibilities**:

- Create, retrieve, and manage moderation cases
- Handle case data persistence and queries
- Provide case statistics and filtering

**Key Methods**:

```python
# Create a new moderation case
await case_service.create_case(
    guild_id=123,
    user_id=456,
    moderator_id=789,
    case_type=CaseType.BAN,
    reason="Violation of rules",
    case_expires_at=datetime.utcnow() + timedelta(days=7)  # For temp actions
)

# Retrieve cases
case = await case_service.get_case(case_id)
user_cases = await case_service.get_user_cases(user_id, guild_id)
active_cases = await case_service.get_active_cases(user_id, guild_id)
```

**Features**:

- Automatic case number generation
- Support for temporary and permanent actions
- Case history tracking
- User-specific case queries

### CommunicationService

**Location**: `src/tux/services/moderation/communication_service.py`

**Responsibilities**:

- Send DMs to users about moderation actions
- Create and send moderation embeds
- Handle error responses and user feedback

**Key Methods**:

```python
# Send DM to user about moderation action
dm_sent = await communication_service.send_dm(
    ctx=ctx,
    silent=False,  # Whether to send DM
    user=target_user,
    reason="Violation of rules",
    dm_action="banned"
)

# Create moderation embed
embed = communication_service.create_embed(
    ctx=ctx,
    title=f"Case #{case.case_number}",
    fields=[
        ("Moderator", f"{ctx.author} ({ctx.author.id})", True),
        ("Target", f"{user} ({user.id})", True),
        ("Reason", case.reason, False)
    ],
    color=0x2B2D31,
    icon_url=ctx.author.display_avatar.url
)

# Send embed response
await communication_service.send_embed(ctx, embed)
```

**Features**:

- Intelligent DM handling (pre/post action based on removal actions)
- Rich embed creation with consistent formatting
- Error handling for failed DMs
- Support for ephemeral responses

### ExecutionService

**Location**: `src/tux/services/moderation/execution_service.py`

**Responsibilities**:

- Execute Discord API actions with retry logic
- Implement circuit breaker pattern for resilience
- Handle rate limiting and transient failures

**Key Features**:

- **Circuit Breaker**: Prevents cascading failures by temporarily disabling operations
- **Exponential Backoff**: Intelligent retry delays with jitter
- **Rate Limit Handling**: Proper handling of Discord API rate limits
- **Operation Tracking**: Per-operation-type failure tracking

**Configuration**:

```python
# Default configuration
failure_threshold = 5      # Open circuit after 5 failures
recovery_timeout = 60.0    # Wait 60 seconds before retrying
max_retries = 3           # Maximum retry attempts
base_delay = 1.0          # Base delay for exponential backoff
```

**Usage**:

```python
# Execute action with retry logic
result = await execution_service.execute_with_retry(
    operation_type="BAN",  # Used for circuit breaker tracking
    action=lambda: guild.ban(user, reason="Violation"),
    user,
    reason="Violation"
)
```

### ConditionChecker

**Location**: `src/tux/services/moderation/condition_checker.py`

**Responsibilities**:

- Permission level validation
- Hierarchy and target validation
- Advanced condition checking

**Permission Levels** (from highest to lowest):

1. `BOT_OWNER` - Bot owner only
2. `SERVER_OWNER` - Server owner
3. `HEAD_ADMINISTRATOR` - Head administrators
4. `ADMINISTRATOR` - Server administrators
5. `SENIOR_MODERATOR` - Senior moderators
6. `MODERATOR` - Full moderators
7. `JUNIOR_MODERATOR` - Junior moderators
8. `TRUSTED` - Trusted members
9. `MEMBER` - Regular server members

**Usage**:

```python
# Decorator-based permission checking
@require_moderator()
async def ban_command(ctx, user):
    # Command logic here
    pass

# Manual condition checking
checker = ConditionChecker()
can_moderate = await checker.check_condition(
    ctx=ctx,
    target_user=target,
    moderator=moderator,
    action="ban"
)
```

**Advanced Features**:

- Context-aware permission checking
- Hierarchy validation (can't moderate users with higher roles)
- Action-specific permission mapping

### ModerationCoordinator

**Location**: `src/tux/services/moderation/moderation_coordinator.py`

**Responsibilities**:

- Orchestrate all moderation operations
- Coordinate between services
- Handle moderation workflow

**Key Method**:

```python
# Execute complete moderation action
case = await moderation_coordinator.execute_moderation_action(
    ctx=ctx,
    case_type=CaseType.BAN,
    user=target_user,
    reason="Violation of rules",
    silent=False,
    dm_action="banned",
    actions=[
        (lambda: ctx.guild.ban(user, reason=reason), type(None))
    ],
    duration=None,  # For temporary actions
    expires_at=None  # Expiration timestamp
)
```

**Workflow**:

1. **Pre-action DM**: Send DM before action for removal actions (ban, kick, tempban)
2. **Permission Validation**: Verify moderator permissions
3. **Execute Discord Actions**: Perform the actual Discord API operations
4. **Create Database Case**: Persist the moderation action
5. **Post-action DM**: Send DM after action for non-removal actions
6. **Send Response**: Provide feedback to moderator

**Removal Actions**: Actions that remove users from server (BAN, KICK, TEMPBAN) get DMs sent **before** the action to ensure the user receives notification.

## Integration with Moderation Commands

### Base Cog Architecture

**Location**: `src/tux/modules/moderation/__init__.py`

The `ModerationCogBase` provides a foundation for all moderation cogs:

```python
class MyModerationCog(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Services are automatically initialized

    async def my_moderation_command(self, ctx, user, *, flags):
        # Use the moderation service
        await self.moderate_user(
            ctx=ctx,
            case_type=CaseType.WARN,
            user=user,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="warned",
            actions=[]  # No Discord actions for warnings
        )
```

**Features**:

- Automatic service initialization
- Consistent moderation workflow
- Built-in error handling
- Service reuse across commands

### Command Integration

Each moderation command integrates with the service architecture:

```python
class Ban(ModerationCogBase):
    @commands.hybrid_command(name="ban")
    @require_moderator()
    async def ban(self, ctx, member, *, flags: BanFlags):
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.BAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="banned",
            actions=[(lambda: ctx.guild.ban(member, reason=flags.reason), type(None))],
        )
```

## Database Schema and Models

### Case Model Structure

The moderation system uses a comprehensive case model that tracks all moderation actions:

```python
class Case(BaseModel, table=True):
    case_id: int | None = Field(default=None, primary_key=True)
    case_status: bool = Field(default=True)  # Active/Inactive status
    case_type: CaseType | None = Field(default=None)  # BAN, WARN, etc.
    case_reason: str = Field(max_length=2000)  # Reason for action
    case_moderator_id: int = Field()  # Discord ID of moderator
    case_user_id: int = Field()  # Discord ID of target user
    case_user_roles: list[int] = Field(default_factory=list)  # User's roles at time of action
    case_number: int | None = Field(default=None)  # Auto-generated per guild
    case_expires_at: datetime | None = Field(default=None)  # For temporary actions
    case_metadata: dict[str, str] | None = Field(default=None)  # Additional data
    audit_log_message_id: int | None = Field(default=None)  # For editing audit messages
    guild_id: int = Field()  # Foreign key to guild
```

### CaseType Enumeration

The system supports 14 different case types:

| Case Type | Description | Example Usage |
|-----------|-------------|---------------|
| `BAN` | Permanent server ban | `/ban @user spam` |
| `UNBAN` | Remove server ban | `/unban @user` |
| `HACKBAN` | Ban user by ID (not in server) | `/hackban 123456789` |
| `TEMPBAN` | Temporary server ban | `/tempban @user 7d spam` |
| `KICK` | Remove from server | `/kick @user harassment` |
| `TIMEOUT` | Temporary communication ban | `/timeout @user 1h spam` |
| `UNTIMEOUT` | Remove timeout | `/untimeout @user` |
| `WARN` | Issue formal warning | `/warn @user rule violation` |
| `JAIL` | Add to jail role | `/jail @user misconduct` |
| `UNJAIL` | Remove from jail | `/unjail @user` |
| `SNIPPETBAN` | Ban from creating snippets | `/snippetban @user` |
| `SNIPPETUNBAN` | Remove snippet ban | `/snippetunban @user` |
| `POLLBAN` | Ban from creating polls | `/pollban @user` |
| `POLLUNBAN` | Remove poll ban | `/pollunban @user` |

### Guild Integration

Each guild has a `case_count` field that tracks the total number of cases, enabling automatic case number generation:

```python
class Guild(BaseModel, table=True):
    guild_id: int = Field(primary_key=True)
    case_count: int = Field(default=0)  # Auto-incremented for case numbers
    # ... other guild fields
```

## Advanced Database Operations

### Case Number Generation

The system implements sophisticated case number generation with race condition protection:

```python
async def create_case(self, case_type: str, case_user_id: int, case_moderator_id: int,
                     guild_id: int, case_reason: str | None = None, **kwargs) -> Case:
    """Create a new case with atomic case number generation."""

    async def _create_with_lock(session: AsyncSession) -> Case:
        # Lock guild row to prevent concurrent case number generation
        stmt = (
            select(Guild)
            .where(Guild.guild_id == guild_id)
            .options(noload("*"))  # Avoid loading relationships
            .with_for_update()  # PostgreSQL row-level locking
        )
        guild = await session.execute(stmt)
        guild = guild.scalar_one_or_none()

        # Create guild if doesn't exist
        if guild is None:
            guild = Guild(guild_id=guild_id, case_count=0)
            session.add(guild)
            await session.flush()

        # Atomically increment case count
        case_number = guild.case_count + 1
        guild.case_count = case_number

        # Create case with generated number
        case = Case(
            case_type=case_type,
            case_user_id=case_user_id,
            case_moderator_id=case_moderator_id,
            guild_id=guild_id,
            case_number=case_number,
            case_reason=case_reason,
            **kwargs
        )
        session.add(case)
        await session.flush()
        await session.refresh(case)
        return case

    return await self.with_session(_create_with_lock)
```

**Key Features**:

- **Atomic Operations**: Uses `SELECT FOR UPDATE` to prevent race conditions
- **Auto-Increment**: Case numbers are unique per guild and auto-generated
- **Guild Creation**: Automatically creates guild records if they don't exist
- **Transaction Safety**: All operations within a single database transaction

### Advanced Query Capabilities

The controller provides rich querying capabilities:

```python
# Get cases by user in guild
cases = await case_controller.get_cases_by_user(user_id=123, guild_id=456)

# Get active cases only
active_cases = await case_controller.get_active_cases_by_user(user_id=123, guild_id=456)

# Filter by multiple criteria
cases = await case_controller.get_cases_by_options(guild_id=456, options={
    "user_id": 123,
    "case_type": "BAN",
    "status": True
})

# Get case by number (unique per guild)
case = await case_controller.get_case_by_number(case_number=42, guild_id=456)

# Get moderator's cases
mod_cases = await case_controller.get_cases_by_moderator(moderator_id=789, guild_id=456)
```

**Indexing Strategy**:

- `guild_id, case_user_id` - Fast user case lookups
- `guild_id, case_moderator_id` - Fast moderator case lookups
- `case_type` - Fast filtering by action type
- `case_status` - Fast active/inactive filtering
- `case_expires_at` - Fast filtering for expired cases
- `guild_id, case_number` - Unique constraint for case number generation

### Data Integrity and Constraints

The system implements multiple layers of data integrity:

**Database-Level Constraints**:

- **Unique Case Numbers**: `UNIQUE(guild_id, case_number)` prevents duplicate case numbers
- **Valid Case Types**: PostgreSQL enum constraint ensures only valid case types
- **Foreign Key Integrity**: Guild relationships maintained with CASCADE deletes

**Application-Level Validation**:

- **Reason Length**: Maximum 2000 characters for case reasons
- **Role Preservation**: User roles captured at moderation time for historical accuracy
- **Expiration Handling**: Proper datetime handling for temporary actions

**Metadata Support**:

```python
# Store additional context with cases
case = await case_service.create_case(
    guild_id=123,
    user_id=456,
    moderator_id=789,
    case_type=CaseType.BAN,
    reason="Spam violation",
    case_metadata={
        "evidence_links": ["https://example.com/evidence1", "https://example.com/evidence2"],
        "previous_warnings": 2,
        "channel_context": "general"
    }
)
```

### Performance Optimizations

**Query Optimization**:

- **Selective Loading**: Uses `noload("*")` to avoid unnecessary relationship loading
- **Batch Operations**: Efficient bulk case retrieval for case lists
- **Index Utilization**: Optimized indexes for common query patterns

**Caching Strategy**:

- **Guild Case Counts**: Cached in guild table for fast case number generation
- **User Role Snapshots**: Stored with each case for historical accuracy
- **Audit Message IDs**: Tracked for efficient audit log updates

### Audit Trail Features

**Comprehensive Logging**:

- **Moderator Attribution**: Every case records the moderator who performed the action
- **Timestamp Tracking**: Automatic created_at/updated_at timestamps
- **Role Context**: User's roles at time of moderation preserved
- **Reason Documentation**: Detailed reasons for transparency

**Audit Log Integration**:

```python
# Cases can reference Discord audit log messages for editing
updated_case = await case_controller.update_audit_log_message_id(
    case_id=123,
    message_id=456789  # Discord message ID in audit log
)
```

**Historical Accuracy**:

- **Immutable Core Data**: Case type, user, moderator, and guild IDs are immutable
- **Updatable Fields**: Reasons and status can be updated for case management
- **Role Preservation**: Historical role information maintained for context

## Migration and Backwards Compatibility

### Database Evolution

The case system supports smooth migrations and backwards compatibility:

**Schema Versioning**:

- **Gradual Rollouts**: New features added without breaking existing functionality
- **Optional Fields**: New fields added as nullable to maintain compatibility
- **Enum Extensions**: New case types added to existing enums

**Legacy Support**:

```python
# Backward compatibility with old duration parameter
await case_service.create_case(
    guild_id=123,
    user_id=456,
    moderator_id=789,
    case_type=CaseType.TIMEOUT,
    reason="Spam",
    duration=3600,  # Legacy parameter (kept for compatibility)
    case_expires_at=datetime.utcnow() + timedelta(hours=1)  # New preferred method
)
```

### API Compatibility

**Method Aliases**:

- `insert_case()` - Alias for `create_case()` for legacy code
- `is_user_under_restriction()` - Supports both old and new parameter styles
- `get_expired_tempbans()` - Placeholder for future tempban expiration logic

## Complete Case Lifecycle

### Case Creation Workflow

Here's how a complete moderation case flows through the system:

```python
# 1. User triggers moderation command
@commands.hybrid_command(name="warn")
@require_junior_mod()
async def warn(self, ctx, member, *, flags: WarnFlags):
    # 2. Service coordinator handles the complete workflow
    case = await self.moderation.execute_moderation_action(
        ctx=ctx,
        case_type=CaseType.WARN,
        user=member,
        reason=flags.reason,
        silent=flags.silent,
        dm_action="warned",
        actions=[],  # No Discord API actions for warnings
    )
    return case
```

**Internal Workflow**:

1. **Permission Check**: `ConditionChecker` validates moderator permissions
2. **DM Decision**: `CommunicationService` determines if/when to send DM
3. **Case Creation**: `CaseService` creates database record with atomic case number
4. **Response Generation**: `CommunicationService` creates and sends embed
5. **Logging**: All actions logged with contextual information

### Case State Management

Cases progress through different states during their lifecycle:

```python
# Active case (default)
case.case_status = True
case.case_expires_at = None  # Permanent action

# Temporary case
case.case_status = True
case.case_expires_at = datetime.utcnow() + timedelta(days=7)

# Closed/expired case
case.case_status = False
case.case_expires_at = None  # Or past date for expired temp actions

# Updated case (reason/status changed)
await case_controller.update_case_by_number(
    guild_id=ctx.guild.id,
    case_number=case.case_number,
    case_reason="Updated reason",
    case_status=False  # Close the case
)
```

### Cross-Service Integration

**Service Dependencies**:

- **CaseService** depends on database access and guild management
- **CommunicationService** depends on Discord bot instance and embed utilities
- **ExecutionService** operates independently for retry logic
- **ConditionChecker** integrates with the permission system
- **ModerationCoordinator** orchestrates all services together

**Data Flow**:

```text
Discord Event → Permission Check → DM Decision → Discord Actions → Database Case → Response
     ↓              ↓              ↓              ↓              ↓              ↓
ConditionChecker → Communication → ExecutionService → CaseService → Communication
     ↑              ↑              ↑              ↑              ↑              ↑
ModerationCoordinator ←────────── Orchestrates ──────────→ Response Generation
```

## Practical Usage Examples

### Basic Moderation Commands

```python
# Ban a user
case = await moderation.execute_moderation_action(
    ctx=ctx,
    case_type=CaseType.BAN,
    user=target_user,
    reason="Spam and harassment",
    silent=False,
    dm_action="banned",
    actions=[(lambda: ctx.guild.ban(target_user, reason=reason), type(None))],
)

# Temporary timeout
expires_at = datetime.utcnow() + timedelta(hours=2)
case = await moderation.execute_moderation_action(
    ctx=ctx,
    case_type=CaseType.TIMEOUT,
    user=target_user,
    reason="Excessive mentions",
    silent=False,
    dm_action="timed out for 2 hours",
    actions=[(lambda: target_user.timeout(timedelta(hours=2), reason=reason), type(None))],
    expires_at=expires_at,
)
```

### Advanced Case Management

```python
# Check user's moderation history
user_cases = await case_service.get_user_cases(user_id=target_user.id, guild_id=ctx.guild.id)
active_cases = await case_service.get_active_cases(user_id=target_user.id, guild_id=ctx.guild.id)

# Filter cases by type
ban_cases = await case_controller.get_cases_by_type(guild_id=ctx.guild.id, case_type="BAN")

# Search cases with multiple criteria
search_results = await case_controller.get_cases_by_options(guild_id=ctx.guild.id, options={
    "user_id": target_user.id,
    "case_type": "WARN",
    "status": True
})

# Update case information
updated_case = await case_controller.update_case_by_number(
    guild_id=ctx.guild.id,
    case_number=123,
    case_reason="Updated reason with more details",
    case_status=False  # Close the case
)
```

### Error Handling Examples

```python
try:
    case = await moderation.execute_moderation_action(...)
    if case:
        await ctx.send(f"✅ Case #{case.case_number} created successfully")
    else:
        await ctx.send("⚠️ Action completed but case creation failed")
except Exception as e:
    # The coordinator handles most errors internally
    # Only connection-level errors reach here
    logger.error(f"Critical moderation error: {e}")
    await ctx.send("❌ Critical error occurred during moderation")
```

### Custom Moderation Actions

You can extend the system with custom actions:

```python
# Define new case type in models.py
class CaseType(str, Enum):
    CUSTOM_ACTION = "CUSTOM_ACTION"
    # ... existing types

# Create custom moderation command
class CustomAction(ModerationCogBase):
    @commands.hybrid_command(name="custom")
    @require_moderator()
    async def custom_action(self, ctx, member, *, flags):
        await self.moderate_user(
            ctx=ctx,
            case_type=CaseType.CUSTOM_ACTION,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="custom action applied",
            actions=[(lambda: self.perform_custom_action(member), type(None))],
        )
```

## Monitoring and Analytics

### Case Statistics

```python
# Get guild statistics
total_cases = await case_controller.get_case_count_by_guild(guild_id=ctx.guild.id)
user_case_count = await case_controller.get_case_count_by_user(
    user_id=target_user.id, guild_id=ctx.guild.id
)

# Moderator statistics
mod_cases = await case_controller.get_cases_by_moderator(
    moderator_id=ctx.author.id, guild_id=ctx.guild.id
)

# Recent activity
recent_cases = await case_controller.get_recent_cases(guild_id=ctx.guild.id, hours=24)
```

### Performance Monitoring

The system provides built-in performance tracking:

- **Circuit Breaker State**: Monitor failure rates per operation type
- **Query Performance**: Track database query execution times
- **DM Success Rates**: Monitor communication delivery success
- **Error Rates**: Track and categorize different error types

### Audit and Compliance

**Data Retention**:

- Cases are permanently stored for audit purposes
- Role information preserved for historical accuracy
- Moderator attribution maintained for accountability
- Timestamp tracking for compliance requirements

**Export Capabilities**:

```python
# Export case data for compliance
all_cases = await case_controller.get_all_cases(guild_id=ctx.guild.id)
export_data = [case.to_dict(include_relationships=True) for case in all_cases]

# Filter for specific time periods or actions
time_filtered = await case_controller.get_cases_by_options(guild_id=ctx.guild.id, options={
    "case_type": "BAN",
    # Add date filtering when implemented
})
```

## Error Handling

### Centralized Error Management

The system uses a centralized error handling approach:

```python
try:
    await moderation_coordinator.execute_moderation_action(...)
except Exception as e:
    # Errors are logged and handled by the coordinator
    # Appropriate responses are sent to users
    pass
```

### Circuit Breaker Protection

- **Failure Threshold**: 5 consecutive failures open the circuit
- **Recovery Timeout**: 60 seconds before attempting operations again
- **Per-Operation Tracking**: Each moderation action type tracks failures independently

### Discord API Error Handling

- **Rate Limits**: Automatic retry with exponential backoff
- **Forbidden/NotFound**: Immediate failure (no retry)
- **Server Errors (5xx)**: Retry with backoff
- **Client Errors (4xx)**: Immediate failure

## Configuration

### Service Configuration

```python
# ExecutionService configuration
execution_service = ExecutionService(
    failure_threshold=5,      # Number of failures before opening circuit
    recovery_timeout=60.0,    # Seconds to wait before retrying
    max_retries=3,           # Maximum retry attempts
    base_delay=1.0           # Base delay for exponential backoff
)

# Or use defaults
execution_service = ExecutionService()
```

### Permission Configuration

Permission levels are defined in the core permission system and used throughout the moderation service for access control.

## Best Practices

### Service Usage

1. **Always use the coordinator**: Don't call individual services directly for moderation actions
2. **Handle errors gracefully**: The coordinator provides appropriate error responses
3. **Use appropriate case types**: Each action has a corresponding case type
4. **Provide clear reasons**: Include detailed reasons for audit trails

### Command Development

1. **Inherit from ModerationCogBase**: Use the provided base class for consistency
2. **Use permission decorators**: Apply appropriate `@require_*` decorators
3. **Leverage flags**: Use the flags system for command parameters
4. **Handle edge cases**: Check for already-applied actions (e.g., already banned)

### Testing

1. **Mock services**: Each service can be mocked for unit testing
2. **Test error scenarios**: Verify circuit breaker and retry behavior
3. **Integration testing**: Test complete moderation workflows

## Future Enhancements

### Planned Features

- **Bulk Operations**: Apply actions to multiple users
- **Scheduled Actions**: Delay moderation actions
- **Appeal System**: Allow users to appeal moderation actions
- **Advanced Analytics**: Detailed moderation statistics and trends
- **Integration APIs**: Webhook support for external moderation tools

### Extension Points

- **Custom Actions**: Add new moderation action types
- **Additional Services**: Extend the service architecture
- **Enhanced Permissions**: More granular permission controls
- **Audit Logging**: Comprehensive audit trails

## Troubleshooting

### Common Issues

1. **Circuit Breaker Open**: Too many failures - wait for recovery timeout
2. **Permission Denied**: Check user permission levels and hierarchy
3. **DM Failures**: Users may have DMs disabled or bot blocked
4. **Discord API Errors**: Check rate limits and bot permissions

### Debugging

Enable debug logging to see detailed operation flow:

```python
import logging
logging.getLogger('tux.services.moderation').setLevel(logging.DEBUG)
```

### Monitoring

The system provides built-in monitoring through:

- Structured logging with contextual information
- Circuit breaker state tracking
- Performance metrics collection
- Error rate monitoring

## Areas for Improvement and Concerns

### Documentation Issues Identified

1. **Service Count Inconsistency**: ~~The documentation initially stated there are 5 core services, but there are actually 4 main components (3 services + ModerationCoordinator) with ConditionChecker as a supporting utility class.~~ ✅ **RESOLVED** - Documentation updated.

2. **Method Signature Accuracy**: ~~Some method signatures in examples may need verification against actual implementations.~~ ✅ **RESOLVED** - All examples updated to match current API.

3. **Index Documentation**: ~~The `case_number` unique constraint was missing from the indexing strategy documentation.~~ ✅ **RESOLVED** - Documentation updated.

4. **Test Failures**: ~~Critical integration tests were failing due to parameter naming inconsistencies.~~ ✅ **RESOLVED** - Fixed parameter name mismatch in ModerationCoordinator.

### Potential Refactoring Opportunities

1. **Service Naming**: Consider renaming `ConditionChecker` to `PermissionChecker` for clarity about its purpose.

2. **Method Consolidation**: ✅ **RESOLVED** - The `get_operation_type` method existed in both `CaseService` and `ExecutionService` but was removed from CaseService as it was unused dead code.

3. **Error Handling Patterns**: The current error handling is mostly centralized in the coordinator, but some services could benefit from more specific error types.

4. **Configuration Management**: ~~Service configuration was hardcoded but ExecutionService is now configurable.~~ ✅ **PARTIALLY RESOLVED** - ExecutionService now accepts configuration parameters. Consider per-guild configuration for advanced use cases.

### Code Quality Concerns

1. **Type Safety**: ~~Some areas used `Any` types but `actions` parameter in `execute_moderation_action` now uses `Type[Any]` for better type checking.~~ ✅ **IMPROVED** - Enhanced type annotations for better type safety.

2. **Magic Numbers**: ~~Circuit breaker configuration used hardcoded values but is now configurable through constructor parameters.~~ ✅ **RESOLVED** - Configuration parameters are now properly parameterized.

3. **Exception Handling**: Broad `Exception` catches in some places could be more specific to catch only expected errors.

### Performance Considerations

1. **Database Query Optimization**: The case number generation uses `SELECT FOR UPDATE` which may not scale well with high concurrency.

2. **Memory Usage**: Large case lists could benefit from pagination rather than loading all records.

3. **Caching Strategy**: Guild case counts are cached in the database but could benefit from application-level caching for frequently accessed data.

### Testing Gaps

1. **Service Integration Testing**: While individual services are testable, full integration tests across all services would be valuable.

2. **Error Scenario Testing**: Circuit breaker behavior and retry logic should be thoroughly tested under various failure conditions.

3. **Performance Testing**: Load testing for high-volume moderation scenarios.

### Future Enhancement Opportunities

1. **Bulk Operations**: Add support for moderating multiple users simultaneously.

2. **Scheduled Actions**: Implement delayed moderation actions (e.g., "ban this user in 24 hours").

3. **Appeal System**: Add case appeal functionality with escalation workflows.

4. **Advanced Analytics**: Implement detailed moderation statistics and trend analysis.

5. **Audit Trail Export**: Add comprehensive audit log export capabilities for compliance.

## Support

For questions or issues with the moderation service:

1. Check the logs for detailed error information
2. Verify Discord permissions and bot configuration
3. Review the permission system configuration
4. Ensure all services are properly initialized
