---
title: Database Controllers
tags:
  - developer-guide
  - concepts
  - database
  - controllers
---

# Database Controllers

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Tux's controller layer provides a clean, composable interface for database operations. Controllers encapsulate business logic, optimize queries, and provide consistent APIs for database interactions.

The controller system uses composition over inheritance with lazy-loaded specialized controllers for optimal performance. The DatabaseCoordinator acts as a facade providing centralized access to all model-specific controllers.

## Architecture

### BaseController Composition Structure

The BaseController uses composition to provide specialized database operations through core and specialized controllers.

#### Core Controllers (Eagerly Loaded)

- **CrudController**: Basic Create, Read, Update, Delete operations
- **QueryController**: Advanced querying with filtering and relationships

#### Specialized Controllers (Lazy Loaded)

- **BulkOperationsController**: Batch operations for efficiency
- **TransactionController**: Transaction management
- **UpsertController**: Get-or-create and upsert patterns

### Lazy Initialization Strategy

Specialized controllers load on-demand to reduce memory usage and improve startup speed while maintaining flexibility for adding new controller types.

### DatabaseCoordinator Organization

The DatabaseCoordinator provides centralized controller access through a facade pattern, enabling uniform property-based access and lazy loading of controllers.

## Key Concepts

### Composition Over Inheritance

Controllers use composition patterns for flexibility, allowing lazy-loaded specialized controllers that can be combined as needed without forcing all functionality to be available at once.

### Lazy Loading for Performance

Specialized controllers load only when needed, reducing memory footprint and improving startup speed while supporting many operation types without overhead.

### Filter Building Patterns

Flexible filtering with automatic query construction from dictionaries and support for complex SQLAlchemy filter expressions.

### Pagination Patterns

Built-in pagination with metadata including page information, total counts, and navigation data for large result sets.

### Upsert Operations

Get-or-create and upsert patterns for data synchronization scenarios, returning both the record and creation status.

### Transaction Management

Explicit transaction control for complex multi-step operations requiring atomicity and consistency.

## Usage Patterns

### DatabaseCoordinator Usage

Access model-specific controllers through centralized coordinator with uniform property-based interface.

### Custom Controller Methods

Create domain-specific controllers that extend BaseController with business logic methods using composed specialized controllers.

### Specialized Controller Usage

Leverage bulk operations for efficiency, upsert for synchronization, and transactions for consistency.

## Best Practices

### Always Use Controllers, Not Direct Session Access

- Type safety through full type checking
- Business logic enforced at controller level
- Consistent APIs across the application
- Easy testability and mocking
- Isolated changes for maintainability

### Create Model-Specific Controllers for Domain Logic

Build domain-specific controllers that encapsulate business rules and provide higher-level operations.

### Use Lazy-Loaded Controllers for Complex Operations

- Performance optimization through on-demand loading
- Memory efficiency for simple operations
- Faster startup through reduced initialization
- Scalability support for many operation types

### Leverage Specialized Controllers for Optimized Queries

- Bulk operations for batch processing efficiency
- Upsert for data synchronization scenarios
- Transactions for multi-step operations requiring consistency

### Handle Errors at Appropriate Levels

Controller-level validation for business rules, data integrity checks, and user-friendly error messages.

### Design Controllers for Testability

Use dependency injection patterns for easy mocking and isolated testing of controller logic.

### Use Appropriate Loading Strategies

- Selective relationship loading to prevent over-fetching
- Choose between selectin, joined, or noload based on access patterns
- Consider performance implications of loading strategies

### Document Controller Methods Clearly

Provide comprehensive docstrings explaining purpose, parameters, return values, and error conditions for complex operations.

## Related Topics

- [Database Architecture](architecture.md) - Overall controller placement in architecture
- [Database Service](service.md) - Underlying database service used by controllers
- [Database Models](models.md) - Models used by controllers
- [Database Utilities](utilities.md) - Helper functions for controller access
