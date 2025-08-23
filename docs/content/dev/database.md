# Database

## Overview

Our application utilizes SQLModel with SQLAlchemy, providing a type-safe database interface with modern Python async support. Database models are defined using SQLModel classes, and Alembic handles schema migrations. We implement custom controllers to manage database operations for each model.

## SQLModel Setup

### Model Organization

Our SQLModel models are organized in the `src/tux/database/models/` directory:

- `content.py`: Content-related models (Snippets, Reminders, etc.)
- `guild.py`: Guild and guild configuration models
- `moderation.py`: Moderation case models
- `permissions.py`: Permission and role-related models
- `social.py`: Social features (AFK status, levels, etc.)
- `starboard.py`: Starboard message models

### Environment Configuration

The database connection is configured through environment variables:

- `DATABASE_URL`: Primary connection URL for the database
- `DEV_DATABASE_URL`: Development database URL
- `PROD_DATABASE_URL`: Production database URL

## Project Structure

### Database Directory

Located at `src/tux/database/`, this directory contains:

#### Core Module

The `core/` directory contains the database management layer:

- `database.py`: DatabaseService class for session management (DatabaseManager is deprecated)
- `base.py`: Base model definitions and common functionality

#### Services Module

The `services/` directory provides high-level database services:

- `database.py`: DatabaseService class for dependency injection

### Controllers Directory

All logic pertaining to each database model is encapsulated within controllers. These controllers are located within the `src/tux/database/controllers` directory. They serve as the main access point for handling all operations related to data manipulation and retrieval for their respective models.

### Initialization

Within the `controllers` directory, the `__init__.py` file plays a critical role.

It is responsible for importing all individual controllers, thus consolidating them into a unified system. These imported controllers are then made available to the rest of the application through the `DatabaseController` class.

## DatabaseController Class

The `DatabaseController` class serves as the central hub, interfacing between various parts of the application and the database controllers. By importing it, other components of the system can utilize database operations seamlessly, leveraging the logic encapsulated within individual controllers.

## Working with SQLModel

### Key Features

1. **Type Safety**: SQLModel generates Python types for all models, ensuring type-safe database operations
2. **Async Support**: Built-in support for async/await operations through SQLAlchemy
3. **Query Building**: Intuitive API for building complex queries using SQLAlchemy syntax
4. **Automatic Migrations**: Support for database schema migrations via Alembic
5. **Relation Handling**: Sophisticated handling of model relationships

### Common Operations

Controllers can utilize SQLAlchemy's powerful query capabilities through SQLModel:

```python
from sqlmodel import select
from tux.database.models.guild import Guild

# Create
async with self.db.session() as session:
    guild = Guild(guild_id=123456789, name="Test Guild")
    session.add(guild)
    await session.commit()

# Read
async with self.db.session() as session:
    statement = select(Guild).where(Guild.guild_id == 123456789)
    result = await session.exec(statement)
    guild = result.first()

# Update
async with self.db.session() as session:
    statement = select(Guild).where(Guild.guild_id == 123456789)
    result = await session.exec(statement)
    guild = result.first()
    if guild:
        guild.name = "Updated Guild Name"
        await session.commit()

# Delete
async with self.db.session() as session:
    statement = select(Guild).where(Guild.guild_id == 123456789)
    result = await session.exec(statement)
    guild = result.first()
    if guild:
        await session.delete(guild)
        await session.commit()
```

### Best Practices

1. Always use the database session context manager for database operations
2. Implement model-specific logic in dedicated controllers
3. Use type hints with SQLModel types where necessary
4. Leverage SQLAlchemy's built-in filtering and pagination as needed
5. Handle database connections properly in async contexts
6. Use Alembic for schema migrations instead of manual schema changes

## Database Management

This section details how to manage the database schema and migrations using the `tux` CLI, which internally uses Alembic.

### Available Commands

- **Upgrade Database:**
    Apply all pending migrations to bring the database up to the latest schema version.

    ```bash
    uv run tux db upgrade
    ```

- **Create Migration:**
    Generate a new migration file based on model changes.

    ```bash
    uv run tux db revision
    ```

- **Downgrade Database:**
    Downgrade the database by one migration (rollback).

    ```bash
    uv run tux db downgrade
    ```

- **Check Current Version:**
    Display the current migration version of the database.

    ```bash
    uv run tux db current
    ```

- **View Migration History:**
    Show the complete migration history.

    ```bash
    uv run tux db history
    ```

- **Reset Database:**
    Reset the database to the base state (WARNING: This will drop all data).

    ```bash
    uv run tux db reset
    ```

For details on interacting with the database *within the application code* using controllers, see the [Database Controller Patterns](./database_patterns.md) guide.
