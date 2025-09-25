# CLI Reference

Tux provides a comprehensive set of CLI tools for development, testing, deployment, and maintenance.

## Overview

All CLI tools are accessible through `uv run` commands defined in `pyproject.toml`:

```bash
uv run tux      # Bot operations
uv run dev      # Development tools  
uv run db       # Database management
uv run test     # Testing operations
uv run docker   # Docker operations
uv run docs     # Documentation tools
```text

## Quick Examples

### Daily Development Workflow

```bash
# Start development
uv run tux start

# Run tests
uv run test

# Check code quality
uv run dev all

# Database operations
uv run db upgrade
```text

### Common Operations

```bash
# Code quality
uv run dev lint          # Run linting
uv run dev format        # Format code
uv run dev type-check    # Type checking

# Database
uv run db status         # Check connection
uv run db revision       # Create migration

# Docker
uv run docker up         # Start services
uv run docker logs       # View logs
```text

## Auto-Generated CLI Documentation

::: mkdocs-typer
    :module: scripts.cli
    :command: cli
    :depth: 1
