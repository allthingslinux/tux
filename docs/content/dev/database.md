# Database

## Overview

Our application utilizes Prisma, a type-safe database client and Object-Relational Mapping (ORM) tool. The database models are automatically defined and generated from `.prisma` schema files. To manage database operations for each model, we implement custom controllers.

## Prisma Setup

### Schema Organization

Our Prisma schema is organized in the `prisma/schema` directory, following a modular approach:

- `main.prisma`: The root schema file that contains:
  - Client generator configuration for Python
  - Database connection configuration
  - Preview features configuration
  - Database provider settings (PostgreSQL)

The generator is configured with:

- `prisma-client-py` as the provider
- Asyncio interface for asynchronous operations
- Unlimited recursive type depth
- Support for schema folder organization

### Environment Configuration

The database connection is configured through environment variables:

- `DATABASE_URL`: Primary connection URL for Prisma
- `directUrl`: Direct connection URL (same as DATABASE_URL in our setup)

## Project Structure

### Prisma Directory

The `prisma` directory contains:

- `schema/`: Directory containing all Prisma schema files
  - `main.prisma`: Core schema configuration
  - Additional model-specific schema files (if any)

### Database Directory

Located at `tux/database/`, this directory contains:

#### Client Module

The [`client.py`](https://github.com/allthingslinux/tux/blob/main/tux/database/client.py) file initializes our Prisma client with:

```python
from prisma import Prisma

db = Prisma(log_queries=False, auto_register=True)
```

### Controllers Directory

All logic pertaining to each database model is encapsulated within controllers. These controllers are located within the `tux/database/controllers` directory. They serve as the main access point for handling all operations related to data manipulation and retrieval for their respective models.

### Initialization

Within the `controllers` directory, the `__init__.py` file plays a critical role.

It is responsible for importing all individual controllers, thus consolidating them into a unified system. These imported controllers are then made available to the rest of the application through the `DatabaseController` class.

## DatabaseController Class

The `DatabaseController` class serves as the central hub, interfacing between various parts of the application and the database controllers. By importing it, other components of the system can utilize database operations seamlessly, leveraging the logic encapsulated within individual controllers.

## Working with Prisma

### Key Features

1. **Type Safety**: Prisma generates Python types for all models, ensuring type-safe database operations
2. **Async Support**: Built-in support for async/await operations
3. **Query Building**: Intuitive API for building complex queries
4. **Automatic Migrations**: Support for database schema migrations
5. **Relation Handling**: Sophisticated handling of model relationships

### Common Operations

Controllers can utilize Prisma's powerful query capabilities:

```python
# Create
await db.user.create(data={"name": "John"})

# Read
user = await db.user.find_unique(where={"id": 1})

# Update
await db.user.update(
    where={"id": 1},
    data={"name": "John Doe"}
)

# Delete
await db.user.delete(where={"id": 1})

# Relations
posts = await db.user.find_unique(
    where={"id": 1}
).include(posts=True)
```

### Best Practices

1. Always use the central `db` instance from `client.py`
2. Implement model-specific logic in dedicated controllers
3. Use type hints with Prisma-generated types where necessary
4. Leverage Prisma's built-in filtering and pagination as needed
5. Handle database connections properly in async contexts

## Database Management

This section details how to manage the database schema and migrations using the `tux` CLI, which internally uses Prisma.

(For details on interacting with the database *within the application code* using controllers, see the [Database Controller Patterns](./database_patterns.md) guide).

Commands target the development or production database based on the environment flag used (see [CLI Usage](./cli/index.md)). Development mode is the default.

- **Generate Prisma Client:**
    Regenerates the Prisma Python client based on `schema.prisma`. Usually done automatically by other commands, but can be run manually.

    ```bash
    poetry run tux --dev db generate
    ```

- **Apply Schema Changes (Dev Only):**
    Pushes schema changes directly to the database **without** creating SQL migration files. This is suitable only for the development environment as it can lead to data loss if not used carefully.

    ```bash
    poetry run tux --dev db push
    ```

- **Create Migrations:**
    Compares the current `schema.prisma` with the last applied migration and generates a new SQL migration file in `prisma/migrations/` reflecting the changes.

    ```bash
    # Use --dev for the development database
    poetry run tux --dev db migrate --name <your-migration-name>

    # Use --prod for the production database
    poetry run tux --prod db migrate --name <your-migration-name>
    ```

- **Apply Migrations:**
    Runs any pending SQL migration files against the target database.

    ```bash
    # Apply to development database
    poetry run tux --dev db migrate

    # Apply to production database
    poetry run tux --prod db migrate
    ```

- **Pull Schema from Database:**
    Introspects the target database and updates the `schema.prisma` file to match the database's current state. Useful if the database schema has diverged.

    ```bash
    poetry run tux --dev db pull
    poetry run tux --prod db pull
    ```

- **Reset Database (Destructive!):**
    Drops the entire database and recreates it based on the current schema, applying all migrations. **Use with extreme caution, especially with `--prod`.**

    ```bash
    # Reset development database
    poetry run tux --dev db reset

    # Reset production database (requires confirmation)
    poetry run tux --prod db reset
    ```
