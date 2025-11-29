---
title: Async Best Practices
description: Async programming best practices for Tux development, including concurrency patterns, Discord.py async considerations, and performance optimization.
tags:
  - developer-guide
  - best-practices
  - async
---

# Async Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Discord bots operate in a highly concurrent environment where thousands of users can interact simultaneously. Understanding async programming is essential for building responsive, scalable bots that handle multiple operations efficiently.

## Why Async Matters

Traditional synchronous programming creates blocking operations that freeze your bot when waiting for I/O. When one user's command waits for a database query, every other user must wait too. Async programming solves this by allowing your bot to handle multiple operations concurrently without blocking.

### The Discord Bot Challenge

Discord bots face unique concurrency challenges. A single bot might need to:

- Process hundreds of messages per second across multiple servers
- Handle simultaneous command invocations from different users
- Manage background tasks like periodic updates or cleanup operations
- Coordinate database queries, API calls, and Discord interactions

Without async programming, your bot becomes a bottleneck. One slow database query blocks all other operations, making your bot feel unresponsive and unreliable.

### How Async Helps

Async programming lets your bot start multiple operations and switch between them as they wait for I/O. When one database query is waiting for a response, your bot can process another user's command. This non-blocking approach means your bot stays responsive even under heavy load.

Tux uses asyncio throughout its architecture. Database operations use async SQLAlchemy with connection pooling. HTTP requests use a shared async client. All Discord interactions are async. Background tasks run concurrently without blocking command processing.

## Understanding Async Fundamentals

### Coroutines and Awaitables

Async functions are coroutines—special functions that can pause and resume execution. When you call an async function, it returns a coroutine object that doesn't execute until you await it. This pause-and-resume mechanism is what makes concurrency possible.

Always mark functions that perform I/O as `async`. This includes database queries, HTTP requests, Discord API calls, and file operations. Functions that only do computation don't need to be async, but if they call async functions, they must be async too.

When you await an async function, you're telling Python to pause execution here and let other coroutines run. If the awaited operation is waiting for I/O, Python switches to another coroutine. When the I/O completes, execution resumes where it left off.

### The Event Loop

The event loop manages all async operations. It tracks which coroutines are waiting for what, switches between them efficiently, and resumes them when their operations complete. In Tux, discord.py manages the event loop automatically—you don't need to create or manage it yourself.

Don't create your own event loop in Discord bot code. Let discord.py handle it. Creating multiple event loops causes conflicts and breaks the framework's assumptions about how async operations work.

## Discord.py Async Patterns

### Command Handlers

Discord.py commands are async by default. Your command handlers receive contexts and can await Discord API calls, database queries, and other async operations. This design makes concurrent command processing natural.

When multiple users invoke commands simultaneously, each command runs as a separate coroutine. They execute concurrently, sharing the event loop's time. One command waiting for a database query doesn't block others from executing.

Use `asyncio.gather()` when you have multiple independent async operations. Instead of awaiting them sequentially, gather them together and await the collection. This runs them concurrently, reducing total execution time.

For operations that might fail independently, use `return_exceptions=True` with gather. This collects exceptions as results instead of stopping at the first failure, letting you handle partial successes gracefully.

### Event Listeners

Event listeners handle Discord events like messages, member joins, and reactions. These events can arrive rapidly, so your listeners should process them efficiently without blocking.

Use early returns to skip unnecessary processing. If a message is from a bot, return immediately. If a user doesn't have permissions, return before doing expensive checks. These small optimizations add up when processing hundreds of events per second.

When processing events requires multiple async operations, gather them together. Checking user permissions and analyzing message content can happen concurrently. Only await them together when you need both results.

### Rate Limiting Considerations

Discord's API has rate limits. When performing bulk operations like banning multiple users, process them in batches with delays between batches. Within each batch, use gather to process users concurrently, but respect rate limits by spacing batches appropriately.

The `discord.ext.tasks` extension provides built-in rate limiting and retry logic for background tasks. Use it instead of raw asyncio tasks when you need periodic operations or scheduled tasks.

## Task Management

### Discord.py Tasks Extension

Tux uses `discord.ext.tasks` for background tasks. This extension provides automatic reconnection logic, exception handling, and scheduling that solves common issues with raw asyncio tasks.

Tasks created with `@tasks.loop()` automatically handle reconnection on network failures. They include retry logic for transient errors. They support clean cancellation during shutdown. They provide before and after hooks for setup and cleanup.

Use task loops for periodic operations like health checks, data cleanup, or status updates. Configure them with intervals (seconds, minutes, hours) or specific times. Add exception types to the retry list for automatic recovery from specific errors.

