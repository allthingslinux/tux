# Integration Tests

## Overview

Run integration tests to verify components work together correctly.

## Steps

1. **Run Integration Tests**
   - Execute `uv run pytest -m integration`
   - Review integration test results
   - Check for database integration issues
   - Verify service layer integration

2. **Check Database Integration**
   - Verify database fixtures work
   - Test database operations
   - Check migration integration
   - Verify controller integration

3. **Verify Service Integration**
   - Test service layer interactions
   - Check Discord API integration
   - Verify external service integration
   - Test error handling integration

4. **Fix Integration Issues**
   - Fix service integration problems
   - Update integration tests if needed
   - Ensure all integration tests pass
   - Verify end-to-end workflows

## Checklist

- [ ] Integration tests executed
- [ ] Database integration verified
- [ ] Service integration verified
- [ ] External service integration checked
- [ ] All integration tests pass
- [ ] End-to-end workflows work
- [ ] No integration errors

## See Also

- Related rule: @testing/pytest.mdc
- Related rule: @testing/fixtures.mdc
- Related command: `/run-all-tests-and-fix`
- Related command: `/test-coverage`
