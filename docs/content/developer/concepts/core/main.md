---
title: Main Entry Point
description: Tux Discord bot main entry point with error handling, logging configuration, and application lifecycle management.
tags:
  - developer-guide
  - concepts
  - core
---

# Main Entry Point

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The main entry point (`src/tux/main.py`) serves as Tux's primary application entry point, handling error management, logging configuration, and providing the synchronous interface to the asynchronous bot application.

## Overview

The main module provides a clean separation between the command-line interface and the core bot application, ensuring proper error handling and resource management at the application level.

## Entry Point Function

### Core Application Runner

```python
def run() -> int:
    """Instantiate and run the Tux application."""
    # The debug flag is currently used for logging info if needed,
    # but actual logging is configured by the CLI script.
    app = TuxApp()
    return app.run()
```

### Error Handling Strategy

The application layer handles the lifecycle, and the entry point delegates execution to `TuxApp`. Most error handling and logging now occur at the appropriate service or orchestrator level.

**Database Errors:**

```python
if isinstance(e, TuxDatabaseError):
    logger.error("❌ Database connection failed")
    logger.info("💡 To start the database, run: docker compose up")
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

- **0** - Success (normal operation or graceful shutdown)
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

The main module is typically invoked through the CLI system (`scripts/tux/start.py`):

```bash
# CLI invocation (recommended)
uv run tux start

# Direct module execution (fallback)
python -m tux.main
```

### Logging Configuration

**Logging Setup:**

- Logging is configured in the CLI start script (`scripts/tux/start.py`) before `run()` is called
- As a defensive fallback, logging is also configured in `TuxApp.start()` before Sentry initialization
- Ensures consistent log formatting across all execution methods
- Supports different log levels via `--debug` flag, `LOG_LEVEL` environment variable, or `DEBUG=1` flag
- The `--debug` flag has highest priority and overrides environment variables

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
💡 To start the database, run: docker compose up

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
docker compose ps | grep postgres

# Test database connectivity
uv run db health

# Reset database if needed
uv run db reset
```

**Configuration Problems:**

```bash
# Validate configuration
uv run config validate

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
- **CLI System**: `scripts/tux/start.py`
- **Application Layer**: `src/tux/core/app.py`
- **CLI Core**: `scripts/core.py`
- **Error Handling**: See exception documentation
- **Logging**: See logging configuration documentation
