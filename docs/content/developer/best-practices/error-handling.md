---
title: Error Handling Best Practices
description: Error handling best practices for Tux development, including exception patterns, graceful degradation, and debugging techniques.
---

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
# ✅ Good: Use specific exception types
from tux.shared.exceptions import TuxDatabaseConnectionError
raise TuxDatabaseConnectionError("Cannot connect to PostgreSQL")

# ❌ Bad: Generic exceptions
raise Exception("Database connection failed")

# ✅ Good: Catch specific exception types and chain them
try:
    await database_operation()
except ConnectionError as e:
    raise TuxDatabaseConnectionError("Database connection failed") from e
except TuxDatabaseError:
    # Handle database errors
    pass
```

## Error Categories & Handling Strategies

### User Errors

**Examples:** Invalid input, missing permissions, rate limits, command not found
**Handling:** Global error handler with user-friendly messages

```python
# Let global handler catch these - they become user-friendly messages
raise commands.BadArgument("Invalid user ID format")
raise commands.MissingPermissions(["manage_messages"])
raise TuxPermissionLevelError("moderator")
```

### Infrastructure Errors

**Examples:** Network failures, database timeouts, file I/O errors, external API issues
**Handling:** Local handling with graceful degradation and fallbacks

```python
try:
    result = await external_api_call()
except (httpx.TimeoutException, httpx.ConnectError):
    # Graceful fallback to cached data
    logger.warning("API unavailable, using cached data")
    result = get_cached_result()
except Exception as e:
    logger.error(f"API call failed: {e}")
    result = None
```

### System Errors

**Examples:** Configuration errors, startup failures, critical bugs, missing dependencies
**Handling:** Log and fail fast, or disable functionality gracefully

```python
try:
    self.config = load_config()
except Exception as e:
    logger.critical(f"Invalid configuration: {e}")
    raise SystemExit(1) from e
```

## Core Principles

### Fail Gracefully, Log Aggressively

```python
# ✅ Good: Graceful degradation with detailed logging
async def get_user_profile(user_id: int) -> dict | None:
    """Fetch user profile with graceful error handling."""
    try:
        profile = await self.api_client.get_user(user_id)
        logger.debug("Successfully fetched user profile", user_id=user_id)
        return profile
    except TuxAPIConnectionError:
        logger.warning("API unavailable, cannot fetch user profile", user_id=user_id)
        return None  # Graceful degradation
    except Exception as e:
        logger.error("Unexpected error fetching user profile", user_id=user_id, exc_info=True)
        return None
```

### Be Specific, Not Generic

```python
# ❌ Bad: Overly broad exception handling
try:
    await risky_operation()
except Exception as e:
    logger.error("Something went wrong")

# ✅ Good: Specific exception handling
try:
    await risky_operation()
except TuxDatabaseConnectionError:
    logger.warning("Database temporarily unavailable, retrying...")
    await asyncio.sleep(1)
    return await risky_operation()
except TuxPermissionError as e:
    logger.warning("Permission denied", user_id=user_id, required_perm=e.permission)
    raise  # Re-raise for global handler
except Exception as e:
    logger.error("Unexpected error in risky_operation", exc_info=True)
    raise
```

## Error Handling Patterns

### Database Operations

```python
from tux.database.service import DatabaseService

async def create_user_with_retry(self, user_data: dict) -> User | None:
    """Create user with database error handling and retry logic."""

    for attempt in range(3):
        try:
            async with self.db.session() as session:
                user = User(**user_data)
                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.info("User created successfully", user_id=user.id)
                return user

        except TuxDatabaseConnectionError as e:
            if attempt == 2:  # Last attempt
                logger.error("Failed to create user after 3 attempts",
                           user_data=user_data, error=str(e))
                raise

            logger.warning(f"Database connection failed, retrying (attempt {attempt + 1})",
                         error=str(e))
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

        except TuxDatabaseQueryError as e:
            logger.error("Database query failed", user_data=user_data, error=str(e))
            raise  # Don't retry query errors

    return None
```

### External API Calls

```python
from tux.services.http_client import http_client

