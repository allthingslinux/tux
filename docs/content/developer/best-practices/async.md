---
title: Async Best Practices
description: Async programming best practices for Tux development, including concurrency patterns, Discord.py async considerations, and performance optimization.
---

## Why Async Matters for Discord Bots

Discord bots operate in a highly concurrent environment where thousands of users can interact simultaneously. Traditional synchronous programming would create blocking operations that make the bot unresponsive.

### Key Benefits

- **Non-blocking I/O**: Handle multiple users simultaneously without freezing
- **Scalability**: Support hundreds of concurrent operations
- **Resource Efficiency**: Better CPU and memory utilization
- **Discord API Compliance**: Discord.py requires async for API interactions

### Tux Architecture

Tux uses asyncio throughout its architecture:

- **Database**: Async SQLAlchemy with connection pooling
- **HTTP Client**: Shared httpx.AsyncClient for API calls
- **Discord Interactions**: All bot commands and events are async
- **Background Tasks**: Async task scheduling and monitoring

## Core Async Concepts

### Coroutines and Awaitables

```python
# ✅ Good: Proper async function definition
async def fetch_user_data(user_id: int) -> dict | None:
    """Fetch user data asynchronously."""
    response = await http_client.get(f"/users/{user_id}")
    return response.json()

# ❌ Bad: Mixing sync and async
def sync_function(user_id: int) -> dict | None:  # Blocking!
    response = requests.get(f"/users/{user_id}")  # This blocks!
    return response.json()

# ❌ Bad: Not awaiting async calls
async def broken_function(user_id: int) -> dict | None:
    response = http_client.get(f"/users/{user_id}")  # Forgot await!
    return response.json()  # This returns a coroutine, not data
```

### Event Loop Management

```python
# ✅ Good: Let the framework manage the event loop
# In Tux, discord.py manages the event loop automatically

# ❌ Bad: Creating your own event loop
import asyncio

async def bad_example():
    # Don't do this in a Discord bot!
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # ... bot code ...
```

## Discord.py Async Patterns

### Command Handlers

```python
@commands.hybrid_command(name="userinfo")
async def user_info(self, ctx: commands.Context[Tux], user: discord.User = None):
    """Get information about a user."""
    user = user or ctx.author

    # ✅ Good: Gather multiple async operations concurrently
    embed, avatar_data = await asyncio.gather(
        self.create_user_embed(user),
        self.fetch_user_avatar(user),
    )

    # ✅ Good: Single await for simple operations
    member_info = await self.get_member_info(ctx.guild, user)
    embed.add_field(**member_info)

    await ctx.send(embed=embed)

@commands.hybrid_command(name="mass_ban")
async def mass_ban(self, ctx: commands.Context[Tux], users: str):
    """Ban multiple users by ID."""
    user_ids = [int(uid.strip()) for uid in users.split(",")]

    # ✅ Good: Process in batches to avoid rate limits
    batch_size = 5
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]

        # Ban users in parallel within each batch
        tasks = [ctx.guild.ban(discord.Object(uid)) for uid in batch]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Rate limit protection
        await asyncio.sleep(1)
```

### Event Listeners

```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    """Process incoming messages."""

    # ✅ Good: Early returns for performance
    if message.author.bot:
        return

    # ✅ Good: Concurrent processing when possible
    user_check, content_check = await asyncio.gather(
        self.check_user_permissions(message.author),
        self.analyze_message_content(message.content),
    )

    if not user_check or not content_check:
        return

    # Process the message
    await self.handle_message(message)

@commands.Cog.listener()
async def on_member_join(self, member: discord.Member):
    """Handle new member joins."""

    # ✅ Good: Parallel initialization tasks
    welcome_msg, role_assignment, logging = await asyncio.gather(
        self.send_welcome_message(member),
        self.assign_default_roles(member),
        self.log_member_join(member),
        return_exceptions=True,  # Handle partial failures
    )

    # Check for exceptions in results
    if isinstance(welcome_msg, Exception):
        logger.error(f"Welcome message failed: {welcome_msg}")
    if isinstance(role_assignment, Exception):
        logger.error(f"Role assignment failed: {role_assignment}")
    # Logging failure is less critical, just log it
    if isinstance(logging, Exception):
        logger.warning(f"Join logging failed: {logging}")
```

## Task Management

### Discord.py Tasks Extension

Tux uses `discord.ext.tasks` for background tasks, which provides automatic reconnection logic, exception handling, and scheduling - solving common issues like cancellation, network failures, and sleep limits.

