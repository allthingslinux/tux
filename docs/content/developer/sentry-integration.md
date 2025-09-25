# Sentry Integration Guide

## Overview

This document covers Sentry integration for error tracking, performance monitoring, and debugging in
the Tux Discord bot. Our Sentry setup provides comprehensive error tracking with rich context for
effective debugging and monitoring.

## Architecture

### Core Components

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │───▶│  SentryManager   │───▶│   Sentry SDK    │
│   (Commands,    │    │  (Centralized    │    │   (Events &     │
│    Services)    │    │   Interface)     │    │   Monitoring)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Context &       │    │   Sentry.io     │
                       │  Utilities       │    │   Dashboard     │
                       └──────────────────┘    └─────────────────┘
```text

### Key Files

- `src/tux/services/sentry/config.py` - Sentry SDK configuration and setup
- `src/tux/services/sentry/utils.py` - Specialized error capture utilities
- `src/tux/services/sentry/context.py` - Context management for events
- `src/tux/services/sentry/monitoring.py` - Performance monitoring
- `src/tux/services/sentry/__init__.py` - SentryManager class

## Configuration

### Environment Setup

```bash
# Required
SENTRY_DSN=https://your-dsn@sentry.io/project-id

# Optional
SENTRY_ENVIRONMENT=production  # or development
SENTRY_RELEASE=v1.0.0
```text

### Initialization

```python
from tux.services.sentry import SentryManager

# Initialize Sentry (done automatically in bot startup)
sentry_manager = SentryManager()
sentry_manager.setup()

# Check if initialized
if sentry_manager.is_initialized:
    logger.info("Sentry is ready")
```text

## Error Capture Patterns

### Basic Exception Capture

```python
from tux.services.sentry import capture_exception_safe

try:
    risky_operation()
except Exception as e:
    # Safe capture with automatic context
    capture_exception_safe(e, extra_context={"operation": "user_update"})
    raise  # Re-raise for normal error handling
```text

### Specialized Error Capture

#### Database Errors

```python
from tux.services.sentry import capture_database_error

try:
    await db.user.create(**user_data)
except Exception as e:
    capture_database_error(
        e,
        operation="create",
        table="users",
        query="INSERT INTO users..."  # Optional
    )
    raise
```text

#### API Errors

```python
from tux.services.sentry import capture_api_error

try:
    response = await http_client.get("https://api.example.com/users")
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    capture_api_error(
        e,
        endpoint="https://api.example.com/users",
        status_code=e.response.status_code,
        response_data=e.response.json() if e.response else None
    )
    raise
```text

#### Cog Errors

```python
from tux.services.sentry import capture_cog_error

try:
    await self.bot.load_extension("tux.modules.admin")
except Exception as e:
    capture_cog_error(
        e,
        cog_name="admin",
        command_name="reload"  # Optional
    )
    raise
```text

#### Tux-Specific Errors

```python
from tux.services.sentry import capture_tux_exception
from tux.shared.exceptions import TuxConfigurationError

try:
    config = load_required_config()
except TuxConfigurationError as e:
    capture_tux_exception(
        e,
        command_name="setup",
        user_id=str(ctx.author.id),
        guild_id=str(ctx.guild.id)
    )
    raise
```text

## Context Management

### User Context

```python
from tux.services.sentry import SentryManager

sentry = SentryManager()

# Set user context for all subsequent events
sentry.set_user_context(ctx.author)

# Or use in command context
sentry.set_command_context(ctx)
```text

### Custom Context

```python
# Add custom context data
sentry.set_context("database", {
    "connection_pool_size": 10,
    "active_connections": 7,
    "query_count": 1234
})

# Add tags for filtering
sentry.set_tag("feature", "moderation")
sentry.set_tag("guild_size", "large")
```text

### Breadcrumbs

```python
# Track user actions leading to errors
sentry.add_breadcrumb(
    message="User started command execution",
    category="command",
    level="info",
    data={"command": "ban", "target_user": "123456789"}
)

sentry.add_breadcrumb(
    message="Permission check passed",
    category="security",
    level="info"
)

sentry.add_breadcrumb(
    message="Database query executed",
    category="database",
    level="debug",
    data={"table": "cases", "operation": "insert"}
)
```text

## Performance Monitoring

### Transaction Tracking

```python
# Start a transaction for command execution
with sentry.start_transaction(op="command", name="ban_user") as transaction:
    # Command logic here
    await ban_user_logic()
    
    # Add transaction data
    transaction.set_data("user_count", len(users))
    transaction.set_tag("command_type", "moderation")
```text

### Span Tracking

```python
# Track specific operations within a transaction
with sentry.start_span(op="database", description="fetch_user_cases") as span:
    cases = await db.case.find_all(filters=Case.user_id == user_id)
    span.set_data("case_count", len(cases))

with sentry.start_span(op="discord_api", description="send_dm") as span:
    await user.send("You have been banned")
    span.set_tag("message_type", "dm")