async def fetch_github_user(self, username: str) -> dict | None:
    """Fetch GitHub user with comprehensive error handling."""

    try:
        response = await http_client.get(
            f"https://api.github.com/users/{username}",
            timeout=10.0
        )

        data = response.json()
        logger.debug("GitHub user fetched", username=username, user_id=data.get("id"))
        return data

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info("GitHub user not found", username=username)
            return None
        elif e.response.status_code == 403:
            logger.warning("GitHub API rate limited", username=username,
                         reset_time=e.response.headers.get("X-RateLimit-Reset"))
            return None
        else:
            logger.error("GitHub API error",
                       username=username, status=e.response.status_code)
            raise TuxAPIRequestError("github", e.response.status_code, e.response.reason_phrase)

    except httpx.TimeoutException:
        logger.warning("GitHub API timeout", username=username)
        raise TuxAPIConnectionError("github", TimeoutError("Request timed out"))

    except httpx.RequestError as e:
        logger.error("GitHub API connection error", username=username, error=str(e))
        raise TuxAPIConnectionError("github", e)
```

### File Operations

```python
import aiofiles
from pathlib import Path

async def save_user_avatar(self, user_id: int, avatar_data: bytes) -> bool:
    """Save user avatar with proper error handling."""

    avatar_path = Path(f"avatars/{user_id}.png")

    try:
        # Ensure directory exists
        avatar_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file atomically
        temp_path = avatar_path.with_suffix('.tmp')
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(avatar_data)

        # Atomic rename
        temp_path.replace(avatar_path)

        logger.info("User avatar saved", user_id=user_id, size=len(avatar_data))
        return True

    except PermissionError as e:
        logger.error("Permission denied saving avatar", user_id=user_id, path=str(avatar_path))
        raise TuxPermissionError("file_write") from e

    except OSError as e:
        logger.error("Failed to save avatar file", user_id=user_id, path=str(avatar_path), error=str(e))
        # Clean up temp file if it exists
        temp_path.unlink(missing_ok=True)
        return False
```

## Command Error Handling

### Global Error Handler Integration

Commands automatically use the global error handler (`src/tux/services/handlers/error/cog.py`). Focus on business logic exceptions - the handler provides:

- **Automatic error categorization** using `ERROR_CONFIG_MAP`
- **User-friendly messages** based on error type
- **Sentry integration** with proper context
- **Command suggestions** for unknown commands
- **Structured logging** with appropriate levels

The handler covers hundreds of error types including Discord API errors, permission errors, validation errors, and custom Tux exceptions.

```python
@commands.hybrid_command(name="ban")
async def ban_user(self, ctx: commands.Context[Tux], user: discord.User, reason: str):
    """Ban a user from the server."""

    # Validate input (will raise exceptions caught by global handler)
    if len(reason) < 3:
        raise TuxValidationError("Reason must be at least 3 characters long")

    if user == ctx.author:
        raise TuxPermissionError("You cannot ban yourself")

    # Check permissions (framework handles this, but be explicit)
    if not ctx.guild.me.guild_permissions.ban_members:
        raise TuxPermissionError("Bot lacks ban permissions")

    try:
        # Attempt ban
        await ctx.guild.ban(user, reason=reason, delete_message_days=0)

        # Log success
        logger.info("User banned successfully",
                  moderator=ctx.author.id,
                  target=user.id,
                  reason=reason)

        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.SUCCESS,
            title="User Banned",
            description=f"Successfully banned {user.mention}",
            user_name=ctx.author.name,
        )
        await ctx.send(embed=embed)

    except discord.Forbidden:
        raise TuxPermissionError("Insufficient permissions to ban this user") from discord.Forbidden
    except discord.HTTPException as e:
        logger.error("Discord API error during ban", target=user.id, error=str(e))
        raise TuxAPIError(f"Failed to ban user: {e}") from e
```

### Custom Validation Errors

```python
class TuxValidationError(TuxError):
    """Raised when user input validation fails."""

    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid {field}: {reason}")

# Usage in commands
@commands.hybrid_command(name="set_prefix")
async def set_prefix(self, ctx: commands.Context[Tux], prefix: str):
    """Set server command prefix."""

    if len(prefix) > 5:
        raise TuxValidationError("prefix", prefix, "must be 5 characters or less")

    if any(char in prefix for char in ['@', '#', '<', '>']):
        raise TuxValidationError("prefix", prefix, "cannot contain Discord formatting characters")

    # Set prefix logic...
