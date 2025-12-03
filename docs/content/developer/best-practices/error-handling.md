---
title: Error Handling Best Practices
description: Error handling best practices for Tux development, including exception patterns, graceful degradation, and debugging techniques.
tags:
  - developer-guide
  - best-practices
  - error-handling
---

# Error Handling Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Error handling is crucial for building reliable Discord bots. Users expect your bot to handle failures gracefully, provide helpful feedback, and continue operating even when things go wrong. Good error handling separates professional bots from fragile ones.

## Errors vs Exceptions in Python

Understanding the difference between errors and exceptions helps you handle them appropriately:

**Errors** are fundamental coding mistakes that prevent a program from running altogether. Errors are commonly detected during compilation, and the code won't execute until they are fixed. Examples include syntax errors and indentation errors.

**Exceptions** are a subcategory of errors that occur during program execution (runtime) when your code encounters an unexpected situation, such as trying to divide by zero or accessing a non-existent dictionary key. Unlike errors, exceptions can be caught and handled within your code.

```python
# Error: Syntax error - prevents execution
print("Hello World"  # Missing closing parenthesis

# Exception: Runtime error - can be handled
result = 10 / 0  # Raises ZeroDivisionError - can be caught
```

In Tux, we focus on handling exceptions gracefully while preventing errors through proper code review and linting.

## Common Python Exceptions

Python provides built-in exception classes for different error scenarios. Understanding these helps you catch and handle them appropriately:

### Type and Value Exceptions

- **`TypeError`**: Raised when an operation is performed on incompatible types

  ```python
  print("10" + 5)  # Raises TypeError
  ```

- **`ValueError`**: Occurs when a function receives an argument with an unsuitable value

  ```python
  num = int("abc")  # Raises ValueError
  ```

### Data Structure Exceptions

- **`KeyError`**: Raised when trying to access a non-existent dictionary key

  ```python
  data = {"name": "Alice"}
  print(data["age"])  # Raises KeyError
  ```

- **`IndexError`**: Occurs when accessing an out-of-range index

  ```python
  numbers = [1, 2, 3]
  print(numbers[5])  # Raises IndexError
  ```

### Mathematical Exceptions

- **`ZeroDivisionError`**: Triggered when attempting to divide by zero

  ```python
  result = 10 / 0  # Raises ZeroDivisionError
  ```

- **`OverflowError`**: Triggered when the resulting value exceeds the allowed number range

### File Operation Exceptions

- **`FileNotFoundError`**: Raised when attempting to access a non-existent file

  ```python
  with open("missing_file.txt", "r") as file:
      content = file.read()  # Raises FileNotFoundError
  ```

- **`IOError`**: Raised when an I/O operation fails (file operations, network operations)
- **`PermissionError`**: Raised when trying to perform an operation without adequate permissions

### Import and Module Exceptions

- **`ImportError`**: Raised when importing a module fails
- **`ModuleNotFoundError`**: Raised when a module cannot be found (subclass of `ImportError`)

### Runtime Exceptions

- **`RuntimeError`**: Raised when an error doesn't fall into any specific category
- **`AttributeError`**: Raised when attribute assignment or reference fails
- **`AssertionError`**: Raised when an `assert` statement fails

### System Exceptions

- **`KeyboardInterrupt`**: Raised when the user presses interrupt keys (Ctrl+C or Delete)
- **`SystemExit`**: Raised when `sys.exit()` is called
- **`MemoryError`**: Raised when programs run out of memory

