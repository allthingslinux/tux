# Run Tests

## Overview

Run tests with various scopes and filters, then fix any failures. Supports running all tests, related tests for a file, tests by marker (unit, integration, etc.), or specific test files. Focuses on ensuring tests validate business behavior correctly, not just that they pass.

## Steps

1. **Determine Test Scope**
   - **All tests**: Run full test suite (`uv run test all`)
   - **Related tests**: Find and run tests related to a source file
   - **By marker**: Run tests with specific markers (`-m unit`, `-m integration`, `-m "not slow"`)
   - **Specific file**: Run tests in a specific file or directory
   - **Quick tests**: Run fast tests only (`uv run test quick`)

2. **Find Related Tests** (if running related tests)
   - Extract file path from input
   - Determine if source file (`src/tux/`) or test file (`tests/`)
   - Parse module path (e.g., `src/tux/services/moderation/execution_service.py` → `tux.services.moderation.execution_service`)
   - Find related tests by:
     - **Module imports**: Search for `from tux.services.moderation.execution_service import`
     - **Naming pattern**: `execution_service.py` → `test_execution_service.py`
     - **Directory structure**: `src/tux/services/` → `tests/services/`
     - **Grep/search**: Search for references to module, class, or function names

3. **Run Tests**
   - Execute appropriate command:
     - All tests: `uv run test all`
     - Related tests: `uv run test file <test_paths>`
     - By marker: `uv run pytest -m <marker>`
     - Quick tests: `uv run test quick`
   - Review test results and failures
   - Identify failing tests and error messages
   - Check coverage report if running full suite (but remember: test for behavior, not coverage)

4. **Analyze Failures**
   - Read error messages and tracebacks carefully
   - Identify root cause of failures
   - Determine if failure indicates:
     - **Code bug**: Fix the code to match requirements
     - **Test bug**: Fix the test to validate correct behavior
     - **Changed requirements**: Update test to reflect new behavior
   - Check if test is testing behavior or implementation details

5. **Fix Issues**
   - **If code is wrong**: Fix the code to match requirements
   - **If test is wrong**: Fix the test to validate correct behavior
   - **If requirements changed**: Update test to reflect new behavior
   - Ensure tests follow ACT pattern (Arrange-Act-Assert-Cleanup)
   - Verify tests validate business logic, not implementation
   - Ensure all tests pass

6. **Verify Test Quality**
   - Check that tests follow Arrange-Act-Assert-Cleanup pattern
   - Verify tests validate behavior, not implementation details
   - Ensure one feature per test with single assertion
   - Confirm descriptive test names
   - Check proper use of markers, type hints, and docstrings

7. **Re-run Tests**
   - Run tests again to verify fixes
   - Verify all tests pass
   - Check coverage if running full suite (aim for 80%+ overall, 100% on critical paths)
   - Review test output for warnings
   - Ensure no flaky or non-deterministic tests

## Test Scopes

### All Tests

```bash
uv run test all          # Full test suite with coverage
uv run test quick        # Fast tests only (no coverage)
```

### Related Tests

```bash
# Find and run tests related to a source file
uv run test file tests/modules/test_moderation.py
uv run test file tests/services/
```

### By Marker

```bash
uv run pytest -m unit              # Unit tests only
uv run pytest -m integration        # Integration tests only
uv run pytest -m "not slow"        # Exclude slow tests
uv run pytest -m "unit and database"  # Unit tests with database
```

### Integration Tests

```bash
uv run pytest -m integration
```

**Integration Test Focus:**

- Verify components work together to achieve business goals
- Test database integration (fixtures, operations, transactions)
- Test service layer interactions
- Verify external service integration (with proper mocking)
- Ensure tests validate business outcomes, not just method calls

## Test Quality Checks

When fixing tests, ensure:

- ✅ Tests validate business behavior, not implementation
- ✅ Tests follow ACT pattern (cleanup via fixtures)
- ✅ One feature per test with single assertion
- ✅ Descriptive test names that read like specifications
- ✅ Proper mocking with `spec=` or `autospec=True`
- ✅ Appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
- ✅ Type hints and docstrings present

## Error Handling

If tests fail:

- **Syntax errors**: Fix syntax issues
- **Import errors**: Check imports and dependencies
- **Fixture errors**: Verify fixture setup and scope
- **Async errors**: Ensure `@pytest.mark.asyncio` is present
- **Database errors**: Check database fixtures and state
- **Mock errors**: Verify mocks are set up correctly with `spec=` or `autospec=True`

## Checklist

- [ ] Test scope determined (all, related, by marker, specific file)
- [ ] Related tests found (if applicable)
- [ ] Tests executed with appropriate command
- [ ] All test failures identified
- [ ] Root causes determined (code bug, test bug, or requirement change)
- [ ] Code or tests fixed appropriately
- [ ] Tests validate behavior, not implementation
- [ ] Tests follow ACT pattern
- [ ] All tests pass
- [ ] Coverage meets requirements (if running full suite: 80%+ overall, 100% critical paths)
- [ ] No test warnings
- [ ] Test quality verified

## See Also

- Related rule: @testing/test-quality.mdc - Test quality philosophy and ACT pattern
- Related rule: @testing/pytest.mdc - Pytest configuration
- Related rule: @testing/markers.mdc - Test marker conventions
- Related rule: @testing/coverage.mdc - Coverage requirements
- Related command: `/test-coverage` - Check test coverage
- Related command: `/write-tests` - Create new tests
- Related command: `/audit-and-fix-tests` - Audit and fix test compliance
