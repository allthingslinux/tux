---
title: Error Handling Best Practices
description: Error handling best practices for Tux development, including exception patterns, graceful degradation, and debugging techniques.
---

# Error Handling Best Practices

Error handling is crucial for building reliable Discord bots. Users expect your bot to handle failures gracefully, provide helpful feedback, and continue operating even when things go wrong. Good error handling separates professional bots from fragile ones.

## Understanding Tux's Exception System

Tux uses a hierarchical exception system built on `TuxError`. This hierarchy lets you catch errors at the right level of specificity. Database errors inherit from `TuxDatabaseError`, API errors from `TuxAPIError`, and permission errors from `TuxPermissionError`.

Use specific exception types instead of generic ones. When you raise `TuxDatabaseConnectionError`, callers can handle database connection issues specifically. They can retry, fall back to cached data, or show appropriate error messages. Generic exceptions force callers to guess what went wrong.

The exception hierarchy includes:

- **Database errors** - Connection failures, query errors, migration issues
- **API errors** - HTTP failures, rate limits, resource not found
- **Permission errors** - Insufficient permissions, invalid access levels
- **Configuration errors** - Invalid settings, missing required values
- **Service errors** - Cog loading failures, hot reload issues

When you catch exceptions, chain them properly with `raise ... from e`. This preserves the original error context, making debugging easier. The error chain shows what happened at each level, from the original cause to the final error.

## Error Categories and Strategies

### User Errors

User errors happen when users provide invalid input or lack permissions. These errors should be handled globally and shown to users with friendly messages. Don't log these as errors—they're expected user behavior.

Examples include invalid command arguments, missing permissions, rate limits, and command not found. The global error handler catches these and converts them to user-friendly messages automatically.

Raise specific exceptions for user errors. Use `commands.BadArgument` for invalid input, `commands.MissingPermissions` for permission issues, and `TuxPermissionLevelError` for custom permission checks. The global handler knows how to format these for users.

### Infrastructure Errors

Infrastructure errors occur when external systems fail—databases timeout, APIs go down, networks disconnect. These errors need local handling with graceful degradation. Your bot should continue operating even when some services are unavailable.

Handle infrastructure errors locally with fallbacks. If an external API fails, use cached data. If the database is temporarily unavailable, queue operations for later. If file operations fail, log the error and continue with reduced functionality.

Log infrastructure errors appropriately. Use warning level for transient failures that you handle gracefully. Use error level for failures that require attention but don't stop the bot. Use critical level only for failures that prevent core functionality.

### System Errors

System errors indicate serious problems—invalid configuration, missing dependencies, critical bugs. These errors should fail fast with clear error messages. Don't try to continue operating with broken configuration or missing dependencies.

For configuration errors, validate early and fail immediately. Don't let the bot start with invalid configuration—it will cause confusing errors later. Provide clear error messages explaining what's wrong and how to fix it.

For critical bugs, log the error with full context and shut down gracefully. Don't try to recover from programming errors—they indicate bugs that need fixing, not runtime conditions to handle.

## Core Principles

### Fail Gracefully, Log Aggressively

When operations fail, handle them gracefully but log everything. Users shouldn't see technical errors, but you need detailed logs for debugging. Return `None` or empty results instead of crashing, but log the failure with full context.

Include context in your logs. Log user IDs, command names, operation types, and relevant parameters. This context helps you understand what was happening when errors occurred. Without context, error logs are useless for debugging.

Use appropriate log levels. Debug for detailed execution flow. Info for normal operations and recoverable issues. Warning for problems that don't prevent functionality. Error for failures that need attention. Critical only for failures that stop core functionality.

### Be Specific, Not Generic

Catch specific exceptions, not generic ones. When you catch `TuxDatabaseConnectionError`, you know it's a connection issue and can retry or use cached data. When you catch `Exception`, you don't know what went wrong and can't handle it appropriately.

Handle exceptions at the right level. Catch specific exceptions where you can handle them meaningfully. Let exceptions propagate to the global handler when you can't handle them locally. Don't catch exceptions just to log them—let them propagate to handlers that can actually deal with them.

Chain exceptions properly. When you catch an exception and raise a new one, use `raise ... from e` to preserve the chain. This shows the full error path from original cause to final error, making debugging much easier.

## Error Handling Patterns

### Database Operations

Database operations can fail for many reasons—connection issues, query errors, constraint violations. Handle each type of failure appropriately. Connection errors might be transient and worth retrying. Query errors indicate problems with the query itself and shouldn't be retried.

Implement retry logic for transient failures. Use exponential backoff to avoid overwhelming the database during outages. Limit retry attempts to prevent infinite loops. After retries are exhausted, fail gracefully with appropriate error messages.

For query errors, don't retry—the query itself is wrong. Log the error with the query details and raise an appropriate exception. Let callers handle the failure or let it propagate to the global handler.

Use database transactions for multi-step operations. If any step fails, roll back the entire transaction. This keeps your database consistent and prevents partial updates that cause data corruption.

### External API Calls

