# Audit and Fix Tests

## Overview

Automatically audit and fix test files to ensure they follow Tux project testing standards, style guide, and best practices. This command identifies issues and fixes them automatically, ensuring tests are compliant with all rules.

## Steps

1. **Identify Test Files**
   - Find all test files in `tests/` directory
   - Identify test files matching the target (if specified)
   - List all test files to audit and fix

2. **Fix Test Quality Issues**
   - **ACT Pattern**: Ensure Arrange-Act-Assert-Cleanup structure
     - Add clear Arrange, Act, Assert comments if missing
     - Verify cleanup is handled by fixtures (remove manual cleanup)
   - **Behavior-Driven**: Ensure tests validate behavior, not implementation
     - Refactor assertions to validate business outcomes
     - Remove tests that check internal methods or private attributes
   - **One Feature Per Test**: Split tests that cover multiple features
     - Identify tests with multiple unrelated assertions
     - Split into separate tests, one per feature
   - **Descriptive Names**: Rename vague test names
     - Pattern: `test_<what>_<when>_<expected_outcome>`
     - Rename vague names like `test_works`, `test_function` to descriptive names

3. **Fix Style Guide Issues**
   - **Type Hints**: Add type hints to all test function parameters
   - **Docstrings**: Add docstrings to all test functions
   - **Naming**: Ensure test names follow `snake_case` convention
   - **Imports**: Fix import organization (stdlib → third-party → local)
   - **Line Length**: Fix lines exceeding 88 characters (with exceptions)
   - **Code Style**: Apply style guide patterns

4. **Fix Testing Rules Issues**
   - **Markers**: Add missing markers
     - Add `@pytest.mark.unit` for unit tests
     - Add `@pytest.mark.integration` for integration tests
     - Add `@pytest.mark.asyncio` for async tests
     - Add `@pytest.mark.slow` for slow tests (>5 seconds)
   - **Fixtures**: Fix fixture issues
     - Add type hints to fixtures
     - Add docstrings to fixtures
     - Ensure appropriate scope (session, function)
   - **Async Tests**: Add `@pytest.mark.asyncio` to async tests missing it
   - **Mocking**: Fix mocking practices
     - Add `spec=` or `autospec=True` to `MagicMock()`` calls
     - Update `mocker.patch()` calls to use `autospec=True`
   - **DRY**: Fix code duplication
     - Extract shared setup to fixtures
     - Convert repeated test cases to `@pytest.mark.parametrize`

5. **Fix Best Practices Issues**
   - **Isolation**: Ensure tests don't depend on each other
   - **Deterministic**: Fix non-deterministic tests
   - **Fast Unit Tests**: Optimize slow unit tests
   - **Assertions**: Make assertions clear and meaningful
   - **Error Handling**: Add tests for error conditions if missing
   - **Edge Cases**: Add tests for boundary conditions if missing

6. **Remove Anti-Patterns**
   - Remove tests that test implementation details
   - Remove tests that test trivial code (simple getters/setters)
   - Remove tests that test framework code (SQLModel, discord.py)
   - Fix vague test names
   - Fix missing ACT structure
   - Fix unspecified mocks
   - Remove repeated test code (use fixtures/parametrize)
   - Split tests with multiple features

7. **Verify Fixes**
   - Run tests to ensure fixes don't break functionality
   - Verify all tests still pass
   - Check that fixes follow all rules
   - Ensure no regressions introduced

## Fixes Applied

### Missing Markers

**Fix**: Add appropriate marker before test function

```python
# Before
async def test_permission_check(...) -> None:

# After
@pytest.mark.unit
async def test_permission_check(...) -> None:
```

### Missing Type Hints

**Fix**: Add type hints to all parameters

```python
# Before
async def test_function(db_service, mock_ctx) -> None:

# After
async def test_function(
    db_service: DatabaseService,
    mock_ctx: commands.Context[Tux],
) -> None:
```

### Missing Docstrings

**Fix**: Add docstring describing what the test validates

```python
# Before
async def test_permission_check(...) -> None:
    # Test code

