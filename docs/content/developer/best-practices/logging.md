---
title: Logging Best Practices
description: Logging best practices for Tux development using loguru, including structured logging, third-party library interception, and debugging patterns.
---

## Loguru Configuration

Tux uses loguru for all logging, configured in `src/tux/core/logging.py`. The setup provides:

- **Single global logger**: Centralized configuration for the entire application
- **Environment-based levels**: Configurable via `.env` file or explicit overrides
- **Third-party interception**: Routes all library logs through loguru
- **IDE-clickable paths**: Shows `src/tux/...` paths for easy navigation

### Basic Setup

```python
from loguru import logger

# Logger is pre-configured - just import and use
logger.info("Bot started successfully")
logger.debug("Processing user request", user_id=12345)
logger.warning("Rate limit approaching", remaining=5)
logger.error("Database connection failed", error=str(e))
```

### Configuration Priority

Log levels are determined in this order (highest to lowest priority):

1. **Explicit parameter**: `configure_logging(level="DEBUG")`
2. **Environment variable**: `LOG_LEVEL=DEBUG` in `.env`
3. **Debug flag**: `DEBUG=1` in `.env` sets DEBUG level
4. **Default**: `INFO` level

## Log Levels

### TRACE

**When to use:** Very detailed debugging, function entry/exit, variable dumps

```python
logger.trace("Function entered", arg1=value1, arg2=value2)
```

### DEBUG

**When to use:** Development debugging, SQL queries, API calls, internal state

```python
logger.debug("Database query executed", query=sql, duration=0.045)
logger.debug("Cache miss, fetching from database", key=cache_key)
```

### INFO

**When to use:** Normal operations, startup/shutdown, user actions, important state changes

```python
logger.info("Bot connected to Discord")
logger.info(f"User {user_id} executed command '{command}'")
logger.info("Database migration completed", version="abc123")
```

### SUCCESS

**When to use:** Successful operations, achievements, positive outcomes

```python
logger.success("All tests passed")
logger.success("User registration completed", user_id=new_user.id)
```

### WARNING

**When to use:** Potential issues, degraded performance, recoverable errors

```python
logger.warning("Rate limit hit, using cached data", guild_id=guild.id)
logger.warning("API call failed, retrying", attempt=2, error=str(e))
```

### ERROR

**When to use:** Application errors, failed operations, data corruption

```python
logger.error("Database connection lost", error=str(e))
logger.error("Command execution failed", command=ctx.command.name, error=str(e))
```

### CRITICAL

**When to use:** System failures, unrecoverable errors, security issues

```python
logger.critical("Database corruption detected", table="users")
logger.critical("Sentry integration failed, error reporting disabled")
```

## Structured Logging

Tux provides `StructuredLogger` helpers for consistent, queryable logs:

### Performance Logging

```python
from tux.core.logging import StructuredLogger

# Log operation performance with context
StructuredLogger.performance(
    "database_query",
    duration=0.123,
    operation="user_lookup",
    user_id=user.id
)
```

### Database Logging

```python
# Log database queries with metadata
StructuredLogger.database(
    "SELECT * FROM users WHERE id = ?",
    duration=0.045,
    rows_returned=1,
    table="users"
)
```

### API Call Logging

```python
# Log external API interactions
StructuredLogger.api_call(
    "GET",
    "https://api.github.com/user",
    status=200,
    duration=0.234,
    user_agent="Tux/1.0"
)
```

## Third-Party Library Interception

Tux automatically intercepts logs from these libraries:

| Library | Purpose | Log Level |
|---------|---------|-----------|
| `discord.*` | Discord.py client logs | INFO |
| `sqlalchemy.*` | Database ORM | DEBUG (queries)/WARNING (internals) |
| `httpx` | HTTP client | WARNING |
| `asyncio` | Async operations | INFO |
| `sentry_sdk` | Error reporting | INFO |
| `watchdog` | File watching | WARNING |

### Custom Interception

To intercept additional libraries, add them to `INTERCEPTED_LIBRARIES`:

```python
# In src/tux/core/logging.py
INTERCEPTED_LIBRARIES = [
    # ... existing libraries ...
    "new_library",
    "another.library.submodule",
]
```

## Logging Patterns

### Command Execution

```python
@commands.hybrid_command(name="ban")
async def ban_user(self, ctx: commands.Context[Tux], user: discord.User, reason: str):
    logger.info(f"User {ctx.author.id} executing ban command",
                target_user=user.id, guild=ctx.guild.id)

    try:
        # Ban logic here
        await ctx.guild.ban(user, reason=reason)
        logger.success(f"Successfully banned user {user.id}",
                      moderator=ctx.author.id, reason=reason)
    except discord.Forbidden:
        logger.warning(f"Insufficient permissions to ban user {user.id}",
                      moderator=ctx.author.id)
    except Exception as e:
        logger.error(f"Failed to ban user {user.id}: {e}",
                    moderator=ctx.author.id, exc_info=True)
```

### Database Query Logging

```python
async def get_user(self, user_id: int) -> User | None:
    logger.debug("Fetching user from database", user_id=user_id)

    try:
        user = await self.db.get_user(user_id)
        if user:
            logger.debug("User found in database", user_id=user_id)
        else:
            logger.debug("User not found in database", user_id=user_id)
        return user
    except Exception as e:
        logger.error(f"Database error fetching user {user_id}: {e}",
                    user_id=user_id, exc_info=True)
        return None
```

