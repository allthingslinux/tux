---
title: Database Models
---

## Overview

Tux uses SQLModel for type-safe database models that combine SQLAlchemy and Pydantic. All models inherit from a custom BaseModel class providing automatic timestamp management, serialization utilities, and PostgreSQL-specific features.

Models serve as the data contract between application and database, providing type safety, automatic serialization, relationship management, and schema generation.

## BaseModel Foundation

All Tux models inherit from BaseModel for consistent behavior across the application.

### BaseModel Features

- **Automatic Timestamps**: created_at and updated_at managed by database
- **Serialization**: Built-in JSON conversion with proper datetime handling
- **Utility Methods**: to_dict() for API responses and logging
- **Flexibility**: Support for advanced SQLAlchemy features

### Mixin Patterns

Tux provides reusable mixins for common model patterns:

- **UUIDMixin**: For records needing UUID primary keys (API keys, tokens)
- **SoftDeleteMixin**: For data that should be recoverable (users, important records)

Mixins maintain type safety while providing reusable functionality across models.

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