!!! note "System Exceptions"
    `KeyboardInterrupt` and `SystemExit` inherit from `BaseException`, not `Exception`.
    They should generally be allowed to propagate for proper program shutdown.
    See the section on [The Critical Difference: `except:` vs `except Exception:`](#the-critical-difference-except-vs-except-exception) for more details.

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

### Keep Try Blocks Focused

The scope of your `try` blocks directly impacts how effectively you can diagnose and fix issues. Large, encompassing `try` blocks often mask the true source of errors and make debugging significantly more challenging.

#### Problem: Large try blocks

```python
# ❌ BAD: Too broad, impossible to determine which operation failed
try:
    user = await db.get_user(user_id)
    profile = await process_user_data(user)
    await send_notification(profile)
except Exception as e:
    logger.error(f"Operation failed: {e}")
    # Which operation failed? Database? Processing? Notification?
```

#### Solution: Focused try blocks

```python
# ✅ GOOD: Each operation has its own error boundary
try:
    user = await db.get_user(user_id)
except TuxDatabaseConnectionError as e:
    logger.error(f"Database connection failed: {e}")
    return None

try:
    profile = await process_user_data(user)
except TuxValidationError as e:
    logger.error(f"User data invalid: {e}")
    return None

try:
    await send_notification(profile)
except TuxAPIConnectionError as e:
    logger.error(f"Notification delivery failed: {e}")
    # Continue execution - notification failure shouldn't stop the command
```

**Benefits of focused try blocks:**

- **Clear error source**: You immediately know which operation failed
- **Operation-specific context**: Error messages contain relevant details
- **Appropriate handling**: Different failures can be handled differently
- **Easier debugging**: The error source is immediately apparent
- **Specific recovery**: Each operation can implement its own recovery strategy

**When to use focused try blocks:**

- When operations have different failure modes
- When you need different error handling for each operation
- When you want to continue execution after some failures
- When debugging production issues (focused blocks make diagnosis easier)

The extra code is a worthwhile trade-off for the clarity and control it provides. While it might seem verbose, this pattern becomes invaluable as applications grow in complexity and when debugging production issues.

### The Critical Difference: `except:` vs `except Exception:`

!!! danger "Critical Distinction"
    **Never use bare `except:`** - it catches system exceptions that should propagate.

There's an important difference between `except:` and `except Exception:`:

**`except:` (bare except) - Catches EVERYTHING:**

- Catches all exceptions, including `KeyboardInterrupt` (Ctrl+C) and `SystemExit` (sys.exit())
- These system exceptions should normally propagate to allow proper shutdown
- **Avoid this pattern** unless you have a very specific reason (like a top-level error handler in a web service)

**`except Exception:` - Catches user exceptions only:**

- Catches exceptions that inherit from `Exception`
- Does NOT catch `KeyboardInterrupt` or `SystemExit` (they inherit from `BaseException`)
- **Use this** when you need to catch all user exceptions but allow system signals to propagate

**Exception Hierarchy:**

```python
BaseException
├── KeyboardInterrupt  # Ctrl+C - should propagate
├── SystemExit         # sys.exit() - should propagate
└── Exception          # User exceptions - can be caught
    ├── ValueError
    ├── TypeError
    ├── TuxError
    └── ... (all other exceptions)
```

**Example of the problem:**

```python
# ❌ BAD: Bare except catches KeyboardInterrupt
try:
    process_data()
except:  # This catches Ctrl+C!
    logger.error("Error occurred")
    # User can't interrupt the program with Ctrl+C

# ✅ GOOD: except Exception allows KeyboardInterrupt to propagate
try:
    process_data()
except Exception as e:  # KeyboardInterrupt will propagate
    logger.error(f"Error occurred: {e}")
```

**When to use each:**

- **`except Exception:`** - Use when you need to catch all user exceptions (e.g., top-level error handlers, cleanup code)
- **`except:` (bare)** - Only use in very specific cases like web service error handlers where you must catch everything to prevent crashes
- **Specific exceptions** - Always prefer catching specific exception types when possible

**Best practice:** Always use `except Exception:` instead of bare `except:` unless you have a compelling reason to catch system exceptions.

Chain exceptions properly. When you catch an exception and raise a new one, use `raise ... from e` to preserve the chain. This shows the full error path from original cause to final error, making debugging much easier.

## Exception Re-Raising Patterns

Python provides several patterns for re-raising exceptions, each with different behaviors regarding traceback preservation. Understanding these patterns helps you choose the right approach for each situation.

### Pattern 1: Bare `raise` (Re-raise Same Exception)

**Use when:** You want to log or perform cleanup, then re-raise the same exception with its original traceback.

```python
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Validation failed: {e}")
    raise  # Re-raises the same exception with original traceback
```

**Characteristics:**

- Preserves the original exception type and traceback
- Shows exactly where the original error occurred
- Good default pattern for logging before re-raising

**Note:** `raise e` is almost equivalent to bare `raise`, but bare `raise` is preferred as it's more explicit about preserving the traceback.

### Pattern 2: Raise New Exception (Without `from`)

**Use when:** You want to raise a different exception type but still preserve the original traceback context.

```python
try:
    result = divide(x, y)
except ZeroDivisionError:
    raise ValueError("Division by zero is not allowed")
```

**Characteristics:**

- Raises a new exception type with a custom message
- Still includes the original exception's traceback in the output
- The original exception is available but not explicitly chained

**When to avoid:** When you need explicit exception chaining (use Pattern 4 instead).

### Pattern 3: Raise New Exception `from None`

**Use when:** You want to hide the original exception's traceback for security or abstraction reasons.

```python
try:
    result = authenticate_user(email, password)
except InvalidCredentialsError:
    raise AuthenticationError("Invalid credentials") from None
```

**Characteristics:**

- Suppresses the original exception's traceback
- Only shows the new exception in the traceback
- Useful for hiding implementation details or sensitive information

**Security use case:** When the original exception might leak sensitive information:

```python
try:
    user = login(email="user@example.com", password="secret")
except InvalidPasswordFormatError:
    # Don't expose password format details to potential attackers
    raise AuthenticationError("Authentication failed") from None
```

**When to avoid:** When you need the original traceback for debugging (use Pattern 4 instead).

### Pattern 4: Exception Chaining (`from e`) - **Recommended**

**Use when:** You want to raise a new exception type while preserving the original exception as the cause.

```python
try:
    result = divide(x, y)
except ZeroDivisionError as e:
    raise ValueError("Division by zero is not allowed") from e
```

**Characteristics:**

- Explicitly chains the original exception as the cause
- Shows both exceptions in the traceback
- Allows access to original exception via `e.__cause__`
- **Best practice** for raising new exceptions from caught ones

**Example with custom exceptions:**

```python
try:
    content = read_file(file_path)
except FileNotFoundError as e:
    raise TuxAPIResourceNotFoundError(
        service_name="FileSystem",
        resource_identifier=file_path,
    ) from e
```

**When to use:**

- Converting library exceptions to your own exception types
- Providing more context while preserving original error
- Debugging scenarios where you need the full error chain

### Pattern Comparison

| Pattern | Preserves Original Traceback | Shows Both Exceptions | Use Case |
|---------|------------------------------|----------------------|----------|
| Bare `raise` | ✅ Yes | N/A (same exception) | Logging before re-raising |
| Raise new (no `from`) | ✅ Yes | ⚠️ Implicit | Changing exception type |
| `from None` | ❌ No | ❌ No | Security/abstraction |
| `from e` | ✅ Yes | ✅ Yes | **Best practice** |

### Exception Re-Raising Best Practices

1. **Use `from e` when raising a new exception** - This is the recommended pattern for preserving error context.

2. **Use bare `raise` for logging** - When you just need to log and re-raise the same exception.

3. **Use `from None` sparingly** - Only when you need to hide sensitive information or implementation details.

4. **Avoid Pattern 2** - Prefer Pattern 4 (`from e`) over raising new exceptions without `from`, as it's more explicit and informative.

5. **Don't suppress exceptions unnecessarily** - Suppressing exceptions makes debugging harder, so only use `from None` when absolutely necessary.

### Using try/except/else/finally Blocks

Python's exception handling supports four blocks that work together:

- **`try`**: Execute code that may raise an exception
- **`except`**: Catch and handle exceptions
- **`else`**: Execute code only if no exception occurs (optional)
- **`finally`**: Run code regardless of whether an exception was raised (always executes)

```python
try:
    file = open("example.txt", "r")
except FileNotFoundError:
    print("File not found!")
else:
    # Only executes if no exception occurred
    print("File opened successfully!")
    content = file.read()
    print(content)
    file.close()
finally:
    # Always executes, even if exception occurred
    print("End of file operation.")
```

Use `finally` blocks for cleanup operations that must always run, such as closing files, releasing locks, or cleaning up temporary resources.

### Catching Multiple Exceptions

You can catch multiple exception types by chaining `except` blocks or using a tuple:

```python
# Method 1: Tuple in single except block
try:
    x = int(input("Enter a number: "))
    print(10 / x)
except (ValueError, ZeroDivisionError) as e:
    print(f"Error: {e}")

# Method 2: Separate except blocks for different handling
try:
    x = int(input("Enter a number: "))
    print(10 / x)
except ValueError:
    print("Invalid input! Please enter a number.")
except ZeroDivisionError:
    print("Cannot divide by zero!")
```

Use separate `except` blocks when you need different handling for each exception type. Use a tuple when the handling is the same.

### Nested try-except Blocks

Nested try-except blocks allow you to handle exceptions at different levels of code execution. This is useful when you need different error handling strategies for different parts of an operation:

```python
try:
    # Outer try block - handles high-level errors
    try:
        # Inner try block - handles specific operation errors
        file = open("data.txt", "r")
        content = file.read()
        file.close()
    except FileNotFoundError:
        # Handle file not found at the inner level
        logger.warning("Data file not found, using defaults")
        content = get_default_data()
    except PermissionError:
        # Handle permission errors at the inner level
        logger.error("Permission denied accessing data file")
        raise  # Re-raise to outer handler
except Exception as e:
    # Outer handler catches any unhandled errors
    logger.error(f"Unexpected error in data loading: {e}")
    capture_exception_safe(e)
    raise
```

In this example, `FileNotFoundError` is handled gracefully at the inner level with a fallback, while `PermissionError` is re-raised to the outer handler. The outer handler catches any unexpected exceptions and logs them to Sentry.

Use nested try-except blocks when:

- Different parts of an operation need different error handling
- You want to handle some errors locally and let others propagate
- You need to perform cleanup at different levels

### Using traceback for Detailed Error Information

The Python `traceback` module provides detailed information about exceptions, including the full call stack:

```python
import traceback

try:
    num = int("abc")
except ValueError as e:
    print("An error occurred!")
    traceback.print_exc()  # Prints full traceback information
```

In Tux, we use `traceback` in our error logging to provide complete context for debugging. The global error handler automatically includes tracebacks for errors sent to Sentry.

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

Convert HTTP exceptions to Tux exceptions. Use `convert_httpx_error()` to automatically convert `httpx` exceptions to `TuxAPIError` subclasses and report them to Sentry. This provides consistent error handling throughout your code and eliminates duplicated error handling logic.

```python
from tux.services.sentry import convert_httpx_error

try:
    response = await httpx.get(endpoint)
except Exception as e:
    convert_httpx_error(
        e,
        service_name="GitHub",
        endpoint="repos.get",
        not_found_resource=f"{owner}/{repo}",  # Optional: for 404 errors
    )
```

The `convert_httpx_error()` function automatically:

- Converts 404 errors to `TuxAPIResourceNotFoundError`
- Converts 403 errors to `TuxAPIPermissionError`
- Converts other HTTP status errors to `TuxAPIRequestError`
- Converts connection errors to `TuxAPIConnectionError`
- Reports all errors to Sentry with appropriate context

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

## Handling Exceptions in Loops

When processing multiple items in a loop, handle exceptions for each iteration independently. This prevents a single failure from stopping the entire loop:

```python
users = [1, 2, 3, 4, 5]
results = []

for user_id in users:
    try:
        user = await db.get_user(user_id)
        results.append(user)
    except TuxAPIResourceNotFoundError:
        logger.warning(f"User {user_id} not found, skipping")
        # Continue to next iteration
    except Exception as e:
        logger.error(f"Unexpected error fetching user {user_id}: {e}")
        capture_exception_safe(e)
        # Continue to next iteration - don't let one failure stop the loop

logger.info(f"Successfully processed {len(results)}/{len(users)} users")
```

**Key principles for loop exception handling:**

- **Catch specific exceptions** for expected failures (like missing resources)
- **Log and continue** for recoverable errors
- **Track successes and failures** separately to understand overall health
- **Don't let one failure stop the entire batch** unless it's critical

For batch operations, consider collecting exceptions and processing them after the loop completes:

```python
users = [1, 2, 3, 4, 5]
successes = []
failures = []

for user_id in users:
    try:
        user = await db.get_user(user_id)
        successes.append(user)
    except Exception as e:
        failures.append((user_id, e))
        logger.error(f"Failed to fetch user {user_id}: {e}")

logger.info(f"Batch complete: {len(successes)} succeeded, {len(failures)} failed")
if failures:
    # Process failures separately
    for user_id, error in failures:
        capture_exception_safe(error, extra_context={"user_id": user_id})
```

## Async Error Handling

### Task Exception Handling

When running multiple operations concurrently, handle exceptions in each task independently. Use `asyncio.gather()` with `return_exceptions=True` to collect exceptions as results instead of stopping at the first failure.

Process results after gathering completes. Check each result to see if it's an exception or a value. Handle exceptions appropriately—log them, retry operations, or collect them for batch processing. Successful operations shouldn't be affected by failures in other operations.

For batch operations, track successes and failures separately. Log summary information about how many operations succeeded and failed. This helps you understand the overall health of batch operations and identify patterns in failures.

### Timeout Handling

Always use timeouts for long-running operations. Don't let operations hang indefinitely. Set reasonable timeouts based on expected operation duration. If operations consistently timeout, investigate why they're slow.

When timeouts occur, cancel the operation and handle the cancellation gracefully. Log timeout information to help identify slow operations. Consider whether timeouts indicate problems that need fixing or just slow external services.

Use `asyncio.wait_for()` for timeout handling. This automatically cancels operations that exceed their timeout. Handle `TimeoutError` appropriately—retry, use fallbacks, or fail gracefully with clear error messages.

#### Example: Handling Exceptions in Async Functions

```python
import asyncio

async def fetch_user_data(user_id: int):
    """Fetch user data from an external API."""
    try:
        response = await httpx.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise TuxAPIResourceNotFoundError(
                service_name="ExampleAPI",
                resource_identifier=f"user_{user_id}",
            ) from e
        raise TuxAPIRequestError(
            service_name="ExampleAPI",
            status_code=e.response.status_code,
        ) from e
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(
            service_name="ExampleAPI",
            original_error=e,
        ) from e

async def main():
    try:
        user_data = await fetch_user_data(123)
        print(f"User: {user_data}")
    except TuxAPIResourceNotFoundError:
        logger.warning("User not found")
    except TuxAPIConnectionError as e:
        logger.error(f"Connection error: {e}")
        capture_exception_safe(e)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        capture_exception_safe(e)

asyncio.run(main())
```

**Important notes for async exception handling:**

- **Always await async functions** - calling without `await` returns a coroutine object, not the result
- **Handle `asyncio.CancelledError` carefully** - don't catch it unless you're handling cancellation specifically
- **Use `asyncio.gather()` with `return_exceptions=True`** for concurrent operations where you want all results, even if some fail

## Context Managers for Error Handling

Context managers in Python shine when it comes to resource management.
While they're commonly associated with file operations, their scope extends far beyond basic file handling.
The real power of context managers lies in their ability to handle setup and cleanup operations automatically,
whether your code executes successfully or raises an exception.

### When to Use Context Managers

Context managers are particularly crucial when dealing with:

- **Database connections and transactions** - Ensure connections are closed and transactions are committed or rolled back
- **Network sockets and API sessions** - Close connections even when errors occur
- **Memory-intensive operations** - Release resources promptly
- **Thread locks and semaphores** - Ensure locks are released
- **Temporary file management** - Clean up temporary files automatically

### Database Transactions

Use context managers for database transactions. They ensure transactions are committed on success and rolled back on failure. This keeps your database consistent and prevents partial updates.

#### Example: Custom Transaction Context Manager

```python
from contextlib import contextmanager

@contextmanager
def db_transaction(db_service):
    """Context manager for database transactions."""
    async with db_service.session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # Connection automatically closed by session context manager
```

**Usage:**

```python
async def update_user_profile(user_id: int, data: dict) -> None:
    async with db_transaction(db_service) as session:
        user = await session.get(User, user_id)
        if user:
            user.profile = data
            # Auto-committed on success, rolled back on exception
```

**Benefits:**

- Automatic commit on success
- Automatic rollback on failure
- Connection cleanup guaranteed
- No manual transaction management needed

Log transaction outcomes appropriately. Log successful commits at debug level. Log rollbacks at warning level with error details. This helps you understand transaction patterns and identify problematic operations.

### Resource Cleanup

Use context managers for all resources that need cleanup—files, network connections, temporary data. Context managers ensure cleanup happens even when exceptions occur. Don't rely on manual cleanup in finally blocks—use context managers instead.

#### Example: File Operations

```python
# ✅ GOOD: Context manager ensures file is closed
with open("data.txt", "r") as file:
    content = file.read()
    # File automatically closed, even if an exception occurs

# ❌ BAD: Manual cleanup can be forgotten
file = open("data.txt", "r")
try:
    content = file.read()
finally:
    file.close()  # Easy to forget or miss in complex code
```

#### Example: Custom Resource Context Manager

```python
from contextlib import contextmanager

@contextmanager
def temporary_cache():
    """Context manager for temporary cache operations."""
    cache = {}
    try:
        yield cache
    finally:
        cache.clear()  # Always cleanup, even on exceptions

# Usage
with temporary_cache() as cache:
    cache["key"] = "value"
    # Cache automatically cleared when exiting
```

**Best practices:**

- **Identify paired operations**: Look for operations that require setup and cleanup
- **Reserve for resource management**: Not every operation needs a context manager
- **Use for guaranteed cleanup**: When cleanup must happen regardless of success or failure
- **Centralize logic**: Context managers centralize setup and cleanup logic, making code more maintainable

Context managers particularly excel in production environments where resource leaks can cause significant issues. They enforce clean resource management patterns and make code more maintainable by centralizing setup and cleanup logic.

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

## Security: Protecting Sensitive Data

!!! danger "Critical Security Concern"
    **Never log passwords, API keys, tokens, or other sensitive information in error messages or logs.**

### The Problem

When exceptions occur, error messages and stack traces may contain sensitive data that gets logged or sent to error monitoring services. This can expose:

- Database connection strings with passwords
- API keys in URLs or request headers
- Authentication tokens
- User credentials
- Secret keys

### The Solution

Tux automatically sanitizes sensitive data before sending events to Sentry. Our `before_send` handler removes or masks:

- Database URLs: `postgresql://user:password@host` → `postgresql://***:***@host`
- API keys in URLs: `?api_key=xxx` → `?***`
- Bearer tokens: `Bearer xxxxx` → `Bearer ***`
- Authorization headers: `Authorization: xxxxx` → `Authorization: ***`

### Best Practices

1. **Never include secrets in error messages**: When raising exceptions, don't include sensitive data in the message string.

   ```python
   # BAD: Exposes API key in error message
   raise ValueError(f"API call failed with key {api_key}")

   # GOOD: Generic error message
   raise ValueError("API call failed - check configuration")
   ```

2. **Sanitize before logging**: If you must log data that might contain secrets, sanitize it first.

   ```python
   # BAD: Logs full URL with API key
   logger.error(f"Request failed: {request_url}")

   # GOOD: Sanitize sensitive parts
   sanitized_url = _sanitize_url(request_url)
   logger.error(f"Request failed: {sanitized_url}")
   ```

3. **Use environment variables**: Store secrets in environment variables, never in code or error messages.

4. **Validate error context**: Before adding context to Sentry events, ensure it doesn't contain sensitive data.

### Example: Secure Error Handling

```python
import os
import httpx

api_key = os.getenv("SECRET_API_KEY")

try:
    response = httpx.get(f"https://api.example.com/data?key={api_key}")
    response.raise_for_status()
except httpx.HTTPError as e:
    # BAD: This would log the API key
    # logger.error(f"API request failed: {e}")
    
    # GOOD: Generic error message
    logger.error("API request failed - check connection and configuration")
    capture_api_error(e, endpoint="api.example.com/data")
    # Note: Our Sentry handler automatically sanitizes any sensitive data
```

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

Tux provides specialized Sentry utilities for different error types:

- `capture_database_error()` - For database failures
- `convert_httpx_error()` - For HTTPX API failures (recommended for API wrappers)
- `capture_api_error()` - For other API failures
- `capture_cog_error()` - For cog errors

These utilities automatically add relevant context.

Use specialized capture functions instead of generic `capture_exception()`. They add domain-specific context automatically, making errors easier to debug. Database errors include query details, API errors include endpoint information, and cog errors include command context.

Set context before operations, not after. If you set context after an error occurs, you'll miss valuable debugging information. Set user context, command context, and custom tags before doing work, so they're available when errors occur.

### Error Metrics

Track error patterns to identify problematic areas. Monitor error rates by command, by module, and by error type. This helps you identify which parts of your bot are most error-prone and prioritize fixes.

Set up alerts for critical errors. When database connections fail or configuration errors occur, you need to know immediately. Don't wait for users to report problems—monitor error rates and alert on anomalies.

Monitor user-facing error frequency. If users see many errors, investigate why. User-facing errors indicate problems that need immediate attention. Track these separately from internal errors that don't affect users.

## Why Exception Handling Matters

Effective error and exception handling is essential for building robust applications. Here's why:

### 1. Prevents Unexpected Program Crashes

When an unhandled exception occurs, Python terminates the program immediately. By handling exceptions, you prevent crashes and provide graceful recovery mechanisms. Your bot continues operating even when individual operations fail.

### 2. Provides Meaningful Feedback to Users

Displaying informative error messages helps users understand what went wrong and how to correct their input or actions. Instead of showing cryptic tracebacks, users get clear, actionable messages.

### 3. Simplifies Debugging and Enables Detailed Logging

Exception handling allows you to log errors for later analysis, helping pinpoint the source of issues. Logging is especially useful for debugging applications running in production, where you can't interactively debug the code.

### 4. Ensures Proper Cleanup of Resources

Handling exceptions properly ensures that resources like open files, database connections, and network sockets are properly closed, preventing memory leaks and data corruption. Use context managers (`with` statements) to ensure cleanup happens automatically.

### 5. Reduces Security Vulnerabilities

Proper exception handling prevents sensitive information from being exposed in error messages. Never log passwords, API keys, tokens, or other secrets. Our Sentry integration automatically sanitizes sensitive data before sending events.

## Code Quality Tools

### Linting Your Code

Tools like `ruff` and `basedpyright` can help detect syntax and indentation issues before execution. These work similarly to a spell checker for your code, helping you catch errors early before they cause runtime issues.

Tux uses:

- **`ruff`**: Fast Python linter and formatter
- **`basedpyright`**: Static type checker with strict mode

Run quality checks before committing:

```bash
uv run dev all  # Runs all quality checks including linting
```

## Best Practices Summary

### Code Structure

Handle errors at the right level. Catch specific exceptions where you can handle them meaningfully. Let exceptions propagate to global handlers when you can't handle them locally. Don't catch exceptions just to log them.

Use Tux-specific exceptions instead of generic ones. They provide better error categorization and let handlers format errors appropriately. Generic exceptions force handlers to guess what went wrong.

Chain exceptions properly with `raise ... from e`. This preserves error context and makes debugging easier. Don't lose exception chains when re-raising.

Use `try/except/else/finally` blocks appropriately. Use `finally` for cleanup that must always run. Use `else` for code that should only run when no exception occurs.

### User Experience

Provide helpful error messages. Users should understand what went wrong and how to fix it. Don't show technical errors to users—convert them to friendly messages.

Handle errors gracefully. Don't crash on recoverable errors. Use fallbacks, cached data, or reduced functionality to keep your bot operating even when some services fail.

Log errors aggressively with context. Include user IDs, command names, operation types, and relevant parameters. This context is essential for debugging production issues.

**Strategic logging principles:**

- **Log levels that mean something**: Use `DEBUG` for detailed execution flow, `INFO` for normal operations, `WARNING` for recoverable issues, `ERROR` for failures that need attention, `CRITICAL` only for failures that stop core functionality
- **Contextual information**: Include user IDs, command names, operation types, and relevant parameters that help reconstruct the error state
- **Stack traces when they matter**: Use `logger.exception()` or `logger.error(..., exc_info=True)` for exceptions, but only when the full traceback is needed
- **Structured logging in production**: Use structured logging formats (JSON) for easier parsing and analysis
- **Log rotation**: Manage log storage efficiently to prevent disk space issues

#### Example: Comprehensive Error Logging

```python
from loguru import logger
from tux.services.sentry import capture_exception_safe

async def process_command(ctx, user_id: int, data: dict) -> None:
    logger.info(f"Processing command for user {user_id}", extra={
        "user_id": user_id,
        "command": ctx.command.name,
        "guild_id": ctx.guild.id if ctx.guild else None,
    })
    
    try:
        result = await risky_operation(user_id, data)
        logger.debug(f"Operation successful for user {user_id}")
        return result
    except TuxValidationError as e:
        # User error - log as warning, don't send to Sentry
        logger.warning(f"Validation failed for user {user_id}: {e}", extra={
            "user_id": user_id,
            "error_type": type(e).__name__,
            "validation_field": getattr(e, "field", None),
        })
        raise
    except Exception as e:
        # System error - log as error, send to Sentry
        logger.error(
            f"Operation failed for user {user_id}: {e}",
            extra={
                "user_id": user_id,
                "command": ctx.command.name,
                "error_type": type(e).__name__,
            },
        )
        capture_exception_safe(e, extra_context={
            "user_id": user_id,
            "command": ctx.command.name,
        })
        raise
```

**What makes logging exceptional:**

- **Tells a story**: When an exception occurs, your logs should tell a story about what led to the failure
- **Track patterns**: Strategic logging helps track user behavior patterns, performance bottlenecks, and system health
- **Production debugging**: In production, logs are often your only window into what happened
- **Correlation**: Include correlation IDs or request IDs to trace operations across services

### Performance

Avoid expensive operations in error paths. Error handling should be fast—don't make failures slow. Pre-compute expensive values or use lazy evaluation.

Create exceptions only when needed. Don't create exceptions during validation—collect errors and create a single exception at the end. This avoids overhead for common validation failures.

### Documentation

Document expected exceptions in function docstrings. This helps other developers (and your future self) understand what exceptions a function can raise and how to handle them:

```python
async def fetch_user(user_id: int) -> User:
    """
    Fetch a user from the database.

    Parameters
    ----------
    user_id : int
        The ID of the user to fetch.

    Returns
    -------
    User
        The user object.

    Raises
    ------
    TuxAPIResourceNotFoundError
        If the user does not exist.
    TuxDatabaseConnectionError
        If the database connection fails.
    """
    # Implementation...
```

Clear documentation of expected exceptions:

- Helps callers write appropriate error handling
- Makes the API contract explicit
- Reduces guesswork about what can go wrong
- Improves code maintainability

Use NumPy-style docstrings (as shown above) to document exceptions in the `Raises` section. This is the standard format used throughout Tux.

## Modern Python Exception Handling Features

Tux uses Python 3.13+, which includes several modern exception handling features introduced in Python 3.10 and 3.11.

### Pattern Matching with `match` Statements (Python 3.10+)

Python 3.10 introduced structural pattern matching with `match` statements, which can elegantly handle multiple exception types:

```python
try:
    result = risky_operation()
except Exception as e:
    match e:
        case ZeroDivisionError():
            logger.error("Division by zero detected")
            raise ValueError("Cannot divide by zero") from e
        case FileNotFoundError():
            logger.warning("File not found, using defaults")
            result = get_default_data()
        case TuxAPIResourceNotFoundError():
            logger.warning(f"Resource not found: {e.resource_identifier}")
            raise
        case _:
            logger.error(f"Unexpected error: {e}")
            capture_exception_safe(e)
            raise
```

**Benefits:**

- More readable than multiple `elif isinstance()` checks
- Exhaustiveness checking (can use `case _:` as catch-all)
- Pattern matching on exception attributes

**When to use:**

- When handling multiple exception types with different logic
- When you want more readable exception handling
- When pattern matching on exception attributes

### Exception Groups and `except*` (Python 3.11+)

Python 3.11 introduced exception groups to handle multiple exceptions simultaneously, particularly useful for concurrent operations:

```python
from exceptiongroups import ExceptionGroup

try:
    # Multiple operations that might raise different exceptions
    results = await asyncio.gather(
        fetch_user_data(user_id),
        fetch_guild_data(guild_id),
        fetch_channel_data(channel_id),
        return_exceptions=True,
    )
    
    # Check for exceptions in results
    exceptions = [r for r in results if isinstance(r, Exception)]
    if exceptions:
        raise ExceptionGroup("Multiple fetch errors", exceptions)
        
except* TuxAPIResourceNotFoundError as eg:
    # Handle all resource not found errors
    for error in eg.exceptions:
        logger.warning(f"Resource not found: {error.resource_identifier}")
        
except* TuxAPIConnectionError as eg:
    # Handle all connection errors
    for error in eg.exceptions:
        logger.error(f"Connection error: {error}")
        capture_exception_safe(error)
        
except* Exception as eg:
    # Handle any other exceptions
    for error in eg.exceptions:
        logger.error(f"Unexpected error: {error}")
        capture_exception_safe(error)
```

**Benefits:**

- Handle multiple exceptions of the same type together
- Useful for concurrent operations (asyncio, threading)
- Cleaner than checking each result individually

**When to use:**

- Concurrent operations where multiple exceptions might occur
- Batch processing where you want to handle all errors together
- When you need to process all exceptions of a specific type

### Adding Notes to Exceptions (Python 3.11+)

Python 3.11 added the `add_note()` method to exceptions, allowing you to add contextual information:

```python
try:
    result = process_user_input(user_data)
except ValueError as e:
    e.add_note("This error occurred while processing user input")
    e.add_note("Consider validating input before processing")
    e.add_note(f"User ID: {user_data.get('id', 'unknown')}")
    logger.error(f"Validation error: {e}")
    raise
```

**Benefits:**

- Add context without modifying exception message
- Notes appear in traceback output
- Useful for debugging and error reporting

**When to use:**

- When you want to add debugging context to exceptions
- When re-raising exceptions with additional information
- When you need to preserve original exception message but add context

### Suppressing Exceptions with `contextlib.suppress`

Use `contextlib.suppress` to intentionally ignore specific exceptions:

```python
from contextlib import suppress

# Suppress FileNotFoundError when removing a file
with suppress(FileNotFoundError):
    os.remove("temp_file.txt")

# Suppress multiple exception types
with suppress(KeyError, AttributeError):
    value = data["key"].attribute
```

**Benefits:**

- Explicitly documents intent to ignore exceptions
- More readable than empty `except` blocks
- Type-safe exception suppression

**When to use:**

- Cleanup operations where exceptions are expected
- Optional operations that shouldn't fail the program
- When you want to explicitly document ignored exceptions

!!! warning "Use Sparingly"
    Only suppress exceptions when you're certain they're safe to ignore. Suppressing exceptions can hide bugs and make debugging difficult.

**Example from Tux codebase:**

```python
from contextlib import suppress

# Suppress CancelledError when cleaning up tasks
for task in tasks:
    if task.done():
        with suppress(asyncio.CancelledError):
            await task
```

## Creating Custom Exception Classes

You can define custom exception classes to extend Python's `Exception` class and handle specific cases in your application:

```python
class CustomError(Exception):
    """Custom exception for specific application errors."""
    pass

# Usage
if some_condition:
    raise CustomError("This is a custom exception!")
```

In Tux, we use a hierarchical exception system. All custom exceptions inherit from `TuxError`:

```python
from tux.shared.exceptions import TuxError

class MyCustomError(TuxError):
    """Custom error for my module."""
    pass
```

This allows the global error handler to format and handle your custom exceptions appropriately.

## Resources

- **Python Exception Handling**: [Python's official documentation](https://docs.python.org/3/tutorial/errors.html) on exception handling
- **Python traceback Module**: [traceback documentation](https://docs.python.org/3/library/traceback.html) for detailed error information
- **Tux Exception Hierarchy**: See `src/tux/shared/exceptions.py` for all Tux-specific exceptions
- **Global Error Handler**: See `src/tux/services/handlers/error/cog.py` for error handling implementation
- **Sentry Integration**: See `sentry/index.md` for error tracking and monitoring details
- **Security Best Practices**: See our [logging best practices](logging.md) for more on protecting sensitive data