```text

### Command Performance

```python
@commands.command()
async def my_command(self, ctx: commands.Context[Tux]) -> None:
    # Track command start
    sentry.track_command_start("my_command")
    
    try:
        # Command logic
        result = await process_command()
        
        # Track successful completion
        sentry.track_command_end("my_command", success=True)
        
    except Exception as e:
        # Track failed completion
        sentry.track_command_end("my_command", success=False, error=e)
        raise
```text

## Integration Patterns

### Command Error Handling

```python
from tux.services.sentry import SentryManager, capture_exception_safe

class MyCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.sentry = SentryManager()
    
    @commands.command()
    async def risky_command(self, ctx: commands.Context[Tux]) -> None:
        # Set context for this command execution
        self.sentry.set_user_context(ctx.author)
        self.sentry.set_command_context(ctx)
        
        try:
            result = await self.perform_operation()
            await ctx.send(f"Success: {result}")
            
        except ValueError as e:
            # User error - don't send to Sentry
            await ctx.send(f"Invalid input: {e}")
            
        except Exception as e:
            # System error - capture in Sentry
            capture_exception_safe(
                e,
                extra_context={
                    "command": "risky_command",
                    "guild_id": ctx.guild.id if ctx.guild else None,
                    "channel_id": ctx.channel.id
                }
            )
            await ctx.send("An unexpected error occurred.")
            raise  # Let global error handler manage user feedback
```text

### Service Initialization

```python
class MyService:
    def __init__(self):
        self.sentry = SentryManager()
        
    async def initialize(self) -> None:
        try:
            await self._setup_connections()
            await self._load_configuration()
            
            self.sentry.add_breadcrumb(
                message="Service initialized successfully",
                category="service",
                level="info"
            )
            
        except Exception as e:
            capture_exception_safe(
                e,
                extra_context={
                    "service": self.__class__.__name__,
                    "initialization_step": "setup"
                }
            )
            raise
```text

### Background Tasks

```python
async def background_cleanup_task():
    """Background task with Sentry monitoring."""
    sentry = SentryManager()
    
    with sentry.start_transaction(op="task", name="cleanup") as transaction:
        try:
            sentry.add_breadcrumb(
                message="Starting cleanup task",
                category="task"
            )
            
            # Cleanup logic
            deleted_count = await cleanup_old_records()
            
            transaction.set_data("deleted_records", deleted_count)
            sentry.add_breadcrumb(
                message=f"Cleanup completed: {deleted_count} records",
                category="task",
                level="info"
            )
            
        except Exception as e:
            capture_exception_safe(
                e,
                extra_context={"task": "cleanup"}
            )
            transaction.set_status("internal_error")
            raise
```text

## Event Filtering & Sampling

### Custom Filtering

```python
# In config.py - before_send handler
def before_send(event, hint):
    """Filter events before sending to Sentry."""
    
    # Don't send user input validation errors
    if event.get('exception'):
        exc_type = event['exception']['values'][0]['type']
        if exc_type in ['ValidationError', 'commands.BadArgument']:
            return None
    
    # Don't send rate limit errors
    if 'rate limit' in str(event.get('message', '')).lower():
        return None
    
    return event
```text

### Sampling Configuration

```python
def traces_sampler(sampling_context):
    """Custom sampling for performance monitoring."""
    
    # Sample all error transactions
    if sampling_context.get("transaction_context", {}).get("name") == "error":
        return 1.0
    
    # Sample 10% of command transactions
    if sampling_context.get("transaction_context", {}).get("op") == "command":
        return 0.1
    
    # Sample 1% of background tasks
    if sampling_context.get("transaction_context", {}).get("op") == "task":
        return 0.01
    
    return 0.1  # Default 10% sampling
```text

## Testing with Sentry

### Unit Tests

```python
import pytest
from unittest.mock import patch
from tux.services.sentry import capture_exception_safe

def test_error_capture():
    """Test that errors are properly captured."""
    with patch('sentry_sdk.capture_exception') as mock_capture:
        try:
            raise ValueError("Test error")
        except Exception as e:
            capture_exception_safe(e, extra_context={"test": True})
        
        mock_capture.assert_called_once()

@pytest.fixture
def mock_sentry():
    """Mock Sentry for testing."""
    with patch('tux.services.sentry.is_initialized', return_value=True):
        with patch('sentry_sdk.capture_exception') as mock_capture:
            yield mock_capture
```text

### Integration Tests

```python
async def test_command_with_sentry(mock_sentry):
    """Test command execution with Sentry integration."""
    # Simulate command that raises an error
    with pytest.raises(Exception):
        await cog.problematic_command(ctx)
    
    # Verify Sentry was called
    mock_sentry.assert_called()
    
    # Verify context was set correctly
    call_args = mock_sentry.call_args
    assert "command" in str(call_args)
