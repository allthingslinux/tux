---
title: Debugging Best Practices
description: Debugging best practices for Tux development, including logging, interactive debugging, testing, and common debugging scenarios.
tags:
  - developer-guide
  - best-practices
  - debugging
---

# Debugging Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Development Setup

### Debug Mode

Enable debug mode for enhanced logging and error information:

```bash
# Start bot with debug mode
uv run tux start --debug

# Or set in environment
export DEBUG=1
uv run tux start
```

Debug mode provides:

- **Detailed logging** at DEBUG level and above
- **Full stack traces** in error messages
- **Verbose SQL queries** and database operations
- **HTTP request/response details** from external APIs

### Development Environment

Set up your development environment with debugging tools:

```bash
# Install development dependencies
uv sync --dev

# Enable debug logging in .env
DEBUG=1
LOG_LEVEL=DEBUG

# Run tests with verbose output
uv run test unit --verbose
```

## Logging for Debugging

### Log Levels in Development

```python
from loguru import logger

# Use appropriate levels for different debugging scenarios
logger.trace("Very detailed execution flow", var1=value1)
logger.debug("Internal state information", user_id=123, cache_hit=True)
logger.info("Normal operations", command="ban", target_user=456)
logger.warning("Potential issues", rate_limit_remaining=2)
logger.error("Errors with context", error=str(e), user_id=123)
logger.critical("System failures", database_status="disconnected")
```

### Structured Debugging Logs

```python
from tux.core.logging import StructuredLogger

# Log performance with context
StructuredLogger.performance(
    "database_query",
    duration=0.045,
    query="SELECT * FROM users WHERE id = ?",
    user_count=150
)

# Log API calls with timing
StructuredLogger.api_call(
    "GET",
    "https://api.github.com/user/123",
    status=200,
    duration=0.234,
    rate_limit_remaining=4999
)
```

### Conditional Debug Logging

```python
# Only log expensive operations in debug mode
if logger.level("DEBUG").no <= logger.level:
    expensive_debug_data = analyze_large_dataset(data)
    logger.debug("Dataset analysis complete", analysis=expensive_debug_data)
```

## Interactive Debugging

### Python Debugger (pdb)

```python
import pdb

def problematic_function(user_id: int):
    # Set breakpoint
    pdb.set_trace()

    user = get_user(user_id)
    # Execution pauses here for inspection

    return process_user(user)

# Or use breakpoint() in Python 3.7+
def problematic_function(user_id: int):
    user = get_user(user_id)
    breakpoint()  # Equivalent to pdb.set_trace()
    return process_user(user)
```

### Post-Mortem Debugging

```python
import pdb
import traceback

try:
    risky_operation()
except Exception as e:
    # Start debugger at point of exception
    pdb.post_mortem()
    # or
    traceback.print_exc()
    pdb.set_trace()
```

### Remote Debugging

For debugging running applications:

```python
# Add remote debugging capability
import rpdb

def debug_function():
    # Set remote breakpoint
    rpdb.set_trace()

    # Code to debug remotely
    result = complex_calculation()
    return result

# Connect with: nc 127.0.0.1 4444
```

## Testing & Debugging Tests

### Debug Test Failures

```bash
# Run specific test with debugging
uv run pytest tests/database/test_database_model_creation.py::TestModelCreation::test_guild_model_creation -xvs

# Debug with pdb on failure
uv run pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalIPythonApp

# Run tests with coverage and debug info
uv run test unit --verbose --cov-report=html
```

### Test Debugging Techniques

```python
def test_user_creation():
    """Debug test failures with detailed assertions."""
    user_data = {"name": "test", "email": "test@example.com"}

    # Use pytest's breakpoint
    breakpoint()

    result = create_user(user_data)

    # Add debug prints for complex assertions
    print(f"Created user: {result}")
    print(f"User dict: {result.__dict__ if hasattr(result, '__dict__') else result}")

    assert result.name == "test"
    assert result.email == "test@example.com"
```

### Mock Debugging

```python
from unittest.mock import patch, MagicMock

def test_api_call_with_debug():
    """Debug mocked API calls."""

    with patch('httpx.AsyncClient.get') as mock_get:
        # Create detailed mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user": "test"}
        mock_get.return_value = mock_response

        # Add breakpoint to inspect mock
        breakpoint()

        result = call_external_api()

        assert result["user"] == "test"
```

## Common Debugging Scenarios

### Database Issues