```python
from discord.ext import tasks, commands

class BackgroundService(commands.Cog):
    """Background service using discord.ext.tasks."""

    def __init__(self):
        # Start task automatically
        self.health_monitor.start()

    def cog_unload(self):
        # Clean shutdown
        self.health_monitor.cancel()

    @tasks.loop(minutes=5.0)
    async def health_monitor(self):
        """Monitor system health every 5 minutes."""
        try:
            health_data = await self.check_system_health()
            await self.report_health(health_data)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # Task automatically retries on failure

    @health_monitor.before_loop
    async def before_health_monitor(self):
        """Wait for bot to be ready before starting."""
        await self.bot.wait_until_ready()
        logger.info("Health monitoring started")

    @health_monitor.after_loop
    async def after_health_monitor(self):
        """Cleanup after task stops."""
        if self.health_monitor.is_being_cancelled():
            logger.info("Health monitoring cancelled")
        else:
            logger.info("Health monitoring completed")
```

**Key Features:**

- **Automatic reconnection** on network failures
- **Exception handling** with retry logic
- **Clean cancellation** support
- **Scheduling** (seconds, minutes, hours, or specific times)
- **Before/after hooks** for setup and cleanup

**Common Patterns:**

```python
# Database cleanup task
@tasks.loop(hours=1.0)
async def cleanup_old_data(self):
    """Clean up old data hourly."""
    try:
        deleted_count = await self.db.cleanup_old_records()
        logger.info(f"Cleaned up {deleted_count} old records")
    except TuxDatabaseError as e:
        logger.error(f"Database cleanup failed: {e}")
        # Task will retry automatically

# Handle specific exceptions during reconnection
@tasks.loop(minutes=10.0)
async def sync_external_data(self):
    """Sync data with external service."""
    async with self.db.session() as session:
        # Sync logic here
        pass

# Add database connection errors to retry logic
sync_external_data.add_exception_type(TuxDatabaseConnectionError)

# Scheduled tasks at specific times
import datetime

@tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=datetime.timezone.utc))
async def daily_report(self):
    """Generate daily report at 9 AM UTC."""
    report = await self.generate_daily_report()
    await self.send_report_to_channel(report)

# Multiple times per day
times = [
    datetime.time(hour=9, tzinfo=datetime.timezone.utc),
    datetime.time(hour=14, tzinfo=datetime.timezone.utc),
    datetime.time(hour=19, tzinfo=datetime.timezone.utc)
]

@tasks.loop(time=times)
async def status_updates(self):
    """Send status updates 3 times daily."""
    status = await self.get_system_status()
    await self.update_status_channel(status)
```

### Background Tasks (Raw Asyncio)

```python
class BackgroundService:
    """Service for managing background tasks."""

    def __init__(self):
        self._tasks: set[asyncio.Task] = set()
        self._running = True

    async def start_background_monitoring(self):
        """Start background monitoring task."""
        task = asyncio.create_task(self._monitor_system())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _monitor_system(self):
        """Monitor system health in background."""
        while self._running:
            try:
                health_data = await self.check_system_health()
                await self.report_health(health_data)
            except Exception as e:
                logger.error(f"Health monitoring failed: {e}")

            await asyncio.sleep(300)  # Check every 5 minutes

    async def stop_all_tasks(self):
        """Gracefully stop all background tasks."""
        self._running = False

        if self._tasks:
            # Cancel all running tasks
            for task in self._tasks:
                task.cancel()

            # Wait for tasks to complete cancellation
            await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("All background tasks stopped")
```

### Task Groups (Python 3.11+)

```python
async def process_user_batch(self, user_ids: list[int]):
    """Process multiple users with proper task management."""

    async def process_single_user(user_id: int):
        try:
            return await self.process_user(user_id)
        except Exception as e:
            logger.error(f"Failed to process user {user_id}: {e}")
            return None

    # ✅ Good: Use TaskGroup for structured concurrency (Python 3.11+)
    async with asyncio.TaskGroup() as tg:
        for user_id in user_ids:
            tg.create_task(process_single_user(user_id))

    # All tasks complete here, exceptions propagated automatically
    logger.info(f"Processed {len(user_ids)} users")
```

### Task Cancellation

