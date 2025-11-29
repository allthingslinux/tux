---
title: Database Architecture
tags:
  - developer-guide
  - concepts
  - database
  - architecture
---

# Database Architecture

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Tux's database architecture follows a three-layer pattern that separates concerns while maintaining type safety and developer experience. The architecture prioritizes async-first design, automatic resource management, and composable operations built on PostgreSQL.

## Three-Layer Architecture

The architecture provides clear separation of concerns through three distinct layers:

### Service Layer

Foundation layer handling all PostgreSQL interactions with connection pooling, session management, health monitoring, and transaction handling.

### Controller Layer

Business logic layer providing composable database operations through base controllers and specialized controllers (CRUD, Query, Pagination, Bulk, Transaction, Performance, Upsert).

### Model Layer

Type-safe data models with automatic timestamp management, relationship definitions, and PostgreSQL-specific type support.

## Key Principles

### Composition Over Inheritance

Controllers use composition patterns for flexibility, allowing lazy-loaded specialized controllers that can be combined as needed without forcing all functionality to be available at once.

### Async-First Design

All database operations are async by default, enabling non-blocking I/O, efficient concurrent request handling, and optimal resource utilization for Discord bot workloads.

### Automatic Resource Management

Sessions and connections are automatically managed through context managers, ensuring proper cleanup and preventing resource leaks.

### Transaction Safety

Transactions are automatically managed at the session level, with all operations within a session context being transactional and auto-committed on success or rolled back on failure.

### Connection Pooling

PostgreSQL connections are efficiently pooled with pre-ping validation, periodic recycling, and size management optimized for Discord bot workloads.

## Architectural Patterns

### Layer Interaction Flow

Commands/Interactions → DatabaseCoordinator → BaseController → Specialized Controllers → DatabaseService → PostgreSQL

### Service Access Patterns

- **Bot Attachment**: Database services attached directly to bot instances
- **Context Resolution**: Services automatically discovered from Discord contexts
- **Fallback Support**: Graceful degradation when preferred access methods unavailable

### Controller Organization

- **DatabaseCoordinator**: Facade pattern providing centralized controller access
- **BaseController**: Composition pattern with lazy-loaded specialized controllers
- **Model-Specific Controllers**: Domain-specific controllers for business logic

## Best Practices

### Layer Separation Guidelines

- Use Controllers for business logic and complex operations
- Use Service Layer for direct SQL queries or performance-critical operations
- Never bypass controllers for standard CRUD operations

### When to Use Each Layer

**Controller Layer:**

- Standard CRUD operations
- Business logic with relationships
- Pagination and filtering
- Bulk operations

**Service Layer:**

- Raw SQL queries
- Performance-critical operations
- Health checks and monitoring
- Custom transaction management

**Model Layer:**

- Data validation and serialization
- Relationship definitions
- Schema definitions

### Performance Considerations

- Lazy loading of specialized controllers on-demand
- Efficient connection pooling and reuse
- Proper session scoping to operations
- Query optimization through specialized controllers

### Error Handling Strategy

- Controller Level: Business logic errors and validation
- Service Level: Connection errors and transaction failures
- Global Level: Unexpected errors with monitoring integration

### Testing Strategy

- Unit Tests: Test controllers with mocked service layer
- Integration Tests: Test full stack with real database
- Isolation: Each test uses fresh database schema

## Related Topics

- [Database Service](service.md) - Connection management and session handling
- [Database Controllers](controllers.md) - Controller patterns and operations
- [Database Models](models.md) - SQLModel definitions and relationships
- [Database Utilities](utilities.md) - Context access and helper functions