### API Calls

```python
async def fetch_github_user(self, username: str) -> dict | None:
    logger.debug("Fetching GitHub user", username=username)

    try:
        async with self.session.get(f"https://api.github.com/users/{username}") as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.debug("GitHub user fetched successfully",
                           username=username, user_id=data.get("id"))
                return data
            else:
                logger.warning(f"GitHub API returned {resp.status}",
                             username=username, status=resp.status)
                return None
    except Exception as e:
        logger.error(f"Failed to fetch GitHub user {username}: {e}",
                    username=username, exc_info=True)
        return None
```

## Error Handling & Exceptions

### Exception Logging

```python
try:
    result = await risky_operation()
    logger.info("Operation completed successfully")
except SpecificError as e:
    logger.warning(f"Specific error occurred: {e}")
    # Handle specific error
except Exception as e:
    logger.error(f"Unexpected error in operation: {e}", exc_info=True)
    # Handle general error
```

### Context Managers

```python
import contextlib

@contextlib.contextmanager
def log_operation(operation_name: str):
    logger.debug(f"Starting {operation_name}")
    try:
        yield
        logger.debug(f"Completed {operation_name}")
    except Exception as e:
        logger.error(f"Failed {operation_name}: {e}", exc_info=True)
        raise

# Usage
with log_operation("user_registration"):
    await register_user(user_data)
```

## Debugging Techniques

### Conditional Logging

```python
# Log only in debug mode
if logger.level("DEBUG").no <= logger.level:
    logger.debug("Detailed debug info", complex_data=expensive_computation())
```

### Log Levels in Development

```bash
# Run with debug logging
uv run tux start --debug

# Or set in .env
LOG_LEVEL=DEBUG
```

### Log Filtering

```python
# Log only errors from specific module
logger.disable("tux.modules.utility")
logger.enable("tux.modules.utility.ping")  # Enable specific submodule
```

## Performance Considerations

### Avoid Expensive Operations in Logs

```python
# Bad: Expensive computation in log
logger.debug("Processing data", data=expensive_format(large_dataset))

# Good: Lazy evaluation
logger.debug("Processing data", data_size=len(large_dataset))
if logger.level("DEBUG").no <= logger.level:
    logger.debug("Raw data", data=expensive_format(large_dataset))
```

### Log Rotation

Logs are automatically managed by loguru. For file logging in production:

```python
# Add file handler with rotation
logger.add(
    "logs/tux_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)
```

## Testing with Logging

### Testing Log Output

```python
import pytest
from loguru import logger

def test_user_creation(caplog):
    """Test that user creation logs appropriate messages."""
    with caplog.at_level(logging.INFO):
        create_user("test@example.com")

    assert "User created successfully" in caplog.text
    assert "test@example.com" in caplog.text
```

### Mocking Loguru in Tests

```python
from unittest.mock import patch

def test_error_handling():
    """Test error handling without actual logging."""
    with patch('tux.core.logging.logger') as mock_logger:
        # Test code that should log errors
        trigger_error()

        mock_logger.error.assert_called_once()
        mock_logger.warning.assert_not_called()
```

## Common Anti-Patterns

### ❌ Don't Log Sensitive Data

```python
# Bad: Logs passwords, tokens, PII
logger.info("User login", email=user.email, password=user.password)

# Good: Log without sensitive data
logger.info("User login attempt", user_id=user.id, ip_address=request.ip)
```

### ❌ Don't Use Print Statements

```python
# Bad: Mixes print with logging
print("Debug: processing user")
logger.info("User processed")

# Good: Use consistent logging
logger.debug("Processing user", user_id=user.id)
logger.info("User processed successfully")
```

### ❌ Don't Log in Loops Without Care

```python
# Bad: Can flood logs
for user in users:
    logger.info(f"Processing user {user.id}")  # Thousands of logs

# Good: Log summary or sample
logger.info(f"Processing {len(users)} users")
if len(users) <= 10:
    for user in users:
        logger.debug(f"Processing user {user.id}")
```

### ❌ Don't Log Exceptions Without Context

```python
# Bad: Missing context
try:
    await api_call()
except Exception as e:
    logger.error(str(e))

# Good: Include relevant context
try:
    await api_call(user_id=user.id)
except Exception as e:
    logger.error(f"API call failed for user {user.id}: {e}",
                user_id=user.id, endpoint="/api/user", exc_info=True)
```

## Configuration Examples

### Development Setup

```bash
# .env
LOG_LEVEL=DEBUG
DEBUG=1
```

### Production Setup

```bash
# .env
LOG_LEVEL=INFO
DEBUG=0
```

### Testing Override

```python
from tux.core.logging import configure_testing_logging

# In test setup
configure_testing_logging()  # Sets DEBUG level for tests
```

## Resources

- [Loguru Documentation](https://loguru.readthedocs.io/)
- [Structured Logging](https://www.structlog.org/)
- [Twelve-Factor App Logging](https://12factor.net/logs)
- [Tux Logging Source](../concepts/core/logging.md)