```python
async def cancellable_operation(self, timeout: float = 30.0):
    """Operation that can be cancelled gracefully."""

    try:
        # Create task that can be cancelled
        task = asyncio.create_task(self.long_running_operation())

        # Wait with timeout
        result = await asyncio.wait_for(task, timeout=timeout)
        return result

    except asyncio.TimeoutError:
        logger.warning("Operation timed out, cancelling...")
        task.cancel()

        try:
            # Wait for clean cancellation
            await task
        except asyncio.CancelledError:
            logger.info("Operation cancelled successfully")

        raise TuxTimeoutError("Operation was cancelled due to timeout")

    except asyncio.CancelledError:
        logger.info("Operation was cancelled externally")
        # Perform cleanup
        await self.cleanup_resources()
        raise
```

## Concurrency Patterns

### Semaphores for Resource Limiting

```python
class RateLimitedAPI:
    """API client with concurrency limiting."""

    def __init__(self, max_concurrent: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def api_call(self, endpoint: str, **params):
        """Make API call with concurrency control."""

        async with self._semaphore:
            # Only max_concurrent calls can execute this section simultaneously
            response = await http_client.get(endpoint, params=params)
            return response.json()

# Usage in Tux
class GitHubService:
    """GitHub API service with rate limiting."""

    def __init__(self):
        # GitHub allows 5000 requests/hour, but limit concurrency
        self._api = RateLimitedAPI(max_concurrent=10)

    async def get_user_repos(self, username: str) -> list[dict]:
        """Get user's repositories."""
        return await self._api.api_call(f"/users/{username}/repos")
```

### Queues for Producer-Consumer Patterns

```python
class MessageProcessor:
    """Process Discord messages asynchronously."""

    def __init__(self):
        self._queue: asyncio.Queue[discord.Message] = asyncio.Queue(maxsize=100)
        self._processing_task: asyncio.Task | None = None

    async def start_processing(self):
        """Start the message processing loop."""
        self._processing_task = asyncio.create_task(self._process_messages())

    async def stop_processing(self):
        """Stop the message processing."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

    async def queue_message(self, message: discord.Message):
        """Add message to processing queue."""
        try:
            self._queue.put_nowait(message)
        except asyncio.QueueFull:
            logger.warning("Message processing queue is full, dropping message")

    async def _process_messages(self):
        """Process messages from the queue."""
        while True:
            try:
                # Wait for next message
                message = await self._queue.get()

                # Process message (don't await to avoid blocking queue)
                asyncio.create_task(self._handle_message(message))

                self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message processing error: {e}")

    async def _handle_message(self, message: discord.Message):
        """Handle individual message processing."""
        # Message-specific processing logic
        await self.analyze_content(message)
        await self.check_for_spam(message)
        await self.update_statistics(message)
```

## Common Async Pitfalls

### Blocking Operations in Async Code

```python
# ❌ Bad: Blocking I/O in async function
async def bad_file_operation(self, filename: str):
    # This blocks the event loop!
    with open(filename, 'r') as f:
        data = f.read()  # Synchronous I/O
    return data

# ✅ Good: Use async file operations
async def good_file_operation(self, filename: str):
    import aiofiles

    async with aiofiles.open(filename, 'r') as f:
        data = await f.read()  # Non-blocking I/O
    return data

# ✅ Good: Run blocking operations in thread pool
async def thread_blocking_operation(self, filename: str):
    import asyncio

    # Run blocking operation in thread pool
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, self._blocking_read, filename)
    return data

def _blocking_read(self, filename: str) -> str:
    """Blocking file read (runs in thread pool)."""
    with open(filename, 'r') as f:
        return f.read()
```

### Incorrect Exception Handling

```python
# ❌ Bad: Catching exceptions too broadly
async def bad_error_handling(self):
    try:
        await risky_operation()
    except Exception:  # Catches KeyboardInterrupt, SystemExit!
        logger.error("Something went wrong")

# ❌ Bad: Forgetting to await
async def bad_await_handling(self):
    try:
        result = risky_operation()  # Forgot await!
        return result
    except Exception as e:
        logger.error(f"Error: {e}")

# ✅ Good: Specific exception handling
async def good_error_handling(self):
    try:
        result = await risky_operation()
        return result
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise
    except ConnectionError as e:
        logger.error(f"Network error: {e}")
        # Retry logic...
        return await self.retry_operation()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

### Race Conditions

```python
class SharedCounter:
    """Thread-safe counter with async considerations."""

    def __init__(self):
        self._value = 0
        self._lock = asyncio.Lock()

    # ❌ Bad: Race condition
    async def increment_bad(self):
        current = self._value
        await asyncio.sleep(0.01)  # Context switch can happen here
        self._value = current + 1

    # ✅ Good: Protected with lock
    async def increment_good(self):
        async with self._lock:
            current = self._value
            await asyncio.sleep(0.01)  # Safe inside lock
            self._value = current + 1
            return self._value

    # ✅ Good: Atomic operations
    async def increment_atomic(self):
        async with self._lock:
            self._value += 1
            return self._value
