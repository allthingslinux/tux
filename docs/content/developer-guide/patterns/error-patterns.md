# Tux Error Handling Standards & Best Practices

## Overview

This document establishes error handling standards for the Tux Discord bot codebase. Our approach
prioritizes **user experience**, **debugging capability**, and **system reliability** through
consistent error handling patterns.

## Core Principles

### 1. **Fail Gracefully**

- Always provide meaningful feedback to users
- Never expose internal errors or stack traces to end users
- Degrade functionality gracefully when possible

### 2. **Log Everything**

- Use structured logging with appropriate levels
- Include context for debugging (user ID, guild ID, command, etc.)
- Log both successful operations and failures

### 3. **Be Specific**

- Catch specific exceptions when possible
- Avoid broad `except Exception` unless necessary
- Chain exceptions to preserve error context

### 4. **Consistent Patterns**

- Follow established patterns across the codebase
- Use the global error handler for command-level errors
- Handle infrastructure errors locally with proper fallbacks

## Error Handling Architecture

### Global Error Handler

Located in `src/tux/services/handlers/error/handler.py`

**Responsibilities:**

- Command-level error handling
- User-friendly error messages
- Sentry integration for error tracking
- Automatic error categorization

**When to use:**

- Command execution errors
- Permission errors
- Validation errors
- Most user-facing errors

### Local Error Handling

**When to use:**

- Infrastructure operations (HTTP, database, file I/O)
- Background tasks
- Service initialization
- Operations that need graceful degradation

## Tux Exception Hierarchy

All Tux-specific exceptions inherit from `TuxError` base class for consistent error handling:

```text
TuxError
├── TuxConfigurationError
├── TuxRuntimeError
├── TuxDatabaseError
│   ├── TuxDatabaseConnectionError
│   ├── TuxDatabaseMigrationError
│   └── TuxDatabaseQueryError
├── TuxPermissionError
│   ├── TuxPermissionLevelError
│   └── TuxAppCommandPermissionLevelError
├── TuxAPIError
│   ├── TuxAPIConnectionError
│   ├── TuxAPIRequestError
│   ├── TuxAPIResourceNotFoundError
│   └── TuxAPIPermissionError
├── TuxCodeExecutionError
│   ├── TuxMissingCodeError
│   ├── TuxInvalidCodeFormatError
│   ├── TuxUnsupportedLanguageError
│   └── TuxCompilationError
└── TuxServiceError
    ├── TuxCogLoadError
    └── TuxHotReloadError
        ├── TuxDependencyResolutionError
        ├── TuxFileWatchError
        ├── TuxModuleReloadError
        └── TuxConfigurationError
```

### Using Specific Exceptions

```python
# ✅ GOOD: Use specific exception types
from tux.shared.exceptions import TuxDatabaseConnectionError
raise TuxDatabaseConnectionError("Cannot connect to PostgreSQL")

# ❌ BAD: Generic exceptions
raise Exception("Database connection failed")

# ❌ BAD: String matching for error types
try:
    # some operation
except Exception as e:
    if "connection" in str(e).lower():
        # handle connection error

# ✅ GOOD: Catch specific exception types
try:
    # some operation
except ConnectionError as e:
    raise TuxDatabaseConnectionError("Database connection failed") from e
except TuxDatabaseError:
    # handle database errors
except Exception as e:
    # handle other errors
```

## Patterns & Examples

### ✅ Sentry Integration

```python
# ✅ GOOD: Use unified Sentry utilities
from tux.services.sentry import capture_database_error, capture_api_error, capture_exception_safe

# Database errors
try:
    await db.execute(query)
except Exception as e:
    capture_database_error(e, operation="insert", table="cases")
    raise TuxDatabaseQueryError("Failed to insert case") from e

# API errors
try:
    response = await client.get(url)
except httpx.RequestError as e:
    capture_api_error(e, service_name="GitHub", endpoint=url)
    raise TuxAPIConnectionError("GitHub API unavailable") from e

# Generic errors with context
try:
    # some operation
except Exception as e:
    capture_exception_safe(e, extra_context={"operation": "startup", "component": "bot"})
    raise TuxRuntimeError("Operation failed") from e

# ❌ BAD: Raw Sentry calls
import sentry_sdk
sentry_sdk.capture_exception(e)  # Missing context and standardization
```

### ✅ HTTP Operations

