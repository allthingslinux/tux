---
title: Database Concepts
---

## Overview

Tux uses a robust, async-first PostgreSQL database layer built with SQLModel and SQLAlchemy. The database architecture follows a clean three-layer pattern that separates concerns and enables maintainable, type-safe database operations.

The three layers work together to provide:

- **Service Layer**: Connection management, session handling, and health monitoring
- **Controller Layer**: Business logic, query optimization, and specialized operations
- **Model Layer**: Type-safe data models with automatic serialization and relationships

This architecture supports complex Discord bot operations including moderation, user leveling, custom commands, and configuration management, all while maintaining excellent performance and developer experience.

## Navigation

### Core Concepts

- [Database Architecture](architecture.md) - Three-layer architecture and design principles
- [Database Service](service.md) - Connection management and session handling
- [Database Models](models.md) - SQLModel definitions, relationships, and mixins
- [Database Controllers](controllers.md) - Controller patterns and specialized operations
- [Database Migrations](migrations.md) - Schema evolution with Alembic
- [Database Testing](testing.md) - Testing strategies and fixtures
- [Database Utilities](utilities.md) - Context access and helper functions

### Related Guides

- [Database Integration Tutorial](../../tutorials/database-integration.md) - Getting started with database operations
- [Database CLI Reference](../../../reference/cli.md) - Command-line database management