```python
# Debug SQL queries
from sqlalchemy import text
from tux.core.logging import logger

async def debug_query():
    """Debug database queries with detailed logging."""
    logger.debug("About to execute query")

    # Enable SQL echo for this session
    async with db.session() as session:
        # Log the actual SQL
        result = await session.execute(
            text("SELECT * FROM users WHERE active = :active"),
            {"active": True}
        )

        users = result.fetchall()
        logger.debug(f"Query returned {len(users)} users", user_ids=[u.id for u in users])

        return users
```

### Async Debugging

```python
import asyncio

async def debug_async_flow():
    """Debug async task execution."""

    # Log task creation
    logger.debug("Creating async tasks")

    tasks = [
        asyncio.create_task(process_user(user_id))
        for user_id in user_ids
    ]

    # Debug task states
    for i, task in enumerate(tasks):
        logger.debug(f"Task {i} state: {task._state}")

    # Wait with timeout for debugging
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=30.0
        )

        # Debug results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed", error=str(result))
            else:
                logger.debug(f"Task {i} succeeded", result=result)

    except asyncio.TimeoutError:
        logger.error("Async tasks timed out")
        # Debug hanging tasks
        for i, task in enumerate(tasks):
            if not task.done():
                logger.error(f"Task {i} is still running", task_info=str(task))
```

### Discord API Issues

```python
# Debug Discord API interactions
@commands.hybrid_command(name="debug_user")
async def debug_user_command(self, ctx: commands.Context[Tux], user: discord.User):
    """Debug command for user-related issues."""

    logger.info("Debugging user command",
                user_id=user.id,
                user_name=user.name,
                guild_id=ctx.guild.id if ctx.guild else None)

    # Debug permissions
    if ctx.guild:
        permissions = ctx.channel.permissions_for(user)
        logger.debug("User permissions", **{
            k: v for k, v in permissions if v  # Only log True permissions
        })

    # Debug member info
    if isinstance(user, discord.Member):
        logger.debug("Member info",
                    joined_at=user.joined_at,
                    roles=[role.name for role in user.roles],
                    status=user.status)

    await ctx.send(f"Debug info logged for user {user.mention}")
```

## Performance Debugging

### Memory Usage

```python
import psutil
import os

def debug_memory_usage():
    """Debug memory usage of current process."""
    process = psutil.Process(os.getpid())

    memory_info = process.memory_info()
    memory_percent = process.memory_percent()

    logger.debug("Memory usage",
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=memory_percent)

    # Log top memory consumers if available
    if hasattr(process, 'memory_maps'):
        maps = process.memory_maps()
        large_maps = sorted(maps, key=lambda m: m.rss, reverse=True)[:5]

        for mem_map in large_maps:
            logger.debug("Large memory region",
                        path=mem_map.path or 'anonymous',
                        rss_mb=mem_map.rss / 1024 / 1024)
```

### Profiling Code

```python
import cProfile
import pstats
from io import StringIO

def profile_function(func):
    """Decorator to profile function execution."""
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        try:
            return func(*args, **kwargs)
        finally:
            pr.disable()
            s = StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats(10)  # Top 10 functions

            logger.debug("Profile results", profile_output=s.getvalue())

    return wrapper

# Usage
@profile_function
def slow_function():
    # Code to profile
    pass
```

### Async Performance

```python
import asyncio
import time

async def debug_async_performance():
    """Debug async operation performance."""

    start_time = time.perf_counter()

    # Run multiple operations
    tasks = [asyncio.create_task(operation(i)) for i in range(10)]
    results = await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start_time

    logger.debug("Async performance",
                total_time=total_time,
                avg_time_per_task=total_time / len(tasks),
                tasks_completed=len(results))

    return results
```

## Docker Debugging

### Debug Container Issues

```bash
# View container logs
docker compose logs

# Execute commands in running container
docker exec -it tux /bin/bash

# Debug with full environment
docker run --rm -it --entrypoint /bin/bash tux:latest

# View container resource usage
docker stats tux
```

### Debug Database in Docker

```bash
# Connect to database container
docker exec -it tux-postgres psql -U tux -d tux

# View database logs
docker logs tux-postgres

# Debug slow queries
docker exec tux-postgres psql -U tux -d tux -c "SELECT * FROM pg_stat_activity;"
```

### Network Debugging

```bash
# Test connectivity between containers
docker exec tux ping tux-postgres

# Debug network issues
docker network ls
docker network inspect tux_network

# Test external API calls
docker exec tux curl -v https://api.github.com/user
```

