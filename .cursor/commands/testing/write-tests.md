# Write Tests

## Overview

Create comprehensive tests that verify business logic and behavior, not just implementation.

Tests should follow the Arrange-Act-Assert-Cleanup pattern, test one feature at a time, and validate that code behaves correctly according to requirements. Works for unit tests, integration tests, and other test types.

## Steps

1. **Understand What to Test**
   - Identify the behavior being tested (what the code does, not how)
   - Determine business requirements and specifications
   - Focus on meaningful business logic, not trivial code
   - Test requirements, not coverage metrics
   - Determine test type (unit, integration, etc.) and use appropriate markers

2. **Test Structure (ACT Pattern)**
   - **Arrange**: Set up test data, mocks, and preconditions
   - **Act**: Execute the code under test (single, state-changing action)
   - **Assert**: Verify business outcomes (behavior exists between Act and Assert)
   - **Cleanup**: Handled automatically by fixtures (no manual cleanup needed)

3. **Write Test Cases**
   - **One feature per test**: Each test should focus on one behavior
   - **Single assertion**: One assertion per test (or related assertions for one concept)
   - **Descriptive names**: Test names should read like specifications (e.g., `test_permission_system_denies_access_when_user_lacks_required_role`)
   - **Happy path**: Test successful behavior
   - **Edge cases**: Test error handling and boundary conditions
   - **Error conditions**: Test that errors are handled gracefully

4. **Mocking and Isolation**
   - Mock dependencies you don't want to test
   - Use `spec=` or `autospec=True` for type-safe mocks
   - Isolate tests from external dependencies
   - Use fixtures for shared setup (DRY principle)

5. **Test Quality**
   - Test behavior, not implementation details
   - Make tests independent and isolated
   - Ensure tests are deterministic and repeatable
   - Use `@pytest.mark.parametrize` for multiple inputs/outputs
   - Follow project conventions (markers, type hints, docstrings)

6. **Add Appropriate Markers**
   - `@pytest.mark.unit` for unit tests (fast, isolated)
   - `@pytest.mark.integration` for integration tests (multiple components)
   - `@pytest.mark.asyncio` for async tests
   - `@pytest.mark.slow` for slow tests (>5 seconds)
   - Combine markers as needed

## Test Example

```python
@pytest.mark.unit
async def test_user_ban_creates_case_record(
    moderation_coordinator: ModerationCoordinator,
    mock_ctx: commands.Context[Tux],
    db_service: DatabaseService,
) -> None:
    """Test that banning a user creates a case record in the database."""
    # Arrange
    user = MockMember(id=12345)
    reason = "Spam and harassment"

    # Act
    await moderation_coordinator.execute_moderation_action(
        ctx=mock_ctx,
        case_type=DBCaseType.BAN,
        user=user,
        reason=reason,
        actions=[(mock_ban_action, type(None))],
    )

    # Assert - Verify business outcome
    async with db_service.session() as session:
        case = await session.get(Case, (TEST_GUILD_ID, 1))
        assert case is not None
        assert case.case_type == DBCaseType.BAN
        assert case.case_reason == reason
        assert case.case_user_id == user.id
    # Cleanup - Handled automatically by fixtures
```

## Integration Test Example

```python
@pytest.mark.integration
async def test_moderation_workflow_creates_case_and_executes_action(
    moderation_coordinator: ModerationCoordinator,
    db_service: DatabaseService,
    mock_ctx: commands.Context[Tux],
) -> None:
    """Test complete moderation workflow: case creation + action execution."""
    # Arrange
    user = MockMember(id=12345)
    reason = "Violation of rules"

    # Act
    await moderation_coordinator.execute_moderation_action(
        ctx=mock_ctx,
        case_type=DBCaseType.BAN,
        user=user,
        reason=reason,
        actions=[(mock_ban_action, type(None))],
    )

    # Assert - Verify business outcome
    async with db_service.session() as session:
        case = await session.get(Case, (TEST_GUILD_ID, 1))
        assert case is not None
        assert case.case_type == DBCaseType.BAN
        assert case.case_reason == reason
```

## Error Handling

If tests fail:

- Review error messages and tracebacks
- Check fixture setup and teardown
- Verify database state if using database fixtures
- Ensure async tests use `@pytest.mark.asyncio`
- Verify mocks are set up correctly with proper `spec=` or `autospec=True`

## Write Tests Checklist

- [ ] Identified behavior being tested (what, not how)
- [ ] Test follows Arrange-Act-Assert-Cleanup pattern
- [ ] One feature per test with single assertion
- [ ] Descriptive test name that reads like a specification
- [ ] Tests business logic, not implementation details
- [ ] Covered happy path scenarios
- [ ] Covered edge cases and error conditions
- [ ] Mocked external dependencies with `spec=` or `autospec=True`
- [ ] Used fixtures for shared setup (DRY)
- [ ] Tests are independent and isolated
- [ ] Used appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.asyncio`)
- [ ] Added type hints and docstrings
- [ ] Tests verify requirements, not just coverage

## See Also

- Related rule: @testing/test-quality.mdc - Test quality philosophy and ACT pattern
- Related rule: @testing/pytest.mdc - Pytest configuration and structure
- Related rule: @testing/fixtures.mdc - Fixture patterns
- Related rule: @testing/markers.mdc - Test marker conventions
- Related rule: @testing/async.mdc - Async testing patterns
- Related command: `/run-tests` - Run tests and fix failures
- Related command: `/test-coverage` - Check test coverage
- Related command: `/audit-and-fix-tests` - Audit and fix test compliance
