# Service Layer Architecture Plan

## Executive Summary

This document outlines a comprehensive plan for implementing a service layer architecture in the Tux Discord bot codebase. The plan addresses the current issues of tight coupling, code duplication, and mixed concerns by introducing clear architectural layers with well-defined responsibilities and interfaces.

## Current Architecture Analysis

### Existing Patterns

#### Strengths

- **Modular Cog System**: The current cog-based architecture provides excellent modularity and hot-reload capabilities
- **Comprehensive Database Layer**: Prisma-based ORM with BaseController provides type safety and good query building
- **Monitoring Integration**: Extensive Sentry integration provides observability
- **Async/Await Usage**: Proper async patterns throughout the codebase

#### Issues Identified

- **Repetitive Initialization**: Every cog follows the same pattern: `self.bot = bot; self.db = DatabaseController()`
- **Mixed Concerns**: Cogs contain both presentation logic (Discord interactions) and business logic (data processing)
- **Tight Coupling**: Direct database access in cogs creates coupling and testing difficulties
- **Code Duplication**: Similar patterns repeated across cogs (embed creation, validation, error handling)

## Proposed Service Layer Architecture

### 1. Architectural Layers

#### 1.1 Presentation Layer (Cogs)

**Responsibility**: Handle Discord interactions only

- Process Discord commands and events
- Validate user input and permissions
- Format responses for Discord
- Delegate business logic to services

**Current State**: Mixed concerns with business logic
**Target State**: Pure presentation layer focused on Discord API interactions

#### 1.2 Application Layer (Services)

**Responsibility**: Orchestrate business workflows

- Coordinate between domain services
- Handle cross-cutting concerns (logging, caching)
- Manage transactions and error handling
- Implement use cases and business workflows

**Current State**: Non-existent - logic embedded in cogs
**Target State**: Well-defined services for each business domain

#### 1.3 Domain Layer (Business Logic)

**Responsibility**: Core business rules and logic

- Domain models and entities
- Business rules validation
- Domain-specific calculations
- Pure business logic without external dependencies

**Current State**: Scattered throughout cogs
**Target State**: Centralized domain logic with clear boundaries

#### 1.4 Infrastructure Layer (Data Access & External Services)

**Responsibility**: External system interactions

- Database operations (existing controllers)
- External API calls
- File system operations
- Configuration management

**Current State**: Good foundation with BaseController
**Target State**: Enhanced with repository pattern and better abstraction

### 2. Service Interface Design

#### 2.1 Core Service Interfaces

```python
# Base service interface
class IService(Protocol):
    """Base interface for all services"""
    pass

# Domain-specific service interfaces
class IModerationService(IService):
    async def ban_user(self, guild_id: int, user_id: int, moderator_id: int, reason: str, duration: Optional[datetime] = None) -> ModerationResult
    async def unban_user(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> ModerationResult
    async def check_user_restrictions(self, guild_id: int, user_id: int) -> UserRestrictions

class ISnippetService(IService):
    async def create_snippet(self, guild_id: int, name: str, content: str, author_id: int) -> SnippetResult
    async def get_snippet(self, guild_id: int, name: str) -> Optional[Snippet]
    async def delete_snippet(self, guild_id: int, snippet_id: int, user_id: int) -> bool

class ILevelService(IService):
    async def add_experience(self, guild_id: int, user_id: int, amount: int) -> LevelResult
    async def get_user_level(self, guild_id: int, user_id: int) -> UserLevel
    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[UserLevel]
```

#### 2.2 Service Contracts

Each service will define clear contracts including:

- Input validation requirements
- Expected return types
- Error conditions and handling
- Transaction boundaries
- Caching strategies

### 3. Dependency Injection Strategy

#### 3.1 Service Container Implementation

```python
class ServiceContainer:
    """Lightweight dependency injection container"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service"""
        
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service"""
        
    def get(self, interface: Type[T]) -> T:
        """Resolve a service instance"""
```

#### 3.2 Service Registration

Services will be registered at application startup:

