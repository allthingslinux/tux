# ADR-001: Dependency Injection Strategy

## Status

Accepted

## Context

The current Tux Discord bot codebase suffers from tight coupling and repetitive initialization patterns. Every cog follows the same pattern:

```python
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()
```

This pattern appears in 40+ cog files, creating several problems:

- Violates DRY principles with repeated boilerplate code
- Creates tight coupling between cogs and concrete implementations
- Makes unit testing difficult due to hard dependencies
- Complicates service lifecycle management
- Reduces code maintainability and flexibility

The codebase needs a dependency injection strategy that reduces coupling while maintaining the modular cog architecture that provides excellent hot-reload capabilities.

## Decision

Implement a lightweight service container with constructor injection for cogs and services. The solution will:

1. Create a `ServiceContainer` class that manages service registration and resolution
2. Use constructor injection to provide dependencies to cogs
3. Support both singleton and transient service lifetimes
4. Maintain backward compatibility during transition
5. Integrate with the existing cog loader system

## Rationale

Constructor injection was chosen because it:

- Makes dependencies explicit and testable
- Enables compile-time dependency validation
- Supports immutable service references
- Integrates well with Python's type system
- Maintains clear separation of concerns

A lightweight custom container was preferred over heavy frameworks because:

- Minimal overhead and complexity
- Full control over service resolution
- Easy integration with discord.py's cog system
- No external dependencies required
- Tailored to bot-specific needs

## Alternatives Considered

### Alternative 1: Property Injection

- Description: Inject dependencies through properties after object creation
- Pros: Simpler to implement, no constructor changes needed
- Cons: Dependencies not guaranteed at construction time, mutable references, harder to test
- Why rejected: Reduces reliability and testability

### Alternative 2: Service Locator Pattern

- Description: Global service registry that objects query for dependencies
- Pros: Easy to implement, minimal code changes
- Cons: Hidden dependencies, harder to test, violates dependency inversion principle
- Why rejected: Creates hidden coupling and testing difficulties

### Alternative 3: Third-party DI Framework (e.g., dependency-injector)

- Description: Use existing Python DI framework
- Pros: Battle-tested, feature-rich, well-documented
- Cons: External dependency, learning curve, potential overkill for bot needs
- Why rejected: Adds complexity and external dependencies for limited benefit

## Consequences

### Positive

- Eliminates repetitive initialization boilerplate across 40+ cogs
- Enables proper unit testing through dependency mocking
- Improves code maintainability and flexibility
- Supports better service lifecycle management
- Enables easier configuration and environment-specific services

### Negative

- Requires refactoring of existing cog constructors
- Adds complexity to the cog loading process
- Team needs to learn dependency injection concepts
- Potential performance overhead from service resolution

### Neutral

- Changes to cog initialization patterns
- New service registration requirements
- Updated development workflow for new cogs

## Implementation

### Phase 1: Core Infrastructure

1. Create `ServiceContainer` class with registration and resolution methods
2. Implement service lifetime management (singleton, transient)
3. Add type-safe service resolution with generic methods
4. Create service registration decorators for convenience

### Phase 2: Integration

1. Modify cog loader to use service container for dependency injection
2. Create adapter pattern for backward compatibility
3. Update base cog classes to support injected dependencies
4. Implement service interfaces for major components

### Phase 3: Migration

1. Migrate core services (database, configuration, logging) to container
2. Update existing cogs to use constructor injection
3. Remove direct instantiation of services from cogs
4. Add comprehensive tests for service resolution

### Success Criteria

- All cogs use constructor injection for dependencies
- Service container handles all major service lifecycles
- Unit tests can easily mock dependencies
- No performance regression in cog loading times

## Compliance

### Code Review Guidelines

- All new cogs must use constructor injection
- Services must be registered in the container
- Direct instantiation of services in cogs is prohibited
- Dependency interfaces should be preferred over concrete types

### Automated Checks

- Linting rules to detect direct service instantiation in cogs
- Type checking to ensure proper dependency injection usage
- Unit tests must demonstrate mockable dependencies

### Documentation Requirements

- Service registration examples in developer documentation
- Dependency injection patterns guide
- Migration guide for existing cogs

## Related Decisions

- [ADR-002](002-service-layer-architecture.md): Service Layer Architecture
- [ADR-004](004-database-access-patterns.md): Database Access Patterns
- Requirements 3.2, 10.1, 10.2, 1.3

## Notes

This decision builds on the existing modular cog architecture while addressing its coupling issues. The implementation should be incremental to maintain system stability during the transition.

---

**Date**: 2025-01-26  
**Author(s)**: Development Team  
**Reviewers**: Architecture Team  
**Last Updated**: 2025-01-26