```python
async def fetch_data(self, url: str) -> dict | None:
    """Fetch data from API with proper error handling."""
    try:
        response = await http_client.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {url}")
        return None
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return None
```

### ✅ Database Operations

```python
async def create_user_record(self, user_id: int, data: dict) -> bool:
    """Create user record with error handling."""
    try:
        await self.db.user.create(user_id=user_id, **data)
        logger.info(f"Created user record for {user_id}")
        return True
    except IntegrityError:
        logger.warning(f"User {user_id} already exists")
        return False
    except Exception as e:
        logger.error(f"Failed to create user {user_id}: {e}")
        return False
```

### ✅ Command Error Handling

```python
@commands.command()
async def my_command(self, ctx: commands.Context[Tux]) -> None:
    """Command with proper validation."""
    # Let global error handler catch validation errors
    if not ctx.guild:
        raise commands.NoPrivateMessage()
    
    # Handle infrastructure errors locally
    data = await self.fetch_user_data(ctx.author.id)
    if data is None:
        await ctx.reply("Unable to fetch user data. Please try again later.")
        return
    
    # Process data...
```

### ✅ Service Initialization

```python
async def initialize_service(self) -> None:
    """Initialize service with graceful degradation."""
    try:
        await self.connect_to_external_api()
        self.enabled = True
        logger.info("Service initialized successfully")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        self.enabled = False
        # Continue without this service
```

## Anti-Patterns to Avoid

### ❌ Silent Failures

```python
# BAD: Silent failure
try:
    await some_operation()
except Exception:
    return None  # User gets no feedback

# GOOD: Proper error handling
try:
    await some_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise  # Let global handler provide user feedback
```

### ❌ Exposing Internal Errors

```python
# BAD: Exposing stack traces
except Exception as e:
    await ctx.reply(f"Error: {e}")

# GOOD: User-friendly messages
except Exception as e:
    logger.error(f"Command failed: {e}")
    await ctx.reply("Something went wrong. Please try again later.")
```

### ❌ Overly Broad Catches

```python
# BAD: Too broad
try:
    data = response.json()
except Exception:
    return None

# GOOD: Specific exceptions
try:
    data = response.json()
except (JSONDecodeError, KeyError) as e:
    logger.warning(f"Invalid JSON response: {e}")
    return None
```

## Error Categories & Handling

### User Errors

**Examples:** Invalid input, missing permissions, rate limits
**Handling:** Global error handler with helpful messages

```python
# Let global handler catch these
raise commands.BadArgument("Invalid user ID format")
raise commands.MissingPermissions(["manage_messages"])
```

### Infrastructure Errors

**Examples:** Network failures, database timeouts, file I/O errors
**Handling:** Local handling with graceful degradation

```python
try:
    result = await external_api_call()
except (httpx.TimeoutException, httpx.ConnectError):
    # Graceful fallback
    result = get_cached_result()
```

### System Errors

**Examples:** Configuration errors, startup failures, critical bugs
**Handling:** Log and fail fast or disable functionality

```python
try:
    self.config = load_config()
except ConfigError as e:
    logger.critical(f"Invalid configuration: {e}")
    raise SystemExit(1)
```

## Logging Standards

### Log Levels

- **DEBUG:** Detailed diagnostic information
- **INFO:** General operational messages
- **WARNING:** Recoverable errors, degraded functionality
- **ERROR:** Serious errors that need attention
- **CRITICAL:** System-threatening errors

### Log Format

```python
# Include context for debugging
logger.info(f"User {user_id} executed command '{command}' in guild {guild_id}")
logger.error(f"Database query failed for user {user_id}: {error}")
logger.warning(f"Rate limit hit for guild {guild_id}, using cached data")
```

## Error Recovery & Graceful Degradation

### Service Initialization

```python
class MyService:
    def __init__(self):
        try:
            self._initialize()
        except Exception as e:
            capture_exception_safe(e, extra_context={"service": "MyService"})
            raise TuxConfigurationError(f"Failed to initialize MyService: {e}") from e
```

### Graceful Degradation

```python
try:
    # Try primary operation
    result = await primary_api_call()
except TuxAPIConnectionError:
    logger.warning("Primary API unavailable, using fallback")
    result = await fallback_operation()
except TuxConfigurationError as e:
    logger.warning(f"Skipping feature due to configuration: {e}")
    return  # Skip feature gracefully
```

### Command Error Handling

