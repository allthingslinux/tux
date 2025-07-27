# ADR-002: Service Layer Architecture

## Status

Accepted

## Context

The current Tux Discord bot architecture mixes business logic with presentation logic within cogs. This creates several maintainability and testability issues:

- Database operations are directly embedded in Discord command handlers
- Business rules are scattered across multiple cogs
- Validation logic is duplicated in presentation layer
- Testing requires mocking Discord API interactions
- Code reuse is limited due to tight coupling with Discord.py

The codebase needs clear architectural layers that separate concerns while maintaining the flexibility and modularity of the existing cog system.

## Decision

Implement a layered architecture with clear separation of concerns:

1. **Presentation Layer**: Cogs handle Discord interactions, input parsing, and response formatting only
2. **Application Layer**: Services orchestrate business workflows and coordinate between layers
3. **Domain Layer**: Core business logic, rules, and domain models
4. **Infrastructure Layer**: Database access, external APIs, and technical utilities

Services will be injected into cogs through the dependency injection system, enabling clean separation and better testability.

## Rationale

Layered architecture was chosen because it:

- Provides clear separation of concerns
- Enables independent testing of business logic
- Supports code reuse across different presentation contexts
- Follows established architectural patterns
- Maintains flexibility for future changes

The specific layer structure addresses current pain points:

- Business logic extraction from cogs improves testability
- Service orchestration enables complex workflows
- Domain models provide clear data contracts
- Infrastructure abstraction enables easier testing and configuration

## Alternatives Considered

### Alternative 1: Keep Current Mixed Architecture

- Description: Continue with business logic embedded in cogs
- Pros: No refactoring required, familiar to current team
- Cons: Poor testability, code duplication, tight coupling
- Why rejected: Doesn't address fundamental maintainability issues

### Alternative 2: Hexagonal Architecture (Ports and Adapters)

- Description: Use ports and adapters pattern with domain at center
- Pros: Very clean separation, highly testable, framework-independent
- Cons: More complex, steeper learning curve, potential over-engineering
- Why rejected: Too complex for current team size and bot requirements

### Alternative 3: CQRS (Command Query Responsibility Segregation)

- Description: Separate read and write operations with different models
- Pros: Excellent for complex domains, high performance potential
- Cons: Significant complexity, eventual consistency challenges
- Why rejected: Overkill for Discord bot domain complexity

## Consequences

### Positive

- Clear separation of concerns improves maintainability
- Business logic becomes independently testable
- Code reuse increases through service abstraction
- Easier to add new presentation interfaces (web dashboard, CLI)
- Better support for complex business workflows

### Negative

- Requires significant refactoring of existing cogs
- Increased complexity in simple operations
- Team needs to learn layered architecture concepts
- Potential performance overhead from additional abstraction layers

### Neutral

- Changes to development patterns and practices
- New service and domain model creation requirements
- Updated testing strategies for each layer

## Implementation

### Phase 1: Foundation

1. Define service interfaces for major business operations
2. Create domain models separate from database entities
3. Establish service base classes and common patterns
4. Set up dependency injection for services

### Phase 2: Core Services

1. Extract user management logic into UserService
2. Create moderation workflow services
3. Implement configuration management services
4. Build utility and helper services

### Phase 3: Cog Migration

1. Refactor cogs to use services instead of direct database access
2. Move business logic from cogs to appropriate services
3. Update cogs to focus on Discord interaction handling
4. Implement proper error handling and response formatting

### Phase 4: Advanced Features

1. Add cross-cutting concerns (logging, caching, validation)
2. Implement complex business workflows
3. Add service composition for advanced features
4. Optimize service performance and resource usage

### Success Criteria

- All business logic resides in service or domain layers
- Cogs contain only Discord interaction code
- Services are independently testable without Discord mocks
- Clear interfaces exist between all layers

## Compliance

### Code Review Guidelines

- Business logic must not appear in cog command handlers
- Services must implement defined interfaces
- Domain models should be separate from database entities
- Cross-layer dependencies must follow established patterns

### Automated Checks

- Linting rules to detect business logic in cogs
- Architecture tests to verify layer dependencies
- Interface compliance checking for services

### Documentation Requirements

- Service interface documentation with examples
- Layer responsibility guidelines
- Migration patterns for existing code

## Related Decisions

- [ADR-001](001-dependency-injection-strategy.md): Dependency Injection Strategy
- [ADR-003](003-error-handling-standardization.md): Error Handling Standardization
- [ADR-004](004-database-access-patterns.md): Database Access Patterns
- Requirements 3.3, 3.4, 10.3, 10.4

## Notes

This architecture builds on the dependency injection foundation to create a maintainable, testable system. The implementation should be incremental, starting with the most complex business logic areas.

---

**Date**: 2025-01-26  
**Author(s)**: Development Team  
**Reviewers**: Architecture Team  
**Last Updated**: 2025-01-26
