# Database

## Overview

Our application utilizes Prisma as the type-safe database client and Object-Relational Mapping (ORM) tool. The database models are automatically defined and generated from `.prisma` schema files. To manage database operations for each model, we implement custom controllers.

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
The `client.py` file initializes our Prisma client with:
```python
from prisma import Prisma

db = Prisma(log_queries=False, auto_register=True)
```
This provides a centralized database client instance with:
- Query logging disabled for production performance
- Auto-registration enabled for model discovery

### Controllers Directory

All logic pertaining to each database model is encapsulated within controllers. These controllers are located within the `tux/database/controllers` directory. They serve as the main access point for handling all operations related to data manipulation and retrieval for their respective models.

### Initialization

Within the `controllers` directory, the `__init__.py` file plays a critical role. It is responsible for importing all individual controllers, thus consolidating them into a unified system. These imported controllers are then made available to the rest of the application through the `DatabaseController` class.

## DatabaseController Class

The `DatabaseController` class serves as the central hub, interfacing between various parts of the application and the database controllers. By importing it, other components of the system can utilize database operations seamlessly, leveraging the logic encapsulated within individual controllers.

Commands and features within the bot make use of this centralized class to handle all necessary data storage and retrieval operations in a type-safe and efficient manner, ensuring robust interaction with the database.

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
3. Use type hints with Prisma-generated types
4. Leverage Prisma's built-in filtering and pagination
5. Handle database connections properly in async contexts