```python
# Service registration
container = ServiceContainer()
container.register_singleton(IModerationService, ModerationService)
container.register_singleton(ISnippetService, SnippetService)
container.register_singleton(ILevelService, LevelService)
```

#### 3.3 Cog Integration

Cogs will receive services through constructor injection:

```python
class BanCog(commands.Cog):
    def __init__(self, bot: Tux, moderation_service: IModerationService):
        self.bot = bot
        self.moderation_service = moderation_service
    
    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason: str):
        result = await self.moderation_service.ban_user(
            guild_id=ctx.guild.id,
            user_id=member.id,
            moderator_id=ctx.author.id,
            reason=reason
        )
        await self._handle_moderation_result(ctx, result)
```

### 4. Business Logic Extraction Strategy

#### 4.1 Moderation Services

**Current State**: Business logic scattered across moderation cogs
**Target Services**:

- `ModerationService`: Core moderation operations
- `CaseService`: Case management and tracking
- `RestrictionService`: User restriction checking

**Extraction Plan**:

1. Extract case creation logic from `ModerationCogBase`
2. Create `ModerationService` with ban/kick/timeout operations
3. Implement `RestrictionService` for checking user states
4. Update cogs to use services instead of direct database access

#### 4.2 Snippet Services

**Current State**: Snippet logic in individual cog files
**Target Services**:

- `SnippetService`: CRUD operations for snippets
- `SnippetValidationService`: Name and content validation
- `SnippetPermissionService`: Permission checking

**Extraction Plan**:

1. Extract snippet CRUD operations from cogs
2. Create validation service for snippet rules
3. Implement permission checking service
4. Update cogs to use services

#### 4.3 Level Services

**Current State**: Level logic in level cogs
**Target Services**:

- `LevelService`: Experience and level calculations
- `LeaderboardService`: Ranking and statistics
- `LevelEventService`: Level-up event handling

**Extraction Plan**:

1. Extract level calculation logic
2. Create leaderboard generation service
3. Implement event handling for level-ups
4. Update cogs to use services

### 5. Common Functionality Extraction

#### 5.1 Embed Factory Service

**Purpose**: Centralize embed creation patterns
**Interface**:

```python
class IEmbedService(IService):
    def create_success_embed(self, title: str, description: str, **kwargs) -> discord.Embed
    def create_error_embed(self, title: str, description: str, **kwargs) -> discord.Embed
    def create_moderation_embed(self, case_type: CaseType, case_number: int, **kwargs) -> discord.Embed
```

#### 5.2 Validation Service

**Purpose**: Centralize common validation patterns
**Interface**:

```python
class IValidationService(IService):
    def validate_user_permissions(self, user: discord.Member, required_level: int) -> ValidationResult
    def validate_input_length(self, input_str: str, max_length: int) -> ValidationResult
    def validate_snippet_name(self, name: str) -> ValidationResult
```

#### 5.3 Notification Service

**Purpose**: Handle DM sending and notifications
**Interface**:

```python
class INotificationService(IService):
    async def send_moderation_dm(self, user: discord.User, action: str, reason: str, guild: discord.Guild) -> bool
    async def send_level_up_notification(self, user: discord.Member, new_level: int) -> bool
```

### 6. Gradual Migration Strategy

#### 6.1 Phase 1: Infrastructure Setup

**Duration**: 1-2 weeks
**Tasks**:

1. Implement service container and DI framework
2. Create base service interfaces and contracts
3. Set up service registration system
4. Create integration tests for DI container

#### 6.2 Phase 2: Core Services Implementation

**Duration**: 3-4 weeks
**Tasks**:

1. Implement `EmbedService` and `ValidationService`
2. Create `ModerationService` with basic operations
3. Implement `SnippetService` with CRUD operations
4. Update 2-3 cogs to use new services as proof of concept

#### 6.3 Phase 3: Domain Services Expansion

**Duration**: 4-5 weeks
**Tasks**:

1. Implement remaining domain services (Levels, Guild, etc.)
2. Migrate 50% of cogs to use services
3. Add comprehensive error handling and logging
4. Implement caching strategies

