---
title: Cog Loader
description: Dynamic cog loading system with priority-based ordering, telemetry, and error handling for Tux Discord bot extensions.
tags:
  - developer-guide
  - concepts
  - core
  - cogs
---

# Cog Loader

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The Cog Loader (`src/tux/core/cog_loader.py`) handles discovery, validation, and loading of Discord bot cogs with priority-based ordering, comprehensive error handling, and performance monitoring.

## Overview

The Cog Loader provides sophisticated extension loading beyond discord.py's basic capabilities:

- **Priority-Based Loading** - Ensures proper dependency order during startup
- **Concurrent Group Loading** - Parallel loading within priority groups for speed
- **AST-Based Validation** - Static analysis to verify cog validity before loading
- **Graceful Error Handling** - Configuration errors skip gracefully, critical errors fail fast
- **Performance Monitoring** - Detailed timing metrics and slow cog detection
- **Sentry Integration** - Comprehensive telemetry for debugging and monitoring

## How Cog Loading Works

### Loading Flow

The cog loader follows this process:

1. **Discover Files** - Scans directories for Python files
2. **Validate Eligibility** - Checks files meet cog requirements
3. **Assign Priorities** - Determines loading order based on folder
4. **Group by Priority** - Organizes cogs into priority groups
5. **Load Sequentially by Group** - Loads groups in priority order
6. **Load Concurrently Within Group** - Parallel loading for performance

Groups load sequentially to ensure dependencies are satisfied, but cogs within each group load concurrently for maximum performance.

### Priority System

Cogs are organized into priority categories:

- **Handlers (Priority 100)** - Event handlers, error handlers, critical listeners
- **Services (Priority 75)** - Core services, database connections, managers
- **Modules (Priority 50)** - Bot commands, features, user-facing functionality
- **Plugins (Priority 25)** - User extensions, optional features

Higher priority cogs load first, ensuring dependencies are ready when lower priority cogs need them.

## Cog Discovery & Validation

### Eligibility Criteria

The loader validates files using multiple criteria:

1. **Configuration Ignore List** - Cogs explicitly disabled in configuration are skipped
2. **File Type** - Must be `.py` files, not directories or special files
3. **Naming Convention** - Private modules (starting with `_`) are skipped
4. **AST Validation** - Must contain valid `async def setup(bot)` function

### AST-Based Validation

The loader uses Python's AST (Abstract Syntax Tree) to statically analyze files before loading:

**Benefits:**

- **Static Analysis** - No execution required for validation
- **Syntax Error Detection** - Catches syntax errors before loading
- **Function Signature Verification** - Ensures proper `setup(bot)` signature
- **Performance** - Fast validation without module imports

This prevents loading invalid cogs and provides clear error messages when cogs don't meet requirements.

## Error Handling

### Configuration vs Critical Errors

The loader distinguishes between two types of errors:

**Configuration Errors (Graceful Skipping):**

When a cog requires configuration that's missing, it's skipped gracefully. The loader logs a warning and continues loading other cogs. This allows optional cogs to be disabled without breaking startup.

**Critical Errors (Failure Propagation):**

Real errors like import failures or syntax errors cause the loading group to fail. These errors are captured by Sentry with full context and prevent the bot from starting with broken cogs.

### Error Recovery

The loader recursively checks exception chains for configuration errors, so even if a configuration error is wrapped in another exception, it's detected and handled gracefully.

## Performance Monitoring

### Load Time Tracking

The loader tracks detailed timing metrics for each cog:

- Individual cog load times
- Group load times
- Total loading time
- Slow cog detection

All metrics are recorded to Sentry for performance analysis.

### Slow Cog Detection

Cogs taking longer than 1 second to load are flagged as slow. This helps identify performance bottlenecks and optimize startup time.

### Sentry Integration

Comprehensive telemetry spans track the entire loading process:

- Cog name and path
- Load status (loaded, skipped, failed)
- Load time in milliseconds
- Error details for failures

This telemetry helps debug loading issues and monitor performance over time.

## Loading Folders

The cog loader loads cogs from specific folders in priority order:

**Loading Sequence:**

1. **Handlers** - `services/handlers/` (highest priority)
2. **Modules** - `modules/` (normal priority)
3. **Plugins** - `plugins/` (lowest priority)

This ensures handlers are ready before commands, and built-in modules load before custom plugins.

### Folder Structure

Place cogs in the appropriate folder based on their purpose:

- **Handlers** - Event listeners, error handlers, critical infrastructure
- **Modules** - Bot commands, features, user-facing functionality
- **Plugins** - Custom extensions, optional features

The loader automatically discovers and loads all valid cogs from these folders.

## Creating Loadable Cogs

### Required Components

For a file to be loadable as a cog, it must:

1. Be a `.py` file (not starting with `_`)
2. Contain an `async def setup(bot)` function
3. Not be in the ignore list
4. Pass AST validation

### Setup Function

Every cog needs a setup function:

```python
async def setup(bot: Tux) -> None:
    """Cog setup function."""
    await bot.add_cog(MyCog(bot))
```

The setup function is called when the cog is loaded. Use it to add your cog to the bot.

### Module Path Resolution

The loader converts file paths to Python module paths automatically:

- File: `tux/modules/admin/ban.py` → Module: `tux.modules.admin.ban`
- File: `tux/services/handlers/error.py` → Module: `tux.services.handlers.error`

You don't need to worry about path conversion—the loader handles it automatically.

## Best Practices

### Use Appropriate Folders

Place cogs in the correct folder based on their purpose. Handlers go in `services/handlers/`, modules go in `modules/`, and plugins go in `plugins/`.

### Handle Configuration Errors

If your cog requires configuration, raise `TuxConfigurationError` when configuration is missing. The loader will skip your cog gracefully instead of failing startup.

### Keep Setup Functions Simple

Setup functions should only add the cog to the bot. Complex initialization should happen in the cog's `cog_load()` method.

### Avoid Circular Dependencies

Structure your cogs to avoid circular imports. Use lazy imports if necessary, and keep dependencies clear.

## Troubleshooting

### Cog Not Loading

If your cog doesn't load:

1. Check the file is in the correct folder
2. Verify it has a `setup()` function
3. Check for syntax errors
4. Ensure it's not in the ignore list
5. Check logs for error messages

### Configuration Errors

If you see "Skipping cog due to missing configuration":

1. Check what configuration your cog requires
2. Set the required environment variables
3. Restart the bot to reload cogs

### Slow Loading

If cogs load slowly:

1. Check for heavy imports in module-level code
2. Move expensive operations to `cog_load()`
3. Use lazy imports for optional dependencies
4. Check Sentry telemetry for specific timing data

### Import Errors

If you see import errors:

1. Verify all dependencies are installed
2. Check for circular imports
3. Ensure module paths are correct
4. Check Python version compatibility

## Resources

- **Source Code**: `src/tux/core/cog_loader.py`
- **Cog Priorities**: See `src/tux/shared/constants.py` for priority definitions
- **Base Cog**: See `base-cog.md` for cog development
- **Modules**: See `modules.md` for module structure