# After
async def test_permission_check(...) -> None:
    """Test that permission check validates user has required role."""
    # Test code
```

### Vague Test Names

**Fix**: Rename to descriptive name

```python
# Before
def test_works(...) -> None:

# After
def test_permission_system_denies_access_when_user_lacks_required_role(...) -> None:
```

### Missing ACT Structure

**Fix**: Add clear Arrange, Act, Assert sections

```python
# Before
async def test_function(...) -> None:
    result = await some_function()
    assert result == expected

# After
async def test_function(...) -> None:
    # Arrange
    expected = "value"
    
    # Act
    result = await some_function()
    
    # Assert
    assert result == expected
```

### Unspecified Mocks

**Fix**: Add `spec=` or `autospec=True`

```python
# Before
mock_service = MagicMock()

# After
mock_service = MagicMock(spec=ServiceClass)

# Or for mocker.patch
# Before
mocker.patch("module.function", return_value=5)

# After
mocker.patch("module.function", return_value=5, autospec=True)
```

### Testing Implementation Details

**Fix**: Refactor to test behavior/outcomes

```python
# Before
def test_coordinator_calls_service():
    coordinator.execute_action(...)
    mock_service.create.assert_called_once()  # Implementation detail

# After
def test_action_creates_case_record():
    # Arrange
    # Act
    await coordinator.execute_action(...)
    # Assert - Verify business outcome
    case = await db_service.get_case(...)
    assert case is not None
```

### Missing Async Marker

**Fix**: Add `@pytest.mark.asyncio` decorator

```python
# Before
async def test_async_function(...) -> None:

# After
@pytest.mark.asyncio
async def test_async_function(...) -> None:
```

### Multiple Features Per Test

**Fix**: Split into separate tests

```python
# Before
def test_dict():
    assert make_dict(2, 3) == {"a": 2, "b": 3, "result": 5}
    with pytest.raises(ValueError):
        make_dict(-1, -1)

# After
def test_make_dict_returns_expected():
    assert make_dict(2, 3) == {"a": 2, "b": 3, "result": 5}

def test_make_dict_raises_error_with_negative():
    with pytest.raises(ValueError):
        make_dict(-1, -1)
```

### Repeated Test Code

**Fix**: Extract to fixtures or parametrize

```python
# Before
def test_person_is_adult():
    person = Person("Emi")
    person.age = 19
    assert person.is_adult()

def test_person_is_not_adult():
    person = Person("Emi")  # Repeated
    person.age = 10
    assert not person.is_adult()

# After
@pytest.fixture
def person() -> Person:
    """Shared person fixture."""
    return Person("Emi")

def test_person_is_adult(person: Person):
    person.age = 19
    assert person.is_adult()

def test_person_is_not_adult(person: Person):
    person.age = 10
    assert not person.is_adult()
```

## Error Handling

If fixes fail:

- **Syntax Errors**: Review and fix manually
- **Test Failures**: Verify fixes don't break functionality
- **Complex Refactoring**: May require manual intervention
- **Conflicting Patterns**: Choose best approach and document

## Checklist

- [ ] All test files identified
- [ ] Test quality issues fixed (ACT pattern, behavior-driven)
- [ ] Style guide issues fixed (type hints, docstrings, naming)
- [ ] Testing rules issues fixed (markers, fixtures, async, mocking)
- [ ] Best practices issues fixed (isolation, deterministic, fast)
- [ ] Anti-patterns removed
- [ ] All fixes verified (tests still pass)
- [ ] No regressions introduced

## See Also

- Related rule: @testing/test-quality.mdc - Test quality philosophy and ACT pattern
- Related rule: @testing/pytest.mdc - Pytest configuration and structure
- Related rule: @testing/fixtures.mdc - Fixture patterns
- Related rule: @testing/markers.mdc - Test marker conventions
- Related rule: @testing/async.mdc - Async testing patterns
- Related rule: @core/style-guide.mdc - Python code style guide
- Related command: `/write-tests` - Create new tests
- Related command: `/run-tests` - Run tests and fix failures
- Related command: `/test-coverage` - Check test coverage