External APIs can fail in many ways—timeouts, rate limits, server errors, network issues. Handle each failure mode appropriately. Timeouts might be worth retrying. Rate limits need backoff. Server errors might be transient.

Check HTTP status codes to determine appropriate handling. 404 means the resource doesn't exist—handle it gracefully. 403 might mean rate limiting—back off and retry. 500 means server error—might be transient, worth retrying.

Use timeouts for all API calls. Don't let API calls hang indefinitely. Set reasonable timeouts based on expected response times. If an API call times out, log it and handle it appropriately—retry, use cached data, or fail gracefully.

Convert HTTP exceptions to Tux exceptions. Wrap `httpx` exceptions in `TuxAPIError` subclasses to provide consistent error handling throughout your code. This lets callers handle API errors without knowing about the HTTP library.

### File Operations

File operations can fail due to permissions, disk space, or I/O errors. Handle these failures gracefully. Permission errors should be logged and raised as `TuxPermissionError`. I/O errors might be transient and worth retrying.

Use atomic file operations when possible. Write to temporary files first, then rename them atomically. This prevents partial writes from corrupting files. If the write fails, the original file remains intact.

Clean up temporary files in finally blocks. Even if operations fail, ensure temporary files are deleted. Use context managers to ensure cleanup happens automatically, even when exceptions occur.

## Command Error Handling

### Global Error Handler Integration

Tux's global error handler automatically catches command errors and converts them to user-friendly messages. Focus on raising appropriate exceptions in your commands—the handler takes care of formatting and sending responses.

The global handler categorizes errors automatically. It knows how to format Discord API errors, permission errors, validation errors, and Tux exceptions. It provides user-friendly messages, logs errors appropriately, and reports to Sentry with context.

Don't try to handle user-facing errors in commands. Raise appropriate exceptions and let the global handler format them. This keeps your command code focused on business logic and ensures consistent error handling across all commands.

For infrastructure errors in commands, handle them locally and provide fallback behavior. If a database query fails, return a cached result or show a message explaining the issue. Don't let infrastructure failures become user-facing errors unless necessary.

### Custom Validation Errors

Create custom validation errors for complex validation logic. When validation fails, raise a `TuxValidationError` with details about what failed and why. The global handler formats these for users automatically.

Include field names and values in validation errors. This helps users understand what they entered incorrectly. Explain why validation failed—"must be at least 3 characters" is more helpful than "invalid input".

Validate early and fail fast. Check input validity before doing expensive operations. Don't waste resources processing invalid input. Return clear error messages explaining what's wrong and how to fix it.

## Async Error Handling

### Task Exception Handling

When running multiple operations concurrently, handle exceptions in each task independently. Use `asyncio.gather()` with `return_exceptions=True` to collect exceptions as results instead of stopping at the first failure.

Process results after gathering completes. Check each result to see if it's an exception or a value. Handle exceptions appropriately—log them, retry operations, or collect them for batch processing. Successful operations shouldn't be affected by failures in other operations.

For batch operations, track successes and failures separately. Log summary information about how many operations succeeded and failed. This helps you understand the overall health of batch operations and identify patterns in failures.

### Timeout Handling

Always use timeouts for long-running operations. Don't let operations hang indefinitely. Set reasonable timeouts based on expected operation duration. If operations consistently timeout, investigate why they're slow.

When timeouts occur, cancel the operation and handle the cancellation gracefully. Log timeout information to help identify slow operations. Consider whether timeouts indicate problems that need fixing or just slow external services.

Use `asyncio.wait_for()` for timeout handling. This automatically cancels operations that exceed their timeout. Handle `TimeoutError` appropriately—retry, use fallbacks, or fail gracefully with clear error messages.

## Context Managers for Error Handling

### Database Transactions

Use context managers for database transactions. They ensure transactions are committed on success and rolled back on failure. This keeps your database consistent and prevents partial updates.

Create transaction context managers that handle commit and rollback automatically. If any operation in a transaction fails, roll back the entire transaction. Don't commit partial transactions—they cause data inconsistency.

Log transaction outcomes appropriately. Log successful commits at debug level. Log rollbacks at warning level with error details. This helps you understand transaction patterns and identify problematic operations.

### Resource Cleanup

Use context managers for all resources that need cleanup—files, network connections, temporary data. Context managers ensure cleanup happens even when exceptions occur. Don't rely on manual cleanup in finally blocks—use context managers instead.

Create context managers for complex resources. If you need to create temporary files, use a context manager that creates them and cleans them up automatically. If you need to acquire and release locks, use a context manager.

Always clean up resources, even on errors. Don't let temporary files accumulate or connections leak. Context managers handle this automatically, ensuring cleanup happens regardless of how operations complete.

## Testing Error Conditions

### Exception Testing

Test that your code raises appropriate exceptions. Use `pytest.raises()` to verify exceptions are raised for invalid inputs or error conditions. Test that exception messages are helpful and include relevant context.

Test error handling paths. Don't just test happy paths—test what happens when things go wrong. Verify that errors are handled gracefully, resources are cleaned up, and appropriate exceptions are raised.