```

## Async Error Handling

### Task Exception Handling

```python
async def process_users_batch(self, user_ids: list[int]):
    """Process multiple users concurrently with proper error handling."""

    async def process_single_user(user_id: int):
        try:
            return await self.process_user(user_id)
        except Exception as e:
            logger.error("Failed to process user", user_id=user_id, error=str(e))
            return None  # Return None for failed users

    # Process concurrently
    tasks = [process_single_user(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results
    successful = []
    failed = []

    for user_id, result in zip(user_ids, results):
        if isinstance(result, Exception):
            logger.warning("User processing failed", user_id=user_id, error=str(result))
            failed.append(user_id)
        elif result is None:
            failed.append(user_id)
        else:
            successful.append(result)

    logger.info("Batch processing complete",
               total=len(user_ids),
               successful=len(successful),
               failed=len(failed))

    return successful, failed
```

### Timeout Handling

```python
async def call_with_timeout(self, coro, timeout: float = 30.0):
    """Execute coroutine with timeout and proper error handling."""

    try:
        return await asyncio.wait_for(coro, timeout=timeout)

    except asyncio.TimeoutError:
        logger.warning("Operation timed out", timeout=timeout)
        raise TuxTimeoutError(f"Operation exceeded {timeout}s timeout")

    except Exception as e:
        logger.error("Operation failed", error=str(e))
        raise
```

## Context Managers for Error Handling

### Database Transactions

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_transaction(self):
    """Context manager for database transactions with error handling."""
    session = None
    try:
        async with self.db.session() as session:
            yield session
            await session.commit()
            logger.debug("Transaction committed successfully")

    except Exception as e:
        if session:
            await session.rollback()
            logger.warning("Transaction rolled back due to error", error=str(e))
        raise

# Usage
async def transfer_credits(self, from_user: int, to_user: int, amount: int):
    async with self.database_transaction() as session:
        # Deduct from sender
        await session.execute(
            "UPDATE users SET credits = credits - :amount WHERE id = :user_id",
            {"amount": amount, "user_id": from_user}
        )

        # Add to receiver
        await session.execute(
            "UPDATE users SET credits = credits + :amount WHERE id = :user_id",
            {"amount": amount, "user_id": to_user}
        )
```

### Resource Cleanup

```python
@asynccontextmanager
async def temp_file_context(self, suffix: str = ""):
    """Context manager for temporary files with cleanup."""
    import tempfile
    import aiofiles

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            temp_file = Path(f.name)

        yield temp_file

    except Exception as e:
        logger.error("Error in temp file operation", temp_file=str(temp_file), error=str(e))
        raise

    finally:
        # Always cleanup
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug("Cleaned up temp file", path=str(temp_file))
            except Exception as e:
                logger.warning("Failed to cleanup temp file", path=str(temp_file), error=str(e))
```

## Testing Error Conditions

### Exception Testing

```python
import pytest
from unittest.mock import patch, AsyncMock

class TestUserService:
    async def test_create_user_database_error(self):
        """Test user creation handles database errors properly."""
        service = UserService()

        with patch.object(service.db, 'session') as mock_session:
            mock_session.return_value.__aenter__.side_effect = TuxDatabaseConnectionError()

            with pytest.raises(TuxDatabaseConnectionError):
                await service.create_user({"name": "test"})

    async def test_get_user_not_found(self):
        """Test user lookup returns None for non-existent users."""
        service = UserService()

        with patch.object(service.db, 'get_user', return_value=None):
            result = await service.get_user(999)

            assert result is None
            # Check that appropriate warning was logged
            # (would use caplog fixture in actual test)

    async def test_api_timeout_retry(self):
        """Test API calls retry on timeout."""
        service = UserService()

        with patch.object(service.session, 'get') as mock_get:
            # First call times out, second succeeds
            mock_get.side_effect = [
                asyncio.TimeoutError(),
                AsyncMock(status=200, json=AsyncMock(return_value={"user": "data"}))
            ]

            result = await service.fetch_user_data(123)

            assert result == {"user": "data"}
            assert mock_get.call_count == 2
```

### Integration Testing

```python
import httpx
from unittest.mock import MagicMock, patch

async def test_full_user_workflow_with_errors(self, db_session):
    """Test complete user workflow including error scenarios."""

    # Setup - create user successfully
    user = await create_test_user(db_session, "test@example.com")

    # Test successful operations
    profile = await get_user_profile(user.id)
    assert profile is not None

    # Test error scenarios
    with patch('tux.services.http_client.http_client.get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock())
        mock_get.return_value = mock_response

        profile = await get_user_profile(user.id)
        assert profile is None  # Should degrade gracefully

    # Verify error was logged (would check with caplog in real test)
```

## Performance Considerations

### Avoid Expensive Operations in Error Paths

```python
# ❌ Bad: Expensive computation in error handling
try:
    result = await process_data(large_dataset)
except Exception as e:
    # Don't do this - expensive operation in error path
    logger.error("Processing failed", dataset_summary=analyze_dataset(large_dataset))
    raise

# ✅ Good: Pre-compute or use lazy evaluation
def get_dataset_summary(dataset):
    return {
        "size": len(dataset),
        "type": type(dataset).__name__,
        "sample": dataset[:5] if len(dataset) > 5 else dataset
    }

try:
    dataset_summary = get_dataset_summary(large_dataset)
    result = await process_data(large_dataset)
    logger.info("Processing complete", dataset_summary=dataset_summary)
except Exception as e:
    logger.error("Processing failed", dataset_summary=dataset_summary, exc_info=True)
    raise
```

### Exception Creation Cost

```python
# ✅ Good: Create exceptions only when needed
def validate_user_data(self, data: dict) -> list[str]:
    """Validate user data and return list of errors."""
    errors = []

    if not data.get("email"):
        errors.append("Email is required")
    if not data.get("name"):
        errors.append("Name is required")

    return errors

def create_user(self, data: dict):
    errors = self.validate_user_data(data)
    if errors:
        # Create exception only when validation fails
        raise TuxValidationError(f"Validation failed: {', '.join(errors)}")

    # Create user...
```

## Anti-Patterns

### ❌ Silent Failures

```python
# Bad: Swallows all errors
try:
    await risky_operation()
except Exception:
    pass  # Silent failure - very bad

# Good: At minimum log the error
try:
    await risky_operation()
except Exception as e:
    logger.error("Operation failed", error=str(e), exc_info=True)
    # Continue or raise as appropriate
```

### ❌ Re-raising with Generic Exceptions

```python
# Bad: Loses original exception context
try:
    await database_operation()
except Exception:
    raise TuxDatabaseError("Operation failed")  # Loses original error

# Good: Chain exceptions properly
try:
    await database_operation()
except Exception as e:
    raise TuxDatabaseError("Operation failed") from e  # Preserves context
```

### ❌ Overly Broad Exception Handling

```python
# Bad: Catches too much
async def send_moderation_dm(self, user: discord.User, reason: str):
    try:
        await user.send(f"You have been moderated for: {reason}")
    except Exception:  # Catches KeyboardInterrupt, SystemExit, etc.
        return False

# Good: Be specific
async def send_moderation_dm(self, user: discord.User, reason: str):
    try:
        await user.send(f"You have been moderated for: {reason}")
    except (discord.Forbidden, discord.HTTPException) as e:  # Specific exceptions
        logger.error("Failed to send moderation DM", user_id=user.id, error=str(e))
        return False
```

## Code Review Checklist

### Error Handling Review

- [ ] Are all external operations (HTTP, database, file I/O) wrapped in try/except?
- [ ] Are exceptions specific rather than broad `Exception` catches?
- [ ] Do error messages provide helpful information to users?
- [ ] Is appropriate logging included for debugging (user ID, operation context)?
- [ ] Are errors properly chained to preserve context (`raise ... from e`)?
- [ ] Does the code degrade gracefully on errors?
- [ ] Are critical errors properly escalated to global handler?
- [ ] Are Tux-specific exceptions used instead of generic ones?

### User Experience Review

- [ ] Do users receive meaningful feedback on errors?
- [ ] Are internal errors and stack traces hidden from users?
- [ ] Is the bot still functional after recoverable errors?
- [ ] Are error messages actionable when possible?
- [ ] Do error messages maintain consistent tone and formatting?

## Error Monitoring

### Sentry Integration

Tux provides specialized Sentry utilities for different error types:

```python
from tux.services.sentry import (
    capture_exception_safe,
    capture_tux_exception,
    capture_database_error,
    capture_api_error,
    capture_cog_error
)

async def critical_operation(self, ctx):
    """Critical operation with Sentry monitoring."""
    try:
        await self.perform_critical_task()
    except TuxDatabaseError as e:
        # Specialized database error capture
        capture_database_error(e, query="SELECT * FROM users", operation="user_sync")

    except TuxAPIError as e:
        # Specialized API error capture
        capture_api_error(e, endpoint="/api/users", status_code=500)

    except Exception as e:
        # Generic error capture with context
        capture_exception_safe(e, extra_context={
            "operation": "critical_task",
            "command": ctx.command.name if ctx.command else None,
            "guild_id": ctx.guild.id if ctx.guild else None
        })

        # Handle gracefully
        await self.enter_degraded_mode()
```

### Error Metrics & Monitoring

#### Key Metrics to Track

- **Error rate by command/module:** Identify problematic areas
- **Response time degradation:** Performance impact of errors
- **User-facing error frequency:** Impact on user experience
- **Critical system error alerts:** Immediate notification for severe issues

#### Dashboards & Alerts

- **Real-time error tracking** via Sentry with user context
- **Command success/failure rates** to identify reliability issues
- **Infrastructure health monitoring** for database/API availability
- **User experience impact metrics** to prioritize fixes

**Example Error Metrics:**

```python
class ErrorMetrics:
    """Track error patterns for monitoring and alerting."""

    def __init__(self):
        self.errors_by_type = {}
        self.errors_by_command = {}
        self.critical_errors = 0

    def record_error(self, error: Exception, command_name: str = None):
        """Record error for metrics and potential alerting."""
        error_type = type(error).__name__

        # Count by error type
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

        # Count by command
        if command_name:
            self.errors_by_command[command_name] = self.errors_by_command.get(command_name, 0) + 1

        # Alert on critical errors
        if isinstance(error, (TuxDatabaseConnectionError, TuxConfigurationError)):
            self.critical_errors += 1
            if self.critical_errors > 5:  # Threshold for alerting
                logger.critical(f"High critical error rate: {self.critical_errors} errors")
                # Send alert to monitoring system
```

## Migration & Best Practices

### When to Use Global vs Local Error Handling

- **Global Handler (recommended for user errors):**
  - Command validation errors
  - Permission checks
  - Input validation failures
  - Rate limiting
  - Command not found

- **Local Handler (recommended for infrastructure):**
  - HTTP API calls
  - Database operations
  - File I/O operations
  - External service calls
  - Background task failures

### Migrating Existing Code

**Before:**

```python
# Old code with poor error handling
async def old_function(self, user_id):
    data = await self.api.get_user(user_id)  # No error handling
    return data
```

**After:**

```python
# New code with proper error handling
async def new_function(self, user_id: int) -> dict | None:
    try:
        response = await http_client.get(f"https://api.example.com/users/{user_id}")
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"User {user_id} not found")
            return None
        raise TuxAPIRequestError("user_api", e.response.status_code, e.response.reason_phrase) from e
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch user {user_id}", error=str(e))
        raise TuxAPIConnectionError("user_api", e) from e
```

**Sentry Context Functions:**

```python
from tux.services.sentry import set_command_context, set_user_context, set_tag

# Set command context (automatically done by error handler)
set_command_context(ctx)

# Set user context
set_user_context(ctx.author)

# Add custom tags
set_tag("operation", "user_import")
set_tag("batch_size", 1000)
```

### Error Metrics

```python
class ErrorMetrics:
    """Track error patterns for monitoring."""

    def __init__(self):
        self.errors_by_type = {}
        self.errors_by_endpoint = {}

    def record_error(self, error: Exception, endpoint: str = None):
        """Record error for metrics."""
        error_type = type(error).__name__

        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

        if endpoint:
            self.errors_by_endpoint[endpoint] = self.errors_by_endpoint.get(endpoint, 0) + 1

# Usage in error handler
metrics = ErrorMetrics()

async def handle_command_error(self, ctx, error):
    metrics.record_error(error, ctx.command.name if ctx.command else None)
    # Continue with normal error handling...
```

## Resources

- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
