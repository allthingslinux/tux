# Implementation Guidelines and Standards

## Overview

This document provides comprehensive guidelines and standards for implementing improvements to the Tux Discord bot codebase. These guidelines ensure consistency, maintainability, and quality across all code contributions.

## Table of Contents

1. [Coding Standards](#coding-standards)
2. [Architecture Patterns](#architecture-patterns)
3. [Implementation Checklists](#implementation-checklists)
4. [Code Review Criteria](#code-review-criteria)
5. [Quality Gates](#quality-gates)
6. [Testing Standards](#testing-standards)
7. [Documentation Requirements](#documentation-requirements)

## Coding Standards

### General Principles

#### Code Quality Standards

- **DRY (Don't Repeat Yourself)**: Eliminate code duplication through abstraction
- **SOLID Principles**: Follow Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion
- **Clean Code**: Write self-documenting code with meaningful names and clear structure
- **Type Safety**: Use comprehensive type hints and leverage mypy for static analysis

#### Naming Conventions

- **Classes**: PascalCase (e.g., `DatabaseService`, `EmbedCreator`)
- **Functions/Methods**: snake_case (e.g., `create_embed`, `handle_error`)
- **Variables**: snake_case (e.g., `user_id`, `embed_color`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: Leading underscore (e.g., `_internal_method`, `_cache`)

#### File Organization

```
tux/
├── core/           # Core framework components
├── cogs/           # Discord command modules
├── database/       # Data access layer
├── services/       # Business logic services
├── utils/          # Utility functions and helpers
├── ui/             # User interface components
└── handlers/       # Event and error handlers
```

### Python-Specific Standards

#### Import Organization

```python
# Standard library imports
import asyncio
from datetime import datetime
from typing import Any, Optional

# Third-party imports
import discord
from discord.ext import commands
from loguru import logger

# Local imports
from tux.core.interfaces import IService
from tux.database.controllers import DatabaseController
from tux.utils.exceptions import CustomError
```

#### Type Hints

```python
# Always use type hints for funignatures
async def create_case(
    self,
    guild_id: int,
    user_id: int,
    moderator_id: int,
    case_type: CaseType,
    reason: str,
    expires_at: datetime | None = None,
) -> Case | None:
    """Create a moderation case with proper typing."""
    pass

# Use generic types for collections
def process_users(users: list[discord.User]) -> dict[int, str]:
    """Process users and return mapping."""
    pass
```

#### Error Handling

```python
# Use specific exception types
try:
    result = await risky_operation()
except DatabaseError as e:
    logger.error(f"Database operation failed: {e}")
    raise ServiceError("Failed to process request") from e
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    return None

# Always log errors with context
logger.error(
    "Failed to ban user",
    user_id=user.id,
    guild_id=guild.id,
    error=str(e),
    extra={"operation": "ban_user"}
)
```

## Architecture Patterns

### Dependency Injection Pattern

#### Service Registration

```python
# In main application setup
container = ServiceContainer()
container.register_singleton(IDatabaseService, DatabaseService)
container.register_singleton(IEmbedService, EmbedService)
container.register_transient(IValidationService, ValidationService)
```

#### Service Consumption

```python
class ModerationCog(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Services are automatically injected via BaseCog
        
    async def ban_user(self, user: discord.User, reason: str) -> None:
        # Use injected services
        if not self.validation_service.validate_reason(reason):
            raise ValidationError("Invalid reason")
            
        await self.moderation_service.ban_user(user, reason)
```

### Repository Pattern

#### Interface Definition

```python
class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        pass
        
    @abstractmethod
    async def create(self, user_data: UserCreateData) -> User:
        """Create new user."""
        pass
```

#### Implementation

```python
class UserRepository(IUserRepository):
    def __init__(self, db_client: DatabaseClient) -> None:
        self.db = db_client
        
    async def get_by_id(self, user_id: int) -> User | None:
        try:
            return await self.db.client.user.find_unique(
                where={"id": user_id}
            )
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise RepositoryError("Failed to retrieve user") from e
```

### Service Layer Pattern

#### Service Interface

```python
class IModerationService(ABC):
    @abstractmethod
    async def ban_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        duration: timedelta | None = None,
    ) -> ModerationResult:
        """Ban a user from the guild."""
        pass
```

#### Service Implementation

```python
class ModerationService(IModerationService):
    def __init__(
        self,
        user_repo: IUserRepository,
        case_repo: ICaseRepository,
        notification_service: INotificationService,
    ) -> None:
        self.user_repo = user_repo
        self.case_repo = case_repo
        self.notification_service = notification_service
        
    async def ban_user(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
        duration: timedelta | None = None,
    ) -> ModerationResult:
        # Business logic implementation
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
            
        # Create case record
        case = await self.case_repo.create_case(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            case_type=CaseType.BAN,
            reason=reason,
            expires_at=datetime.utcnow() + duration if duration else None,
        )
        
        # Send notification
        await self.notification_service.notify_user_banned(user, reason)
        
        return ModerationResult(success=True, case=case)
```

### Error Handling Pattern

#### Custom Exception Hierarchy

```python
class TuxError(Exception):
    """Base exception for Tux bot."""
    pass

class ServiceError(TuxError):
    """Base service layer error."""
    pass

class ValidationError(ServiceError):
    """Validation failed error."""
    pass

class DatabaseError(TuxError):
    """Database operation error."""
    pass

class ExternalAPIError(TuxError):
    """External API error."""
    def __init__(self, service: str, status_code: int, message: str):
        self.service = service
        self.status_code = status_code
        super().__init__(f"{service} API error ({status_code}): {message}")
```

#### Error Handler Implementation

```python
class ErrorHandler:
    def __init__(self, logger: Logger, sentry_service: ISentryService):
        self.logger = logger
        self.sentry = sentry_service
        
    async def handle_command_error(
        self,
        ctx: commands.Context,
        error: Exception,
    ) -> None:
        """Handle command errors with appropriate responses."""
        if isinstance(error, ValidationError):
            await self._send_user_error(ctx, str(error))
        elif isinstance(error, DatabaseError):
            self.logger.error("Database error in command", error=error, command=ctx.command.name)
            self.sentry.capture_exception(error)
            await self._send_system_error(ctx)
        else:
            self.logger.error("Unexpected error in command", error=error, command=ctx.command.name)
            self.sentry.capture_exception(error)
            await self._send_system_error(ctx)
```

## Implementation Checklists

### New Cog Implementation Checklist

- [ ] **Inheritance**: Extends appropriate base class (`BaseCog`, `ModerationBaseCog`, etc.)
- [ ] **Dependency Injection**: Uses injected services instead of direct instantiation
- [ ] **Type Hints**: All methods have complete type annotations
- [ ] **Error Handling**: Implements proper error handling with custom exceptions
- [ ] **Logging**: Includes appropriate logging statements with context
- [ ] **Documentation**: Has comprehensive docstrings for all public methods
- [ ] **Testing**: Includes unit tests with >80% coverage
- [ ] **Validation**: Input validation using service layer
- [ ] **Permissions**: Proper permission checks using decorators
- [ ] **Async Patterns**: Correct async/await usage throughout

### Service Implementation Checklist

- [ ] **Interface**: Implements defined interface contract
- [ ] **Constructor Injection**: Dependencies injected via constructor
- [ ] **Single Responsibility**: Focused on single business domain
- [ ] **Error Handling**: Converts low-level errors to domain errors
- [ ] **Logging**: Structured logging with correlation IDs
- [ ] **Validation**: Input validation at service boundaries
- [ ] **Transaction Management**: Proper database transaction handling
- [ ] **Testing**: Comprehensive unit tests with mocking
- [ ] **Documentation**: Clear API documentation
- [ ] **Performance**: Considers caching and optimization

### Database Changes Checklist

- [ ] **Migration Script**: Prisma migration created and tested
- [ ] **Backward Compatibility**: Changes don't break existing code
- [ ] **Indexing**: Appropriate database indexes added
- [ ] **Constraints**: Data integrity constraints defined
- [ ] **Repository Updates**: Repository interfaces updated
- [ ] **Service Updates**: Service layer updated for new schema
- [ ] **Testing**: Database tests updated
- [ ] **Documentation**: Schema changes documented
- [ ] **Performance Testing**: Query performance validated
- [ ] **Rollback Plan**: Rollback procedure documented

### UI Component Checklist

- [ ] **Accessibility**: Follows Discord accessibility guidelines
- [ ] **Consistency**: Uses standard embed templates and colors
- [ ] **Responsiveness**: Works across different Discord clients
- [ ] **Error States**: Handles and displays error conditions
- [ ] **Loading States**: Shows appropriate loading indicators
- [ ] **Internationalization**: Supports multiple languages (if applicable)
- [ ] **Testing**: UI components tested in isolation
- [ ] **Documentation**: Usage examples provided
- [ ] **Validation**: Input validation on interactive components
- [ ] **Security**: No sensitive data exposed in UI

## Code Review Criteria

### Mandatory Requirements

#### Code Quality

- [ ] **No Code Duplication**: DRY principle followed
- [ ] **Clear Naming**: Variables, functions, and classes have descriptive names
- [ ] **Type Safety**: Complete type hints with no `Any` types unless necessary
- [ ] **Error Handling**: All exceptions properly caught and handled
- [ ] **Logging**: Appropriate logging levels and context
- [ ] **Performance**: No obvious performance issues or inefficiencies

#### Architecture Compliance

- [ ] **Dependency Injection**: Services properly injected, not instantiated
- [ ] **Layer Separation**: Clear separation between presentation, service, and data layers
- [ ] **Interface Usage**: Code depends on interfaces, not concrete implementations
- [ ] **Single Responsibility**: Each class/method has single, clear purpose
- [ ] **Proper Abstractions**: Appropriate level of abstraction used

#### Testing Requirements

- [ ] **Unit Tests**: All new code has corresponding unit tests
- [ ] **Test Coverage**: Minimum 80% code coverage maintained
- [ ] **Integration Tests**: Critical paths have integration tests
- [ ] **Test Quality**: Tests are readable, maintainable, and reliable
- [ ] **Mocking**: External dependencies properly mocked

### Review Process

#### Pre-Review Checklist

1. **Automated Checks Pass**: All CI/CD checks green
2. **Self-Review**: Author has reviewed their own code
3. **Documentation Updated**: Relevant documentation updated
4. **Breaking Changes**: Breaking changes documented and approved

#### Review Guidelines

1. **Focus Areas**: Architecture, security, performance, maintainability
2. **Constructive Feedback**: Provide specific, actionable feedback
3. **Code Examples**: Include code examples in suggestions
4. **Approval Criteria**: At least one senior developer approval required
5. **Follow-up**: Ensure feedback is addressed before merge

## Quality Gates

### Automated Quality Gates

#### Static Analysis

```yaml
# Example GitHub Actions configuration
static_analysis:
  runs-on: ubuntu-latest
  steps:
    - name: Run mypy
      run: mypy tux/ --strict
    - name: Run ruff
      run: ruff check tux/
    - name: Run bandit
      run: bandit -r tux/
```

#### Test Coverage

```yaml
test_coverage:
  runs-on: ubuntu-latest
  steps:
    - name: Run tests with coverage
      run: pytest --cov=tux --cov-report=xml --cov-fail-under=80
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

#### Performance Testing

```yaml
performance_tests:
  runs-on: ubuntu-latest
  steps:
    - name: Run performance tests
      run: pytest tests/performance/ --benchmark-only
    - name: Check performance regression
      run: python scripts/check_performance_regression.py
```

### Manual Quality Gates

#### Architecture Review

- [ ] **Design Patterns**: Appropriate patterns used correctly
- [ ] **Scalability**: Solution scales with expected load
- [ ] **Maintainability**: Code is easy to understand and modify
- [ ] **Security**: No security vulnerabilities introduced
- [ ] **Dependencies**: New dependencies justified and approved

#### Documentation Review

- [ ] **API Documentation**: All public APIs documented
- [ ] **Architecture Documentation**: Design decisions documented
- [ ] **User Documentation**: User-facing changes documented
- [ ] **Migration Guides**: Breaking changes have migration guides
- [ ] **Examples**: Code examples provided where appropriate

### Deployment Gates

#### Pre-Deployment

- [ ] **All Tests Pass**: Unit, integration, and performance tests pass
- [ ] **Security Scan**: Security vulnerabilities addressed
- [ ] **Performance Baseline**: Performance meets baseline requirements
- [ ] **Database Migrations**: Migrations tested and approved
- [ ] **Rollback Plan**: Rollback procedure documented and tested

#### Post-Deployment

- [ ] **Health Checks**: All health checks passing
- [ ] **Monitoring**: Metrics and alerts configured
- [ ] **Error Rates**: Error rates within acceptable limits
- [ ] **Performance**: Response times within SLA
- [ ] **User Feedback**: No critical user-reported issues

## Acceptance Criteria Templates

### Feature Implementation Template

```markdown
## Acceptance Criteria

### Functional Requirements
- [ ] Feature works as specified in requirements
- [ ] All user scenarios covered
- [ ] Error cases handled appropriately
- [ ] Performance requirements met

### Technical Requirements
- [ ] Code follows architectural patterns
- [ ] Proper error handling implemented
- [ ] Logging and monitoring added
- [ ] Security considerations addressed

### Quality Requirements
- [ ] Unit tests written and passing
- [ ] Integration tests cover critical paths
- [ ] Code coverage >80%
- [ ] Documentation updated

### Deployment Requirements
- [ ] Database migrations (if applicable)
- [ ] Configuration changes documented
- [ ] Rollback procedure defined
- [ ] Monitoring alerts configured
```

### Bug Fix Template

```markdown
## Acceptance Criteria

### Fix Verification
- [ ] Root cause identified and addressed
- [ ] Original issue no longer reproducible
- [ ] No regression in related functionality
- [ ] Fix works across all supported environments

### Quality Assurance
- [ ] Test case added to prevent regression
- [ ] Code review completed
- [ ] Security implications considered
- [ ] Performance impact assessed

### Documentation
- [ ] Bug fix documented in changelog
- [ ] Known issues updated (if applicable)
- [ ] User communication prepared (if needed)
```

## Conclusion

These implementation guidelines and standards ensure consistent, high-quality code across the Tux Discord bot project. All contributors should familiarize themselves with these standards and use the provided checklists and templates to maintain code quality and architectural integrity.

For questions or clarifications about these guidelines, please refer to the project documentation or reach out to the development team.
