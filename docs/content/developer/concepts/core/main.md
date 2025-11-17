---
title: Main Entry Point
description: Tux Discord bot main entry point with error handling, logging configuration, and application lifecycle management.
---

# Main Entry Point

!!! wip "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The main entry point (`src/tux/main.py`) serves as Tux's primary application entry point, handling error management, logging configuration, and providing the synchronous interface to the asynchronous bot application.

## Overview

The main module provides a clean separation between the command-line interface and the core bot application, ensuring proper error handling and resource management at the application level.

## Entry Point Function

### Core Application Runner

```python
def run() -> int:
    """
    Instantiate and run the Tux application.

    This function is the entry point for the Tux application.
    It creates an instance of the TuxApp class.

    Returns
    -------
    int
        Exit code: 0 for success, non-zero for failure

    Notes
    -----
    Logging is configured by the CLI script (scripts/base.py) before this is called.
    """
    try:
        logger.info("🚀 Starting Tux...")
        app = TuxApp()
        return app.run()

    except (TuxDatabaseError, TuxError, SystemExit, KeyboardInterrupt, Exception) as e:
        # Handle all errors in one place
        if isinstance(e, TuxDatabaseError):
            logger.error("❌ Database connection failed")
            logger.info("💡 To start the database, run: make docker-up")
        elif isinstance(e, TuxError):
            logger.error(f"❌ Bot startup failed: {e}")
        elif isinstance(e, RuntimeError):
            logger.critical(f"❌ Application failed to start: {e}")
        elif isinstance(e, SystemExit):
            return int(e.code) if e.code is not None else 1
        elif isinstance(e, KeyboardInterrupt):
            logger.info("Shutdown requested by user")
            return 0
        else:
            logger.opt(exception=True).critical(f"Application failed to start: {e}")

        return 1

    else:
        return 0
```

### Error Handling Strategy

The entry point implements comprehensive error handling with specific responses for different error types:

**Database Errors:**

```python
if isinstance(e, TuxDatabaseError):
    logger.error("❌ Database connection failed")
    logger.info("💡 To start the database, run: make docker-up")
```

**Application Errors:**

```python
elif isinstance(e, TuxError):
    logger.error(f"❌ Bot startup failed: {e}")
```

**System Errors:**

```python
elif isinstance(e, RuntimeError):
    logger.critical(f"❌ Application failed to start: {e}")
```

**User Interrupts:**

```python
elif isinstance(e, KeyboardInterrupt):
    logger.info("Shutdown requested by user")
    return 0
```

### Exit Code Convention

**Standard Exit Codes:**

- **0** - Success (normal operation)
- **1** - Application error (startup failure, configuration error)
- **130** - User-requested shutdown (SIGINT/Ctrl+C)

## Module-Level Entry Point

### Direct Execution Support

```python
if __name__ == "__main__":
    exit_code = run()
    sys.exit(exit_code)
```

**Purpose:**

- Allows direct execution of the module with `python -m tux.main`
- Ensures proper exit code propagation to the shell
- Maintains compatibility with different execution methods

## Integration with CLI System

### CLI Script Delegation

The main module is typically invoked through the CLI system (`scripts/tux.py`):

```bash
# CLI invocation (recommended)
uv run tux start

# Direct module execution (fallback)
python -m tux.main
```

### Logging Configuration

**Logging Setup:**

- Logging is configured by the CLI script before `run()` is called
- Ensures consistent log formatting across all execution methods
- Supports different log levels (DEBUG, INFO, WARNING, ERROR)

## Error Classification

### Application-Level Errors

**Tux-Specific Errors:**

- `TuxDatabaseError` - Database connectivity and operations
- `TuxError` - General application errors
- Custom exceptions from the core application

**System Errors:**

- `SystemExit` - Explicit exit calls with codes
- `KeyboardInterrupt` - User interrupts (Ctrl+C)
- `RuntimeError` - Event loop and asyncio errors
- Generic `Exception` - Unexpected errors

### Error Response Strategy

**Recoverable Errors:**