## Hot Reload Debugging

### Debug Hot Reload Issues

```python
# Enable hot reload debugging
from tux.services.hot_reload import HotReloadService

# Log hot reload events
logger.debug("Hot reload triggered", files_changed=changed_files)

# Debug module reloading
try:
    await hot_reload.reload_module(module_name)
    logger.info("Module reloaded successfully", module=module_name)
except Exception as e:
    logger.error("Module reload failed", module=module_name, error=str(e))
    # Continue with old module
```

### File Watching Issues

```python
# Debug file watcher
from watchdog.events import FileSystemEventHandler

class DebugFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        logger.debug("File modified",
                    path=event.src_path,
                    is_directory=event.is_directory)

    def on_created(self, event):
        logger.debug("File created", path=event.src_path)

    def on_deleted(self, event):
        logger.debug("File deleted", path=event.src_path)
```

## Discord-Specific Debugging

### Command Debugging

```python
@commands.hybrid_command(name="debug_command")
async def debug_command(self, ctx: commands.Context[Tux]):
    """Debug command execution context."""

    # Log command context
    logger.debug("Command execution context",
                command=ctx.command.name if ctx.command else None,
                author_id=ctx.author.id,
                channel_id=ctx.channel.id,
                guild_id=ctx.guild.id if ctx.guild else None,
                message_content=ctx.message.content if ctx.message else None)

    # Debug permissions
    if ctx.guild:
        bot_permissions = ctx.channel.permissions_for(ctx.guild.me)
        user_permissions = ctx.channel.permissions_for(ctx.author)

        logger.debug("Bot permissions", **{
            perm: value for perm, value in bot_permissions
            if not value  # Log missing permissions
        })

    await ctx.send("Debug information logged. Check logs for details.")
```

### Event Debugging

```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    """Debug message processing."""

    # Skip bot messages
    if message.author.bot:
        return

    logger.debug("Message received",
                message_id=message.id,
                author_id=message.author.id,
                channel_id=message.channel.id,
                content_length=len(message.content),
                has_attachments=bool(message.attachments),
                has_embeds=bool(message.embeds))

    # Process message...
```

### Rate Limit Debugging

```python
# Debug Discord rate limits
@commands.Cog.listener()
async def on_command_error(self, ctx: commands.Context[Tux], error):
    """Debug command errors including rate limits."""

    if isinstance(error, commands.CommandOnCooldown):
        logger.warning("Rate limit hit",
                      command=ctx.command.name,
                      user_id=ctx.author.id,
                      retry_after=error.retry_after,
                      cooldown_type=type(error).__name__)

    elif isinstance(error, commands.CommandInvokeError):
        # Check for Discord API errors
        if hasattr(error.original, 'status'):
            logger.error("Discord API error",
                        status=error.original.status,
                        command=ctx.command.name,
                        error=str(error.original))
        else:
            logger.error("Command invoke error",
                        command=ctx.command.name,
                        error=str(error))
```

## Development Commands

Tux includes development commands for debugging:

```bash
# Reload cogs without restarting
/dev reload ping

# Load/unload specific modules
/dev load utility
/dev unload moderation

# Sync application commands
/dev sync_tree

# Stop bot gracefully
/dev stop
```

## Debugging Checklist

### Before Starting Debug Session

- [ ] Enable debug logging (`LOG_LEVEL=DEBUG`)
- [ ] Clear old logs to reduce noise
- [ ] Identify the specific issue/symptom
- [ ] Gather relevant context (user ID, command, environment)

### During Debugging

- [ ] Add strategic log statements with context
- [ ] Use breakpoints for complex logic
- [ ] Test assumptions with small, focused changes
- [ ] Check environment variables and configuration
- [ ] Verify database state and connections

### After Debugging

- [ ] Remove debug logging statements
- [ ] Clean up breakpoints and debug code
- [ ] Document the fix and root cause
- [ ] Add regression tests if applicable

## Resources

- [Python Debugging Documentation](https://docs.python.org/3/library/pdb.html)
- [Loguru Documentation](https://loguru.readthedocs.io/)
- [pytest Debugging](https://docs.pytest.org/en/stable/how-to/failures.html)
- [Discord.py Logging](https://discordpy.readthedocs.io/en/stable/logging.html)
- [AsyncIO Debugging](https://docs.python.org/3/library/asyncio-dev.html)