```

## Performance Optimization

### Concurrent Operations

```python
# ❌ Bad: Sequential API calls
async def slow_user_processing(self, user_ids: list[int]):
    results = []
    for user_id in user_ids:
        user_data = await self.fetch_user(user_id)
        results.append(user_data)
    return results

# ✅ Good: Concurrent API calls
async def fast_user_processing(self, user_ids: list[int]):
    # Fetch all users concurrently
    tasks = [self.fetch_user(user_id) for user_id in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle partial failures
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch user {user_ids[i]}: {result}")
        else:
            successful_results.append(result)

    return successful_results
```

### Connection Pooling

```python
# ✅ Good: Reuse connections (Tux does this automatically with http_client)
class APIClient:
    """Client that reuses connections."""

    def __init__(self):
        # Single client instance for all requests
        self.client = http_client  # Tux's shared client

    async def get_user(self, user_id: int) -> dict:
        # Reuses connection from pool
        response = await self.client.get(f"/users/{user_id}")
        return response.json()

    async def get_multiple_users(self, user_ids: list[int]) -> list[dict]:
        # All requests share connection pool
        tasks = [self.get_user(uid) for uid in user_ids]
        return await asyncio.gather(*tasks)
```

### Memory Management

```python
# ✅ Good: Process large datasets in chunks
async def process_large_dataset(self, dataset: list[dict], chunk_size: int = 100):
    """Process large dataset without loading everything into memory."""

    results = []
    for i in range(0, len(dataset), chunk_size):
        chunk = dataset[i:i + chunk_size]

        # Process chunk concurrently
        chunk_results = await asyncio.gather(*[
            self.process_item(item) for item in chunk
        ], return_exceptions=True)

        results.extend(chunk_results)

        # Allow other tasks to run
        await asyncio.sleep(0)

    return results

# ✅ Good: Use async generators for streaming
async def stream_large_results(self, query: str):
    """Stream results to avoid loading everything into memory."""

    async with self.db.session() as session:
        # Use async iterator for streaming
        async for row in await session.stream_scalars(
            text(query), execution_options={"stream_results": True}
        ):
            yield row
            # Allow other coroutines to run
            await asyncio.sleep(0)
```

## Testing Async Code

### Async Test Functions

```python
import pytest
import pytest_asyncio

class TestUserService:
    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation."""
        service = UserService()

        user_data = {"name": "test", "email": "test@example.com"}
        user = await service.create_user(user_data)

        assert user.name == "test"
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self):
        """Test concurrent user operations."""
        service = UserService()

        # Create multiple users concurrently
        user_data = [
            {"name": f"user{i}", "email": f"user{i}@example.com"}
            for i in range(10)
        ]

        tasks = [service.create_user(data) for data in user_data]
        users = await asyncio.gather(*tasks)

        assert len(users) == 10
        assert all(user.id is not None for user in users)

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in async operations."""
        service = UserService()

        with patch.object(service.http_client, 'get') as mock_get:
            # Simulate slow response
            mock_get.return_value = asyncio.create_task(asyncio.sleep(10))

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    service.fetch_user_data(123),
                    timeout=1.0
                )
```

### Mocking Async Functions

```python
from unittest.mock import AsyncMock, patch