#### 6.4 Phase 4: Complete Migration

**Duration**: 3-4 weeks
**Tasks**:

1. Migrate remaining cogs to service architecture
2. Remove direct database access from cogs
3. Implement advanced features (transactions, events)
4. Performance optimization and monitoring

#### 6.5 Phase 5: Optimization and Cleanup

**Duration**: 2-3 weeks
**Tasks**:

1. Remove deprecated code and patterns
2. Optimize service performance
3. Add comprehensive documentation
4. Final testing and validation

### 7. Error Handling Strategy

#### 7.1 Service-Level Error Handling

Services will implement consistent error handling:

```python
class ServiceResult[T]:
    success: bool
    data: Optional[T]
    error: Optional[ServiceError]
    error_code: Optional[str]

class ServiceError:
    message: str
    error_type: ErrorType
    details: Dict[str, Any]
```

#### 7.2 Error Propagation

- Services return `ServiceResult` objects instead of raising exceptions
- Cogs handle service results and convert to appropriate Discord responses
- Centralized error logging and Sentry integration

### 8. Testing Strategy

#### 8.1 Service Testing

- Unit tests for each service with mocked dependencies
- Integration tests for service interactions
- Contract tests to ensure interface compliance

#### 8.2 Cog Testing

- Mock services for cog testing
- Focus on Discord interaction logic
- End-to-end tests for critical workflows

### 9. Performance Considerations

#### 9.1 Caching Strategy

- Service-level caching for frequently accessed data
- Cache invalidation strategies
- Memory usage monitoring

#### 9.2 Database Optimization

- Batch operations where possible
- Connection pooling optimization
- Query performance monitoring

### 10. Monitoring and Observability

#### 10.1 Service Metrics

- Service call duration and frequency
- Error rates by service
- Resource usage per service

#### 10.2 Logging Strategy

- Structured logging with service context
- Correlation IDs for request tracking
- Performance logging for slow operations

## Success Criteria

### 10.1 Code Quality Improvements

- [ ] Elimination of repetitive initialization patterns
- [ ] Clear separation of concerns between layers
- [ ] Reduced code duplication across cogs
- [ ] Improved testability with dependency injection

### 10.2 Developer Experience

- [ ] Easier to add new features with service abstractions
- [ ] Faster development with reusable services
- [ ] Better debugging with centralized error handling
- [ ] Improved onboarding with clear architecture

### 10.3 System Performance

- [ ] Maintained or improved response times
- [ ] Better resource utilization through caching
- [ ] Improved database query performance
- [ ] Enhanced monitoring and observability

### 10.4 Maintainability

- [ ] Easier to modify business logic in services
- [ ] Reduced bug introduction rate
- [ ] Faster issue resolution with better separation
- [ ] Improved code review process

## Risk Mitigation

### 10.1 Migration Risks

- **Risk**: Breaking existing functionality during migration
- **Mitigation**: Gradual migration with comprehensive testing at each phase

### 10.2 Performance Risks

- **Risk**: Service layer overhead impacting performance
- **Mitigation**: Performance benchmarking and optimization throughout implementation

### 10.3 Complexity Risks

- **Risk**: Over-engineering with too many abstractions
- **Mitigation**: Start simple and add complexity only when needed

### 10.4 Team Adoption Risks

- **Risk**: Team resistance to new patterns
- **Mitigation**: Training sessions, documentation, and gradual introduction

## Conclusion

This service layer architecture plan provides a comprehensive roadmap for transforming the Tux Discord bot codebase from its current tightly-coupled state to a well-structured, maintainable, and testable architecture. The gradual migration strategy ensures minimal disruption while delivering immediate value at each phase.

The implementation will result in:

- Clear separation of concerns between presentation, application, and domain layers
- Improved code reusability through service abstractions
- Better testability through dependency injection
- Enhanced maintainability and developer experience
- Preserved system performance and reliability

This architecture will position the codebase for future growth and make it easier for developers to contribute effectively to the project.
