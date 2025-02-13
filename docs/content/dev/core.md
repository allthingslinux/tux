# Core Components

This document covers the core components of Tux bot, including the main entry point, bot class, and cog loading system.

## Overview

The core of Tux consists of three main components:

1. `main.py` - Entry point and initialization
2. `bot.py` - Core bot implementation and lifecycle management
3. `cog_loader.py` - Extension and cog management system

## Main Entry Point (main.py)

The [`main.py`](https://github.com/allthingslinux/tux/blob/main/main.py) module serves as the primary entry point for the Tux bot. It handles:

- Initial logging setup
- Sentry integration for error tracking
- Bot configuration and initialization
- Graceful shutdown procedures

### Key Components

#### Command Prefix Management

```python
async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
```

Dynamically retrieves command prefixes for guilds, falling back to the default prefix if needed.

#### Sentry Integration

```python
def setup_sentry() -> None:
```

Configures Sentry for error tracking and monitoring with:

- Environment-based configuration
- Full tracing and profiling
- Asyncio and Loguru integrations

#### Main Loop

```python
async def main() -> None:
```

Manages the complete bot lifecycle:

1. Configuration validation
2. Sentry setup
3. Signal handlers
4. Bot initialization
5. Error handling
6. Graceful shutdown

## Bot Implementation (bot.py)

The [`bot.py`](https://github.com/allthingslinux/tux/blob/main/bot.py) module contains the main `Tux` class, which extends `discord.ext.commands.Bot` with additional functionality.

### Key Features

#### Task Management System

The bot implements a sophisticated task monitoring and management system:

```python
@discord_tasks.loop(seconds=60)
async def _monitor_tasks(self) -> None:
```

Key capabilities:

- Comprehensive task monitoring and categorization
- Automatic detection of stuck tasks
- Performance tracking and metrics
- Task state monitoring and cleanup
- Detailed logging and metrics collection
- Graceful task cleanup during shutdown

#### Lifecycle Management

The bot implements several key lifecycle stages:

1. **Initialization**
   - Core state setup
   - Task management initialization
   - Console configuration

2. **Setup Process**

```python
async def setup(self) -> None:
```

Handles core initialization including:

- Database connection
- Extension loading
- Task monitoring startup

3. **Shutdown Process**

```python
async def shutdown(self) -> None:
```

Implements graceful shutdown sequence:

- Setup task cleanup
- Running task cancellation
- Connection closure
- Resource cleanup

## Cog Loading System (cog_loader.py)

The `cog_loader.py` module provides a robust system for loading and managing bot extensions (cogs).

### Key Features - Cog Loading

#### Priority-based Loading

Cogs are loaded based on a priority system:

```python
load_priorities = {
    "handlers": 100,
    "services": 90,
    "admin": 80,
    # ...
}
```

#### Concurrent Loading

- Cogs are loaded concurrently within priority groups
- Performance monitoring for load times
- Automatic detection of slow-loading cogs

### Key Methods

#### Cog Eligibility

```python
async def is_cog_eligible(self, filepath: Path) -> bool:
```

Determines if a file is a valid cog based on:

- File extension
- Naming conventions
- Ignore list status

#### Cog Loading

```python
async def load_cogs(self, path: Path) -> None:
```

Recursively loads cogs with:

- Priority-based ordering
- Concurrent loading within priority groups
- Performance tracking
- Error handling

### Error Handling

The system includes comprehensive error handling through the `CogLoadError` class:

- Detailed error messages
- Stack trace preservation
- Logging integration

## Best Practices

When working with these core components:

1. **Error Handling**
   - Always use the provided error classes
   - Ensure errors are properly logged
   - Maintain the error hierarchy

2. **Task Management**
   - Monitor task lifetimes
   - Clean up resources properly
   - Use appropriate task priorities

3. **Extension Development**
   - Follow the priority system
   - Implement proper cleanup methods
   - Use the provided logging system

4. **Shutdown Handling**
   - Implement cleanup methods
   - Handle cancellation gracefully
   - Close resources properly

## Configuration

Core components are configured through environment variables and the `CONFIG` object. Key configuration options include:

- `TOKEN` - Bot authentication token
- `SENTRY_URL` - Sentry DSN for error tracking
- `DEFAULT_PREFIX` - Default command prefix
- `COG_IGNORE_LIST` - Cogs to exclude from loading

## Logging and Error Tracking

### Logging System

The system uses Loguru for logging with:

- Structured logging format
- Level-based filtering
- Sentry integration
- Performance metrics

### Error Tracking

Error tracking is handled through Sentry with:

- Environment-based configuration
- Full tracing support
- Performance profiling
- Asyncio integration
