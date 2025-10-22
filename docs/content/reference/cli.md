# CLI Reference

This page provides complete reference documentation for all Tux command-line tools.

## Overview

Tux includes a comprehensive CLI built with Typer for development and administration tasks. All commands are invoked via `uv run`:

```bash
uv run <command> <subcommand> [options]
```

Available command groups:

- **`tux`** - Bot management (start, version)
- **`db`** - Database operations (migrations, health)
- **`dev`** - Development tools (lint, format, type-check)
- **`tests`** - Test runner (run tests with various options)
- **`docker`** - Docker management (up, down, logs)
- **`docs`** - Documentation (serve, build)
- **`config`** - Configuration generation

## Quick Reference

### Common Commands

```bash
# Start the bot
uv run tux start
uv run tux start --debug

# Database operations
uv run db push                      # Apply migrations
uv run db new "add feature"         # Create migration
uv run db health                    # Check database health

# Development
uv run dev all                      # Run all checks
uv run dev lint                     # Lint code
uv run dev format                   # Format code

# Testing
uv run tests run                    # Run tests with coverage
uv run tests quick                  # Quick run without coverage

# Docker
uv run docker up                    # Start services
uv run docker down                  # Stop services
uv run docker logs                  # View logs

# Documentation
uv run docs serve                   # Serve docs locally
```

## Auto-Generated Documentation

Below is the complete CLI reference, automatically generated from the command definitions:

::: mkdocs-typer
    :module: scripts.cli
    :command: cli

---

## Usage Examples

### Bot Management

```bash
# Start bot in production mode
uv run tux start

# Start bot in debug mode (verbose logging)
uv run tux start --debug

# Show version information
uv run tux version
```

### Database Management

```bash
# Initialize database (first time setup)
uv run db init

# Apply all pending migrations
uv run db push

# Create new migration
uv run db new "add user preferences table"

# Check migration status
uv run db status

# View migration history
uv run db history

# Check database health
uv run db health

# List all tables
uv run db tables

# Reset database (safe - uses migrations)
uv run db reset

# Nuclear reset (dangerous - drops everything)
uv run db nuke --force
```

### Development Tools

```bash
# Run all quality checks
uv run dev all

# Individual checks
uv run dev lint                     # Ruff linter
uv run dev format                   # Ruff formatter
uv run dev type-check               # Basedpyright
uv run dev lint-docstring           # Pydoclint

# Pre-commit hooks
uv run dev pre-commit
uv run dev pre-commit --all-files
```

### Testing

```bash
# Run all tests with coverage
uv run tests run

# Quick run without coverage
uv run tests quick

# Generate HTML coverage report
uv run tests html

# Show coverage summary
uv run tests coverage

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run tests with marker
uv run pytest -m unit
uv run pytest -m integration
```

### Docker Operations

```bash
# Start all services
uv run docker up

# Start services in detached mode
uv run docker up -d

# Stop all services
uv run docker down

# Build images
uv run docker build

# View logs
uv run docker logs
uv run docker logs tux              # Specific service
uv run docker logs -f               # Follow logs

# List running containers
uv run docker ps

# Open shell in container
uv run docker shell
uv run docker shell tux-postgres
```

### Documentation

```bash
# Serve documentation locally
uv run docs serve

# Serve on specific port
uv run docs serve --port 8080

# Build static documentation
uv run docs build

# Clean build directory
uv run docs clean
```

### Configuration

```bash
# Generate example config files
uv run config generate

# Generate specific format
uv run config generate --format toml
uv run config generate --format yaml
uv run config generate --format json
```

## Exit Codes

All CLI commands follow standard Unix exit codes:

- `0` - Success
- `1` - General error
- `2` - Usage error (invalid arguments)

Example usage in scripts:

```bash
#!/bin/bash
if uv run tests run; then
    echo "Tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

## Environment Variables

CLI commands respect environment variables:

- `DEBUG` - Enable debug mode if set to `true`
- `NO_COLOR` - Disable colored output if set
- `FORCE_COLOR` - Force colored output if set

## For Developers

### Adding New Commands

To add new CLI commands:

1. Open the appropriate CLI file in `scripts/`
2. Add command to the CLI class
3. Register in `_setup_command_registry()`
4. Add docstring with usage examples
5. Test the command
6. Documentation auto-generates

**[Extending CLI Guide →](../developer-guide/cli-tools/extending-cli.md)**

### CLI Architecture

The CLI system uses:

- **Typer** for argument parsing and help generation
- **Rich** for beautiful terminal output
- **Registry Pattern** for command organization
- **Base Class** for shared functionality

**[CLI Architecture →](../developer-guide/cli-tools/overview.md)**

## Getting Help

### In-Terminal Help

All commands support `--help`:

```bash
uv run tux --help
uv run db --help
uv run db push --help
```

### Documentation

- **[Developer Guide](../developer-guide/)** - Development documentation
- **[Admin Guide](../admin-guide/)** - Administration guides
- **[CLI Tools Guide](../developer-guide/cli-tools/)** - CLI architecture

### Community

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask in #development
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Report CLI bugs

---

**Note**: This page includes auto-generated documentation from the CLI commands. For conceptual guides, see the **[Developer Guide](../developer-guide/cli-tools/)**.
