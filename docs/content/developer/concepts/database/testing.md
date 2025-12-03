---
title: Database Testing
tags:
  - developer-guide
  - concepts
  - database
  - testing
---

# Database Testing

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Overview

Tux uses py-pglite for comprehensive database testing, providing an in-memory PostgreSQL instance that supports the full PostgreSQL feature set. This approach enables fast, isolated, and reliable database tests without external dependencies.

The testing strategy focuses on complete isolation, real PostgreSQL compatibility, fast execution, type safety, and fixture-based setup with clear separation between unit and integration testing.

## Architecture

### PGlite Fixture Structure

Tux uses a multi-layer fixture system for optimal test isolation and performance with session-scoped managers, function-scoped engines, and service instances.

### Session vs Function Scoped Fixtures

Different fixture scopes serve different testing needs - session scope for expensive setup and shared resources, function scope for maximum isolation and state safety.

### Test Database Setup/Teardown

Automatic schema management ensures clean test state with consistent table creation and cleanup for every test run.

### Controller Testing Patterns

Controllers are tested through dedicated fixtures providing type safety, service mocking, isolation, and reusability across test suites.

## Key Concepts

### In-Memory PostgreSQL Testing

py-pglite provides a complete PostgreSQL implementation in memory with full feature support including JSONB, arrays, constraints, indexes, and transactions.

### Fixture Lifecycle Management

Proper fixture lifecycle ensures reliable tests with automatic cleanup, exception safety, resource management, and consistent behavior across all tests.

### Test Isolation Principles

Complete isolation prevents test interference through function-scoped fixtures, ensuring no cross-test dependencies, reliable debugging, parallelization support, and consistent environments.

### Performance Testing Considerations

Database testing includes performance validation to prevent regression, validate optimizations, monitor resources, and ensure scalability under load.

## Usage Patterns

### Using Fixtures for Isolation

Always use function-scoped fixtures for database testing to ensure complete isolation between tests.

### Testing with Real Controllers

Test controllers through dedicated fixtures providing type safety and proper service mocking.

### Testing Business Logic

Include business logic validation and edge case testing in database test suites.

### Testing Transactions

Validate transaction behavior and rollback scenarios in database operations.

### Testing Edge Cases

Test constraint violations, concurrent operations, and error handling scenarios.

## Best Practices

### Use Fixtures for All Database Tests

Consistent fixture usage ensures isolation, type safety, and reliable test execution.

### Isolate Tests with Function-Scoped Fixtures

Function-scoped fixtures provide maximum isolation and prevent cross-test contamination.

### Test Both Success and Error Cases

Include validation of business rules, data integrity checks, and error condition handling.

### Clean Up Test Data Properly

Automatic fixture cleanup ensures no test data leakage between test runs.

### Use Realistic Test Data

Test with realistic data patterns that match production usage scenarios.

### Test Performance Characteristics

Include performance validation to catch regression and ensure scalability.

### Mock External Dependencies

Isolate database testing by mocking external services and dependencies.

### Use Appropriate Test Markers

Mark tests by type (unit/integration), performance characteristics, and requirements.

### Document Test Intent

Clear test documentation explaining the purpose and validation being performed.

## Related Topics

- [Database Controllers](controllers.md) - Controller testing patterns and fixtures
- [Database Service](service.md) - Service layer testing approaches
- [Database Architecture](architecture.md) - Overall testing strategy in architecture
- [Testing Best Practices](../../best-practices/testing/index.md) - General testing guidelines
