---
title: Database Models
tags:
  - developer-guide
  - concepts
  - database
  - models
---

# Database Models

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Overview

Tux uses SQLModel for type-safe database models that combine SQLAlchemy and Pydantic. All models inherit from a custom BaseModel class providing automatic timestamp management, serialization utilities, and PostgreSQL-specific features.

Models serve as the data contract between application and database, providing type safety, automatic serialization, relationship management, and schema generation.

## BaseModel Foundation

All Tux models inherit from BaseModel for consistent behavior across the application.

### BaseModel Features

- **Automatic Timestamps**: created_at and updated_at via TimestampMixin
- **Serialization**: Built-in JSON conversion with proper datetime handling
- **Utility Methods**: to_dict() for API responses and logging
- **Flexibility**: Support for advanced SQLAlchemy features

### Mixin Patterns

Tux provides reusable mixins for common model patterns:

- **TimestampMixin**: Automatic created_at/updated_at with database defaults
- **UUIDMixin**: For records needing UUID primary keys (API keys, tokens)
- **SoftDeleteMixin**: For data that should be recoverable (users, important records)

Mixins maintain type safety while providing reusable functionality across models.

#### TimestampMixin

All models automatically get timestamp fields through TimestampMixin:

```python
class MyModel(SQLModel, TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    # created_at and updated_at are automatically added
```

**Features:**

- `created_at`: Automatically set by database on INSERT, never changes
- `updated_at`: Automatically set by database on INSERT, updated on every UPDATE
- Pure database-managed timestamps for consistency and performance
- UTC timezone-aware datetime objects
- Fields always available in model `__dict__` for compatibility
- No application-level defaults (handled entirely by database)

## Model Definition Patterns

### Enum Definitions

Enums provide type-safe constants for database fields, stored as strings in PostgreSQL with compile-time validation and self-documenting names.

### Relationship Definitions

Models define relationships with proper cascade behavior, lazy loading strategies, and bidirectional navigation through back_populates.

## Key Concepts

### Automatic Timestamp Management

Timestamps are managed automatically by the database, ensuring consistency, accuracy, and timezone awareness across all records.

### Serialization Patterns

Models provide flexible serialization for API responses with relationship control, type conversion, and depth management to prevent circular references.

### PostgreSQL-Specific Features

Leverage PostgreSQL's advanced types including JSONB for flexible metadata, arrays for ordered lists, and native indexing for performance.

### Relationship Loading Strategies

- **selectin**: Load related objects in separate query (default for most cases)
- **joined**: Load with JOIN in same query (performance-critical paths)
- **noload**: Skip relationship loading (explicit control)

### Cascade Delete Configurations

Relationships handle deletion automatically with data integrity, performance optimization, and safety through passive deletes for complex relationships.

## Best Practices

### Always Inherit from BaseModel

- Ensures uniform timestamp and serialization behavior
- Provides future-proofing through centralized features
- Maintains type safety and consistency across models

### Use Appropriate Mixins

- UUIDMixin for records needing UUID primary keys
- SoftDeleteMixin for recoverable data
- Combine mixins as needed for domain-specific patterns

### Define Relationships Carefully

- Always use Relationship for navigation between models
- Configure appropriate cascade delete behavior
- Choose lazy strategy based on access patterns
- Include back_populates for bidirectional relationships

### Use Type Hints Consistently

- Proper type annotations for fields and return values
- Optional types with `| None` convention
- Generic types for collections and dictionaries

### Leverage PostgreSQL Features

- JSONB for flexible, queryable metadata
- Arrays for ordered lists (tags, permissions)
- Enums for constrained choice fields
- Database constraints for data integrity

### Handle Serialization Properly

- Use to_dict() for logging, debugging, and API responses
- Control relationship inclusion to prevent over-fetching
- Ensure proper type conversion for JSON compatibility

### Index Strategically

- Index foreign keys and frequently queried fields
- Use GIN indexes for JSON and array fields
- Consider query patterns when adding indexes

### Document Model Purpose

- Clear docstrings explaining model responsibility
- Document relationships and constraints
- Explain business logic and validation rules

## Related Topics

- [Database Architecture](architecture.md) - Overall model placement in architecture
- [Database Controllers](controllers.md) - Using models through controllers
- [Database Migrations](migrations.md) - Schema changes and model evolution
