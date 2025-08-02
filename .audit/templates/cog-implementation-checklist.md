# Cog Implementation Checklist

Use this checklist when implementing new cogs or modifying existing ones.

## Pre-Implementation

- [ ] **Requirements Review**: Understand the functional requirements
- [ ] **Architecture Planning**: Plan the cog structure and dependencies
- [ ] **Interface Design**: Define service interfaces needed
- [ ] **Database Schema**: Review/update database schema if needed
- [ ] **Permission Model**: Define required permissions and checks

## Implementation

### Code Structure

- [ ] **Base Class**: Extends appropriate base class (`BaseCog`, `ModerationBaseCog`, `UtilityBaseCog`)
- [ ] **Constructor**: Properly calls super().**init**(bot) and initializes services
- [ ] **Service Injection**: Uses dependency injection instead of direct instantiation
- [ ] **Import Organization**: Follows standard import order (stdlib, third-party, local)
- [ ] **File Organization**: Code organized in logical sections with clear separation

### Type Safety

- [ ] **Type Hints**: All methods have complete type annotations
- [ ] **Generic Types**: Uses appropriate generic types for collections
- [ ] **Optional Types**: Properly handles Optional/None types
- [ ] **Return Types**: All functions specify return types
- [ ] **Parameter Types**: All parameters have type hints

### Command Implementation

- [ ] **Command Decorators**: Proper use of @commands.hybrid_command or @commands.command
- [ ] **Permission Checks**: Uses appropriate permission decorators (@checks.has_pl, etc.)
- [ ] **Guild Only**: Uses @commands.guild_only() where appropriate
- [ ] **Parameter Validation**: Input parameters validated using flags or converters
- [ ] **Usage Generation**: Command usage generated using generate_usage() utility

### Error Handling

- [ ] **Exception Types**: Uses specific exception types from utils.exceptions
- [ ] **Error Logging**: Errors logged with appropriate context and level
- [ ] **User Feedback**: User-friendly error messages provided
- [ ] **Graceful Degradation**: Handles service unavailability gracefully
- [ ] **Rollback Logic**: Database operations can be rolled back on failure

### Business Logic

- [ ] **Service Layer**: Business logic implemented in service layer, not cog
- [ ] **Validation**: Input validation performed at service boundaries
- [ ] **Transaction Management**: Database operations use proper transaction handling
- [ ] **Async Patterns**: Correct async/await usage throughout
- [ ] **Resource Cleanup**: Proper cleanup of resources (connections, files, etc.)

### User Interface

- [ ] **Embed Creation**: Uses EmbedService or EmbedCreator for consistent styling
- [ ] **Response Handling**: Appropriate response types (ephemeral, public, DM)
- [ ] **Loading States**: Shows loading indicators for long operations
- [ ] **Error Display**: Error messages displayed in consistent format
- [ ] **Success Feedback**: Success messages provide clear confirmation

## Testing

### Unit Tests

- [ ] **Test Coverage**: Minimum 80% code coverage for new code
- [ ] **Command Tests**: All commands have corresponding tests
- [ ] **Service Tests**: Service layer methods tested independently
- [ ] **Error Cases**: Error conditions and edge cases tested
- [ ] **Mock Usage**: External dependencies properly mocked

### Integration Tests

- [ ] **End-to-End**: Critical user workflows tested end-to-end
- [ ] **Database Integration**: Database operations tested with real database
- [ ] **Discord Integration**: Discord API interactions tested (where possible)
- [ ] **Service Integration**: Service interactions tested
- [ ] **Permission Tests**: Permission checks tested with different user roles

### Test Quality

- [ ] **Test Naming**: Tests have descriptive names indicating what they test
- [ ] **Test Structure**: Tests follow Arrange-Act-Assert pattern
- [ ] **Test Independence**: Tests can run independently and in any order
- [ ] **Test Data**: Uses appropriate test data and fixtures
- [ ] **Assertion Quality**: Specific assertions that verify expected behavior

## Documentation

### Code Documentation