Register tasks in your cog's `__init__` and cancel them in `cog_unload()`. This ensures proper cleanup when cogs reload or the bot shuts down. The task extension handles the complexity of cancellation and reconnection automatically.

### Background Tasks

For one-off background operations or custom task management, use raw asyncio tasks. Create tasks with `asyncio.create_task()` and track them in a set. Add done callbacks to remove completed tasks automatically.

When shutting down, cancel all tasks and await their cancellation. Use `asyncio.gather()` with `return_exceptions=True` to wait for all tasks to finish cancellation without stopping on errors.

For structured concurrency with Python 3.11+, use `asyncio.TaskGroup`. This provides automatic exception propagation and ensures all tasks complete before continuing. Task groups make it clear which tasks belong together and handle failures as a unit.

### Task Cancellation

Design your async functions to handle cancellation gracefully. When a task is cancelled, it raises `CancelledError`. Catch this exception in long-running operations to perform cleanup before the task terminates.

Use timeouts with `asyncio.wait_for()` for operations that might hang. If an operation exceeds its timeout, cancel it and handle the timeout appropriately. Don't let operations run indefinitely—always have a timeout or cancellation mechanism.

## Concurrency Patterns

### Semaphores for Resource Limiting

Semaphores limit how many operations can run concurrently. Use them when you need to throttle API calls, limit database connections, or control resource usage.

Create a semaphore with your desired concurrency limit. Acquire it before operations that need limiting, and release it when done. The `async with` statement handles acquisition and release automatically.

For API clients with rate limits, use semaphores to prevent exceeding limits while still allowing concurrency. Limit concurrent requests to stay within rate limits while processing multiple operations efficiently.

### Queues for Producer-Consumer Patterns

Queues decouple producers (event handlers) from consumers (processors). When events arrive faster than you can process them, queues buffer the work and let processors catch up.

Create an async queue with an appropriate size limit. Producers add items to the queue without waiting. Consumers process items from the queue asynchronously. If the queue fills up, producers can drop items or wait, depending on your requirements.

Use queues for message processing, image analysis, or any operation where arrival rate might exceed processing rate. The queue smooths out bursts and prevents overwhelming your processing logic.

### Locks for Shared State

When multiple coroutines access shared state, use locks to prevent race conditions. Async locks work like threading locks but don't block the event loop—they yield control instead.

Acquire locks before modifying shared state. Keep critical sections small to minimize contention. Use locks only when necessary—many operations don't need them if you design your code to avoid shared mutable state.

For simple counters or flags, consider using atomic operations or designing your code to avoid shared state entirely. Locks add complexity and potential for deadlocks, so use them judiciously.

## Common Pitfalls

### Blocking Operations

The most common mistake is using blocking I/O in async code. Synchronous file operations, HTTP requests, or database queries block the entire event loop, defeating the purpose of async programming.

Use async alternatives for all I/O operations. For files, use `aiofiles`. For HTTP, use `httpx.AsyncClient` (which Tux provides as `http_client`). For databases, use async SQLAlchemy. If you must use blocking code, run it in a thread pool with `loop.run_in_executor()`.

### Forgetting to Await

Another common mistake is calling async functions without awaiting them. This returns a coroutine object instead of the actual result, leading to confusing errors later.

Always await async function calls. If you need to start a task without waiting for it, use `asyncio.create_task()` explicitly. This makes your intent clear and properly manages the task lifecycle.

### Incorrect Exception Handling

Catching exceptions too broadly hides important errors. Don't catch `Exception` unless you're at the top level of error handling. Catch specific exception types and handle them appropriately.

When catching exceptions in async code, remember that `CancelledError` is special. Don't catch it unless you're handling cancellation specifically. Let it propagate so tasks can be cancelled properly.

Chain exceptions with `raise ... from e` to preserve error context. This helps debugging by showing the full error chain from original cause to final error.

### Race Conditions

Race conditions occur when multiple coroutines modify shared state without coordination. Use locks to protect critical sections, or better yet, design your code to avoid shared mutable state.

When reading a value, modifying it, and writing it back, use a lock to make the operation atomic. Without a lock, another coroutine might modify the value between your read and write, causing lost updates or inconsistent state.

## Performance Optimization

### Concurrent Operations

The biggest performance win comes from running independent operations concurrently. Instead of awaiting operations sequentially, gather them together and await the collection.

When fetching data for multiple users, create tasks for each fetch and gather them together. This runs all fetches concurrently instead of waiting for each one sequentially. The total time becomes the slowest operation, not the sum of all operations.

Use `return_exceptions=True` with gather to handle partial failures gracefully. This lets successful operations complete even if some fail, giving you partial results instead of complete failure.