```python
@commands.command()
async def my_command(self, ctx: commands.Context[Tux]) -> None:
    try:
        result = await some_operation()
        await ctx.send(f"Result: {result}")
    except TuxAPIConnectionError:
        await ctx.send("❌ External service is currently unavailable")
    except TuxPermissionError as e:
        await ctx.send(f"❌ {e}")
    except Exception as e:
        capture_exception_safe(e, extra_context={"command": "my_command", "user_id": ctx.author.id})
        await ctx.send("❌ An unexpected error occurred")
        raise  # Re-raise for global error handler
```

## Testing Error Handling

### Unit Tests

```python
async def test_http_error_handling():
    """Test HTTP error handling."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.TimeoutException()
        result = await service.fetch_data("http://example.com")
        assert result is None
```

### Integration Tests

```python
async def test_command_with_db_error():
    """Test command behavior during database errors."""
    with patch.object(db, 'create_user') as mock_create:
        mock_create.side_effect = DatabaseError()
        # Verify graceful handling
```

## Sentry Integration

### Automatic Error Tracking

- All unhandled exceptions are automatically sent to Sentry
- Include user context (ID, guild, command) for debugging
- Use Sentry's breadcrumbs for operation tracking

### Manual Error Reporting

```python
from tux.services.sentry import capture_exception_safe

try:
    critical_operation()
except Exception as e:
    logger.error(f"Critical operation failed: {e}")
    capture_exception_safe(e, extra_context={"user_id": user_id})
    raise
```

## Migration Guidelines

### Existing Code

1. **Identify critical paths:** HTTP, database, file operations
2. **Add specific error handling:** Replace broad catches
3. **Improve user feedback:** Replace generic error messages
4. **Add logging:** Include context for debugging

### New Code

1. **Plan error scenarios:** What can go wrong?
2. **Choose handling strategy:** Global vs local
3. **Implement graceful degradation:** Fallback options
4. **Add comprehensive logging:** Success and failure cases

## Code Review Checklist

### Error Handling Review

- [ ] Are all external operations (HTTP, DB, file I/O) wrapped in try/except?
- [ ] Are exceptions specific rather than broad `Exception` catches?
- [ ] Do error messages provide helpful information to users?
- [ ] Is appropriate logging included for debugging?
- [ ] Are errors properly chained to preserve context?
- [ ] Does the code degrade gracefully on errors?
- [ ] Are critical errors properly escalated?

### User Experience Review

- [ ] Do users receive meaningful feedback on errors?
- [ ] Are internal errors hidden from users?
- [ ] Is the bot still functional after errors?
- [ ] Are error messages actionable when possible?

## Performance Considerations

### Error Handling Overhead

- Keep error handling lightweight
- Avoid expensive operations in exception handlers
- Use lazy evaluation for error context

### Resource Cleanup

```python
async def process_file(self, file_path: str) -> None:
    """Process file with proper cleanup."""
    file_handle = None
    try:
        file_handle = await aiofiles.open(file_path)
        await self.process_data(file_handle)
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise
    finally:
        if file_handle:
            await file_handle.close()
```

## Monitoring & Alerting

### Key Metrics

- Error rate by command/module
- Response time degradation during errors
- User-facing error frequency
- Critical system error alerts

### Dashboards

- Real-time error tracking via Sentry
- Command success/failure rates
- Infrastructure health monitoring
- User experience impact metrics

---

## Quick Reference

### Common Patterns

```python
# HTTP with fallback
try:
    response = await http_client.get(url)
    response.raise_for_status()
    return response.json()
except Exception as e:
    logger.warning(f"API call failed: {e}")
    return fallback_data

# Database with user feedback
try:
    await db.operation()
except Exception as e:
    logger.error(f"Database error: {e}")
    await ctx.reply("Database temporarily unavailable.")

# Service initialization
try:
    await service.initialize()
except Exception as e:
    logger.error(f"Service init failed: {e}")
    self.enabled = False
```

### When to Use Global vs Local

- **Global:** User input errors, command validation, permissions
- **Local:** Infrastructure, background tasks, service initialization

### Error Message Guidelines

- Be specific but not technical
- Suggest solutions when possible
- Include relevant context (what failed)
- Maintain consistent tone and format

---

*This guide should be updated as error handling patterns evolve. All team members should follow
these standards for consistent, reliable error handling across the Tux codebase.*