- Database connection issues with helpful guidance
- Configuration problems with clear error messages
- User interrupts with graceful handling

**Critical Errors:**

- Runtime errors that prevent startup
- Unexpected exceptions with full stack traces
- System-level failures

## Startup Flow

### Application Lifecycle

```mermaid
graph TD
    A[CLI Script] --> B[Configure Logging]
    B --> C[Call run()]
    C --> D[Create TuxApp]
    D --> E[Run Application]
    E --> F{Exit Code}
    F --> G[Return to Shell]
```

**Sequence:**

1. **CLI Script** - Parse arguments and configure environment
2. **Logging Setup** - Initialize structured logging
3. **Entry Point** - Call `run()` function
4. **Application Creation** - Instantiate `TuxApp`
5. **Execution** - Run the bot application
6. **Exit Handling** - Process exit codes and errors

## Development Workflow

### Local Development

```bash
# Standard development startup
uv run tux start

# With debug logging
LOG_LEVEL=DEBUG uv run tux start

# Direct execution for testing
python -m tux.main
```

### Error Debugging

**Common Startup Issues:**

```bash
# Database connection failure
❌ "Database connection failed"
💡 To start the database, run: uv run docker-up

# Configuration error
❌ "Bot startup failed: Invalid token"
💡 Check BOT_TOKEN in .env file

# Runtime error
❌ "Application failed to start: Event loop stopped"
💡 Check for previous unclean shutdowns
```

**Debug Logging:**

```bash
# Enable detailed error logging
LOG_LEVEL=DEBUG uv run tux start 2>&1 | grep -E "(ERROR|CRITICAL|❌)"
```

### Testing Entry Point

```python
import sys
from tux.main import run

def test_entry_point():
    """Test the main entry point function."""
    # Test normal operation (will block until shutdown)
    try:
        exit_code = run()
        assert exit_code in [0, 130]  # Success or user shutdown
    except SystemExit as e:
        assert e.code in [0, 1, 130]  # Valid exit codes
```

## Best Practices

### Error Handling

1. **Centralized Error Processing** - All errors handled in one location
2. **User-Friendly Messages** - Clear error descriptions with actionable advice
3. **Proper Exit Codes** - Standard codes for shell integration
4. **Logging Consistency** - Structured logging with appropriate levels

### Application Structure

1. **Clean Separation** - Entry point separate from application logic
2. **Error Isolation** - Application errors don't crash the entry point
3. **Resource Management** - Proper cleanup on all exit paths
4. **Shell Integration** - Exit codes for scripting and automation

### Development Considerations

1. **Direct Execution** - Support for both CLI and direct module execution
2. **Logging Flexibility** - Configurable logging levels and formats
3. **Error Debugging** - Detailed error information for troubleshooting
4. **Testing Support** - Testable entry point for unit testing

## Troubleshooting

### Startup Failures

**Database Issues:**

```bash
# Check database container
uv run docker ps | grep postgres

# Test database connectivity
uv run tux db health

# Reset database if needed
uv run tux db reset
```

**Configuration Problems:**

```bash
# Validate configuration
uv run tux config validate

# Check environment variables
env | grep -E "(BOT_TOKEN|DATABASE)"
```

**Runtime Errors:**

```bash
# Check for syntax errors
python -m py_compile src/tux/main.py

# Test import
python -c "from tux.main import run; print('Import successful')"
```

### Exit Code Issues

**Unexpected Exit Codes:**

```bash
# Capture exit code
uv run tux start; echo "Exit code: $?"

# Debug with verbose output
uv run tux start --debug 2>&1 | tail -20
```

**Signal Handling:**

```bash
# Test SIGINT handling
timeout 5 uv run tux start; echo "Exit code: $?"

# Check signal processing
uv run tux start &
sleep 2
kill -INT $!
wait $!
echo "Exit code: $?"
```

## Resources

- **Source Code**: `src/tux/main.py`
- **CLI System**: `scripts/tux.py`
- **Application Layer**: `src/tux/core/app.py`
- **Error Handling**: See exception documentation
- **Logging**: See logging configuration documentation