### Connection Pooling

Reuse connections instead of creating new ones for each operation. Tux provides a shared `http_client` that pools connections automatically. Use it for all HTTP requests instead of creating new clients.

Database connections are pooled automatically by SQLAlchemy. The connection pool manages connections efficiently, reusing them across operations. Don't create new database engines—use the shared service.

### Memory Management

Process large datasets in chunks to avoid loading everything into memory. Instead of fetching all records at once, fetch them in batches and process each batch before fetching the next.

Use async generators for streaming large results. Yield items as you process them instead of collecting everything in a list. This keeps memory usage constant regardless of dataset size.

Add `await asyncio.sleep(0)` periodically in long-running loops to yield control to other coroutines. This prevents one operation from monopolizing the event loop and keeps your bot responsive.

## Testing Async Code

### Async Test Functions

Mark async test functions with `@pytest.mark.asyncio`. This tells pytest to run them in an async context. Without this marker, pytest won't await your async functions, leading to coroutine objects instead of results.

Test concurrent operations by gathering multiple operations and asserting on the results. This verifies that operations actually run concurrently and produce correct results.

Use timeouts in tests to catch operations that hang. Set reasonable timeouts and let tests fail if operations exceed them. This catches deadlocks and infinite loops early.

### Mocking Async Functions

Use `AsyncMock` from `unittest.mock` for mocking async functions. Regular mocks don't work correctly with async code—they return coroutine objects instead of awaited results.

When patching async functions, ensure the mock returns an awaitable. Use `AsyncMock` or make your mock return a coroutine that resolves to the desired value.

Test cancellation scenarios by cancelling tasks and verifying cleanup happens correctly. This ensures your code handles cancellation gracefully and doesn't leak resources.

## Debugging Async Issues

### Understanding Task State

When debugging async issues, check task states. Use `asyncio.all_tasks()` to see all running tasks. Check if tasks are done, cancelled, or still running. This helps identify tasks that aren't completing or are being cancelled unexpectedly.

Log task information in your code to understand execution flow. Include task names and states in debug logs to trace how tasks progress through your code.

### Detecting Blocking Code

Set `slow_callback_duration` on the event loop to detect blocking operations. If a callback takes longer than this duration, Python logs a warning. This helps identify code that's blocking the event loop.

Monitor operation durations and log warnings for slow operations. This helps identify performance bottlenecks and operations that might benefit from optimization or parallelization.

### Task Monitoring

Track long-running tasks to identify potential issues. Tasks that run for extended periods might indicate blocking operations or infinite loops. Monitor task lifetimes and alert on tasks that exceed expected durations.

Use Tux's task monitor to track background tasks. Register your tasks with the monitor to ensure they're cleaned up properly during shutdown and to track their execution.

## Best Practices Summary

### Code Structure

Mark all I/O operations as async. Use async file operations, async HTTP clients, and async database queries. Don't mix sync and async I/O—stick to async throughout.

Use async generators for streaming data. This keeps memory usage constant and allows processing data as it arrives instead of waiting for everything to load.

Prefer `discord.ext.tasks` for background tasks over raw asyncio tasks. The extension provides better error handling, reconnection logic, and integration with Discord.py's lifecycle.

### Concurrency

Run independent operations concurrently with `asyncio.gather()`. Don't await operations sequentially when they can run in parallel.

Protect shared state with locks when necessary, but prefer designs that avoid shared mutable state. Use semaphores to limit resource usage and prevent overwhelming external services.

Use task groups for structured concurrency when you need to ensure all tasks complete together. This makes task relationships explicit and handles failures as a unit.

### Error Handling

Chain exceptions with `raise ... from e` to preserve error context. This helps debugging by showing the full error chain.

Implement timeouts for long-running operations. Don't let operations run indefinitely—always have a cancellation mechanism.

Handle cancellation gracefully in all async functions. Catch `CancelledError` when you need to perform cleanup, but let it propagate otherwise.

### Performance

Reuse connections through pooling. Use Tux's shared `http_client` and database service instead of creating new connections.

Process large datasets in chunks to avoid memory issues. Use async generators for streaming when possible.

Add `await asyncio.sleep(0)` in long-running loops to yield control. This keeps your bot responsive and prevents one operation from monopolizing the event loop.

## Resources

- **AsyncIO Documentation**: Python's official asyncio documentation covers all the fundamentals
- **Discord.py Async Guide**: Discord.py's FAQ explains how async works in the framework
- **discord.ext.tasks Documentation**: The tasks extension provides background task helpers with automatic reconnection
- **FastAPI Async Guide**: FastAPI's async patterns are similar to Discord bots and provide good examples