class TestAPIClient:
    @pytest.mark.asyncio
    async def test_api_call_with_mock(self):
        """Test API call with mocked async response."""

        client = APIClient()

        with patch.object(client, 'http_client') as mock_client:
            # Create mock response
            mock_response = AsyncMock()
            mock_response.json.return_value = {"user": "test"}
            mock_client.get.return_value = mock_response

            result = await client.get_user(123)

            assert result == {"user": "test"}
            mock_client.get.assert_called_once_with("/users/123")

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self):
        """Test multiple concurrent API calls."""

        client = APIClient()

        with patch.object(client, 'http_client') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"user": "test"}
            mock_client.get.return_value = mock_response

            # Make multiple concurrent calls
            tasks = [client.get_user(i) for i in range(5)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 5
            assert all(r == {"user": "test"} for r in results)
            assert mock_client.get.call_count == 5
```

## Debugging Async Issues

### Async Debugging Tools

```python
import asyncio
import logging

# Enable debug mode for asyncio
logging.getLogger('asyncio').setLevel(logging.DEBUG)

# Or set environment variable
# PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python -X dev -c "import asyncio; asyncio.run(main())"

async def debug_async_flow():
    """Debug async execution flow."""

    # Log current task
    current_task = asyncio.current_task()
    logger.debug(f"Running in task: {current_task}")

    # Log all running tasks
    all_tasks = asyncio.all_tasks()
    logger.debug(f"Total running tasks: {len(all_tasks)}")
    for task in all_tasks:
        logger.debug(f"Task: {task}, Done: {task.done()}")

    # Add timing information
    start_time = asyncio.get_running_loop().time()
    result = await some_operation()
    end_time = asyncio.get_running_loop().time()

    logger.debug(f"Operation took {end_time - start_time:.3f}s")
    return result
```

### Detecting Blocking Code

```python
import asyncio
import time

async def detect_blocking_code():
    """Detect blocking code in async functions."""

    # This will show warnings if code blocks for >100ms
    asyncio.get_running_loop().slow_callback_duration = 0.1

    start_time = time.perf_counter()

    # Your potentially blocking code here
    await some_operation()

    end_time = time.perf_counter()
    duration = end_time - start_time

    if duration > 1.0:  # Adjust threshold as needed
        logger.warning(f"Slow operation detected: {duration:.2f}s")

    return result
```

### Task Monitoring

```python
class AsyncMonitor:
    """Monitor async task execution."""

    def __init__(self):
        self._active_tasks: dict[str, asyncio.Task] = {}

    def start_monitoring(self):
        """Start monitoring async tasks."""
        asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        """Monitor running tasks and log issues."""

        while True:
            try:
                all_tasks = asyncio.all_tasks()
                long_running = []

                for task in all_tasks:
                    if hasattr(task, 'get_coro'):
                        coro = task.get_coro()
                        if hasattr(coro, 'cr_frame') and coro.cr_frame:
                            # Task has been running for a while
                            task_age = asyncio.get_running_loop().time() - task.get_loop().time()
                            if task_age > 30:  # Running for more than 30 seconds
                                long_running.append((task, task_age))

                if long_running:
                    logger.warning(f"Found {len(long_running)} long-running tasks")
                    for task, age in long_running:
                        logger.warning(f"Task {task} has been running for {age:.1f}s")

            except Exception as e:
                logger.error(f"Task monitoring error: {e}")

            await asyncio.sleep(60)  # Check every minute
```

## Best Practices Checklist

### Code Structure

- [ ] All I/O operations use async/await
- [ ] No synchronous HTTP requests or file operations
- [ ] Functions that perform I/O are marked `async`
- [ ] Async generators used for streaming data
- [ ] Background tasks use `discord.ext.tasks` instead of raw asyncio

### Concurrency

- [ ] Multiple independent operations run concurrently with `asyncio.gather()`
- [ ] Resource access protected with appropriate locks
- [ ] Semaphores used to limit concurrent resource usage
- [ ] Task groups used for structured concurrency (Python 3.11+)

### Error Handling

- [ ] Exceptions properly chained with `raise ... from e`
- [ ] Timeouts implemented for long-running operations
- [ ] Cancellation handled gracefully in all async functions
- [ ] Resource cleanup happens in `finally` blocks or context managers

### Performance

- [ ] Connection pooling used for database and HTTP clients
- [ ] Large datasets processed in chunks to avoid memory issues
- [ ] Unnecessary async operations avoided in hot paths
- [ ] Background tasks properly managed and cleaned up

### Testing

- [ ] All async functions tested with `@pytest.mark.asyncio`
- [ ] Concurrent operations tested for race conditions
- [ ] Timeouts and cancellation scenarios covered
- [ ] Mocking properly handles async functions

## Resources

- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [Discord.py Async Guide](https://discordpy.readthedocs.io/en/stable/faq.html#what-is-a-coroutine)
- [discord.ext.tasks Documentation](https://discordpy.readthedocs.io/en/stable/ext/tasks/) - Background task helpers
- [FastAPI Async Guide](https://fastapi.tiangolo.com/async/) (similar patterns)