- [ ] **Docstrings**: All public methods have comprehensive docstrings
- [ ] **Parameter Documentation**: All parameters documented with types and descriptions
- [ ] **Return Documentation**: Return values documented
- [ ] **Exception Documentation**: Raised exceptions documented
- [ ] **Example Usage**: Complex methods include usage examples

### User Documentation

- [ ] **Command Help**: Commands have helpful descriptions and usage examples
- [ ] **Feature Documentation**: New features documented in user guides
- [ ] **Permission Requirements**: Permission requirements clearly documented
- [ ] **Configuration**: Any configuration requirements documented
- [ ] **Troubleshooting**: Common issues and solutions documented

## Security

### Input Validation

- [ ] **Parameter Sanitization**: All user inputs properly sanitized
- [ ] **SQL Injection**: No raw SQL queries, uses ORM properly
- [ ] **Command Injection**: No shell command execution with user input
- [ ] **Path Traversal**: File operations validate paths properly
- [ ] **Rate Limiting**: Commands implement appropriate rate limiting

### Permission Security

- [ ] **Authorization Checks**: Proper authorization checks before sensitive operations
- [ ] **Role Hierarchy**: Respects Discord role hierarchy
- [ ] **Owner Protection**: Cannot perform actions on server owner
- [ ] **Self-Action Prevention**: Users cannot perform moderation actions on themselves
- [ ] **Audit Logging**: Sensitive actions logged for audit purposes

### Data Security

- [ ] **Sensitive Data**: No sensitive data logged or exposed
- [ ] **Data Encryption**: Sensitive data encrypted at rest (if applicable)
- [ ] **Access Control**: Database access properly controlled
- [ ] **Data Retention**: Follows data retention policies
- [ ] **Privacy Compliance**: Complies with privacy requirements

## Performance

### Efficiency

- [ ] **Database Queries**: Queries optimized and use appropriate indexes
- [ ] **Batch Operations**: Multiple operations batched where possible
- [ ] **Caching**: Appropriate caching implemented for frequently accessed data
- [ ] **Resource Usage**: Efficient use of memory and CPU resources
- [ ] **Async Operations**: Long-running operations don't block event loop

### Scalability

- [ ] **Load Testing**: Performance tested under expected load
- [ ] **Resource Limits**: Respects Discord API rate limits
- [ ] **Memory Management**: No memory leaks or excessive memory usage
- [ ] **Connection Pooling**: Database connections properly pooled
- [ ] **Monitoring**: Performance metrics collected and monitored

## Deployment

### Pre-Deployment

- [ ] **Migration Scripts**: Database migrations created and tested
- [ ] **Configuration**: Required configuration documented and provided
- [ ] **Dependencies**: New dependencies added to requirements
- [ ] **Environment Variables**: Required environment variables documented
- [ ] **Rollback Plan**: Rollback procedure documented and tested

### Post-Deployment

- [ ] **Health Checks**: Cog loads and initializes properly
- [ ] **Functionality Verification**: Core functionality works as expected
- [ ] **Error Monitoring**: Error rates monitored and within acceptable limits
- [ ] **Performance Monitoring**: Performance metrics within expected ranges
- [ ] **User Feedback**: No critical issues reported by users

## Review Checklist

### Code Review

- [ ] **Architecture Compliance**: Follows established architectural patterns
- [ ] **Code Quality**: Meets code quality standards
- [ ] **Security Review**: Security implications reviewed and addressed
- [ ] **Performance Review**: Performance implications considered
- [ ] **Documentation Review**: Documentation complete and accurate

### Final Approval

- [ ] **Senior Developer Approval**: At least one senior developer has approved
- [ ] **Architecture Review**: Architecture changes approved by team lead
- [ ] **Security Approval**: Security-sensitive changes approved by security team
- [ ] **Testing Sign-off**: QA team has signed off on testing
- [ ] **Documentation Sign-off**: Documentation team has reviewed docs

---

**Note**: This checklist should be used as a guide. Not all items may apply to every cog implementation. Use judgment to determine which items are relevant for your specific implementation.