Mock external dependencies to simulate failures. Test how your code handles database failures, API timeouts, and network errors. Verify that fallbacks work correctly and errors are logged appropriately.

### Integration Testing

Test error scenarios in integration tests. Verify that errors propagate correctly through your system. Test that global error handlers format errors appropriately and that infrastructure errors are handled gracefully.

Test graceful degradation. Verify that your bot continues operating when some services fail. Test that cached data is used when APIs are unavailable and that operations queue correctly when databases are down.

## Performance Considerations

### Avoid Expensive Operations in Error Paths

Don't do expensive computations in error handling code. Error paths should be fast—they're already handling failures, so don't make them slow too. Pre-compute expensive values before operations, or use lazy evaluation.

If you need expensive data for error logging, compute it before the operation starts. That way, if the operation fails, you already have the data for logging. Don't compute it only when errors occur—that makes error handling slow.

Use lightweight error information. Include IDs, names, and simple values in error logs. Don't serialize large objects or compute complex summaries in error handlers. Keep error handling fast so it doesn't slow down your bot.

### Exception Creation Cost

Create exceptions only when needed. Don't create exceptions during validation—collect validation errors and create a single exception at the end. This avoids the overhead of exception creation for common validation failures.

Use exception chaining efficiently. Don't create multiple exception objects unnecessarily. Chain exceptions properly to preserve context without creating redundant exception objects.

## Anti-Patterns

### Silent Failures

Never silently swallow exceptions. At minimum, log exceptions with context. Silent failures make debugging impossible—you don't know what went wrong or where. Always log exceptions, even if you handle them gracefully.

If you must handle exceptions silently, log them at debug level. This preserves information for debugging while not cluttering error logs. But prefer explicit error handling—silent failures are usually bugs waiting to happen.

### Re-raising with Generic Exceptions

Don't lose exception context when re-raising. Always use `raise ... from e` to chain exceptions. Generic re-raising loses the original error context, making debugging much harder.

Preserve exception chains throughout your code. When you catch an exception and raise a new one, chain them properly. This shows the full error path from original cause to final error.

### Overly Broad Exception Handling

Don't catch `Exception` unless you're at the top level of error handling. Catching `Exception` catches everything, including `KeyboardInterrupt` and `SystemExit`, which should propagate. Catch specific exceptions where you can handle them meaningfully.

Handle exceptions at the right level. Catch specific exceptions where you can handle them. Let exceptions propagate to handlers that can actually deal with them. Don't catch exceptions just to log them—let them propagate to appropriate handlers.

## Error Monitoring

### Sentry Integration

Tux provides specialized Sentry utilities for different error types. Use `capture_database_error()` for database failures, `capture_api_error()` for API failures, and `capture_cog_error()` for cog errors. These utilities automatically add relevant context.

Use specialized capture functions instead of generic `capture_exception()`. They add domain-specific context automatically, making errors easier to debug. Database errors include query details, API errors include endpoint information, and cog errors include command context.

Set context before operations, not after. If you set context after an error occurs, you'll miss valuable debugging information. Set user context, command context, and custom tags before doing work, so they're available when errors occur.

### Error Metrics

Track error patterns to identify problematic areas. Monitor error rates by command, by module, and by error type. This helps you identify which parts of your bot are most error-prone and prioritize fixes.

Set up alerts for critical errors. When database connections fail or configuration errors occur, you need to know immediately. Don't wait for users to report problems—monitor error rates and alert on anomalies.

Monitor user-facing error frequency. If users see many errors, investigate why. User-facing errors indicate problems that need immediate attention. Track these separately from internal errors that don't affect users.

## Best Practices Summary

### Code Structure

Handle errors at the right level. Catch specific exceptions where you can handle them meaningfully. Let exceptions propagate to global handlers when you can't handle them locally. Don't catch exceptions just to log them.

Use Tux-specific exceptions instead of generic ones. They provide better error categorization and let handlers format errors appropriately. Generic exceptions force handlers to guess what went wrong.

Chain exceptions properly with `raise ... from e`. This preserves error context and makes debugging easier. Don't lose exception chains when re-raising.

### User Experience

Provide helpful error messages. Users should understand what went wrong and how to fix it. Don't show technical errors to users—convert them to friendly messages.

Handle errors gracefully. Don't crash on recoverable errors. Use fallbacks, cached data, or reduced functionality to keep your bot operating even when some services fail.

Log errors aggressively with context. Include user IDs, command names, operation types, and relevant parameters. This context is essential for debugging production issues.

### Performance

Avoid expensive operations in error paths. Error handling should be fast—don't make failures slow. Pre-compute expensive values or use lazy evaluation.

Create exceptions only when needed. Don't create exceptions during validation—collect errors and create a single exception at the end. This avoids overhead for common validation failures.

## Resources

- **Python Exception Handling**: Python's official documentation on exception handling
- **Tux Exception Hierarchy**: See `src/tux/shared/exceptions.py` for all Tux-specific exceptions
- **Global Error Handler**: See `src/tux/services/handlers/error/cog.py` for error handling implementation
- **Sentry Integration**: See `sentry.md` for error tracking and monitoring details