```text

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Error Rate**: Errors per minute/hour
2. **Command Performance**: Average execution time
3. **Database Performance**: Query execution time
4. **API Response Times**: External service latency
5. **User Experience**: Failed command rate

### Alert Configuration

```python
# Example alert rules (configured in Sentry dashboard)

# High error rate alert
if error_rate > 10 per minute:
    notify_team()

# Slow command alert  
if command_duration > 5 seconds:
    notify_developers()

# Database connection issues
if database_errors > 5 per minute:
    notify_infrastructure_team()
```text

### Dashboard Setup

**Recommended Sentry Dashboard Widgets:**

- Error frequency by command
- Performance by operation type
- User impact (affected users)
- Release health (error rate by version)
- Custom tags (guild size, feature usage)

## Best Practices

### ✅ DO

```python
# Capture with context
capture_exception_safe(e, extra_context={"user_id": user.id})

# Use specific capture functions
capture_database_error(e, operation="insert", table="users")

# Add breadcrumbs for debugging
sentry.add_breadcrumb("User clicked button", category="ui")

# Set user context for commands
sentry.set_user_context(ctx.author)

# Use transactions for performance monitoring
with sentry.start_transaction(op="command", name="ban"):
    # Command logic
```text

### ❌ DON'T

```python
# Don't capture user errors
try:
    validate_user_input(data)
except ValidationError as e:
    sentry_sdk.capture_exception(e)  # DON'T - this is user error

# Don't use raw Sentry SDK
sentry_sdk.capture_exception(e)  # Use capture_exception_safe instead

# Don't capture without context
capture_exception_safe(e)  # Missing context makes debugging hard

# Don't capture in tight loops
for item in large_list:
    try:
        process(item)
    except Exception as e:
        capture_exception_safe(e)  # Will spam Sentry
```text

## Troubleshooting

### Common Issues

#### Sentry Not Initialized

```python
# Check initialization status
if not sentry.is_initialized:
    logger.warning("Sentry not initialized - check SENTRY_DSN")
    return
```text

#### Too Many Events

```python
# Implement rate limiting
from functools import lru_cache
from time import time

@lru_cache(maxsize=100)
def should_capture_error(error_type: str, timestamp_minute: int) -> bool:
    """Rate limit error capture to prevent spam."""
    return True  # Implement your rate limiting logic

# Usage
if should_capture_error(type(e).__name__, int(time() // 60)):
    capture_exception_safe(e)
```text

#### Missing Context

```python
# Always provide context for debugging
capture_exception_safe(
    e,
    extra_context={
        "operation": "user_ban",
        "user_id": user_id,
        "guild_id": guild_id,
        "moderator_id": moderator_id,
        "reason": ban_reason
    }
)
```text

### Debug Mode

```python
# Enable Sentry debug mode in development
sentry_sdk.init(
    dsn=dsn,
    debug=True,  # Enables verbose logging
    # ... other config
)
```text

## Performance Considerations

### Event Volume Management

1. **Filter user errors** - Don't send validation errors
2. **Sample performance data** - Use sampling for high-volume operations
3. **Rate limit captures** - Prevent spam from repeated errors
4. **Use breadcrumbs wisely** - Don't add too many per event

### Memory Usage

```python
# Limit breadcrumb count
sentry_sdk.init(
    max_breadcrumbs=50,  # Default is 100
    # ... other config
)

# Clear context when done
with sentry_sdk.push_scope():
    # Temporary context
    pass  # Context automatically cleared
```text

## Security Considerations

### PII Handling

```python
# Configure to not send PII
sentry_sdk.init(
    send_default_pii=False,  # Don't send user data automatically
    # ... other config
)

# Sanitize sensitive data
def sanitize_user_data(data):
    """Remove sensitive information before sending to Sentry."""
    sanitized = data.copy()
    sanitized.pop('password', None)
    sanitized.pop('token', None)
    return sanitized

capture_exception_safe(e, extra_context=sanitize_user_data(user_data))
```text

### Data Retention

- Configure appropriate data retention in Sentry dashboard
- Regularly review and clean up old events
- Use Sentry's data scrubbing rules for sensitive data

---

## Quick Reference

### Common Capture Patterns

```python
# Basic error capture
capture_exception_safe(e, extra_context={"operation": "user_update"})

# Database error
capture_database_error(e, operation="insert", table="users")

# API error
capture_api_error(e, endpoint="/api/users", status_code=500)

# Cog error
capture_cog_error(e, cog_name="moderation", command_name="ban")

# Performance monitoring
with sentry.start_transaction(op="command", name="ban_user"):
    # Command logic
```text

### Advanced Context Management

```python
# Set user context
sentry.set_user_context(ctx.author)

# Add breadcrumb
sentry.add_breadcrumb("User action", category="ui", data={"button": "ban"})

# Set custom context
sentry.set_context("database", {"pool_size": 10})

# Add tags
sentry.set_tag("feature", "moderation")
```text

---

*This guide ensures comprehensive error tracking and performance monitoring for the Tux Discord bot.
Follow these patterns for effective debugging and system monitoring.*
