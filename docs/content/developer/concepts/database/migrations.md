---
title: Database Migrations
tags:
  - developer-guide
  - concepts
  - database
  - migrations
---

# Database Migrations

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Overview

Tux uses Alembic for database schema migrations, providing version control for PostgreSQL schema changes. Migrations enable safe, incremental database evolution while maintaining data integrity across environments.

The migration system supports version control for schema changes, safe rollbacks, team collaboration, production safety, and environment consistency through automatic schema comparison and DDL generation.

## Architecture

### Migration Environment Configuration

Alembic migrations are configured with production-ready features including async-to-sync URL conversion, comprehensive schema comparison, batch rendering for ALTER TABLE operations, and transaction safety per migration.

### Model Registration Process

All models are registered with SQLAlchemy metadata to ensure complete coverage in migration detection and prevent garbage collection during migration generation.

### Migration Modes

Alembic supports online mode (database connection) for development/staging/production, and offline mode (SQL generation) for code review, manual DBA execution, and CI/CD pipelines.

### Database CLI Integration

Tux provides a comprehensive database CLI that wraps Alembic commands with workflow optimization, safety features, rich output, and integration with service initialization.

## Key Concepts

### Async-to-Sync URL Conversion

Alembic requires synchronous database drivers, so async URLs must be automatically converted for compatibility across all environments.

### Retry Logic for Docker/CI

Migrations include automatic retry logic with configurable attempts and delays to handle container startup timing and infrastructure resilience.

### Empty Migration Prevention

Alembic prevents generation of empty migration files to maintain clean history and avoid meaningless commits.

### Transaction per Migration

Each migration runs in its own transaction ensuring atomicity, individual rollback capability, isolation from other migrations, and easier debugging.

### Schema Change Detection

Alembic automatically detects table operations, column changes, constraints, indexes, and server defaults through comprehensive comparison configuration.

## Usage Patterns

### Development Workflow

Generate migrations from model changes and apply immediately for rapid iteration.

### Migration Review Process

Check status, generate migrations for review, validate changes, then apply with proper oversight.

### Production Deployment

Validate migration status, run checks, and apply migrations safely with monitoring.

### Migration Rollback

Support safe rollback operations with proper backup procedures for one migration or specific revisions.

## Best Practices

### Always Review Generated Migrations

Auto-generated migrations require review for correct types, constraints, indexes, relationships, and rollback operations before application.

### Use Descriptive Migration Messages

Clear, descriptive migration messages that explain the purpose and scope of schema changes.

### Test Migrations in Development First

Create, apply, rollback, and validate migrations in development before committing and deploying.

### Use Database CLI Commands

Leverage the database CLI for safety features, better UX, and integration rather than direct Alembic commands.

### Keep Migrations Atomic

Each migration should perform one logical change to maintain clarity and rollback safety.

### Handle Data Migrations Carefully

For schema changes requiring data transformation, add columns as nullable first, perform data migration, then apply constraints.

### Use Appropriate Migration Commands

Follow development workflow for iteration, production deployment patterns for releases, and troubleshooting commands for investigation.

### Backup Before Destructive Operations

Always backup before rollback or reset operations, especially for destructive nuclear resets in development.

### Document Migration Dependencies

Document any special requirements, dependencies, or considerations in migration files.

### Monitor Migration Performance

Check for long-running queries and consider batch processing, strategic indexing, and background jobs for large data migrations.

## Related Topics

- [Database Models](models.md) - Model definitions that drive migrations
- [Database Service](service.md) - Database service used by migrations
- [Database CLI Reference](../../../reference/cli.md) - Complete CLI command reference
