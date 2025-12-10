# Run All Tests and Fix

## Overview

Run the full test suite and fix any failures according to Tux project testing standards.

## Steps

1. **Run Full Test Suite**
   - Execute `uv run test all` for full coverage
   - Review test results and failures
   - Identify failing tests and error messages
   - Check coverage report

2. **Analyze Failures**
   - Read error messages and tracebacks
   - Identify root cause of failures
   - Check if failures are due to code changes
   - Determine if tests need updates or code needs fixes

3. **Fix Issues**
   - Fix code issues causing test failures
   - Update tests if requirements changed
   - Ensure all tests pass
   - Verify coverage meets requirements

4. **Re-run Tests**
   - Run `uv run test all` again
   - Verify all tests pass
   - Check coverage improved
   - Review test output for warnings

## Checklist

- [ ] Full test suite executed
- [ ] All test failures identified
- [ ] Root causes determined
- [ ] Code or tests fixed
- [ ] All tests pass
- [ ] Coverage meets requirements
- [ ] No test warnings

## See Also

- Related rule: @testing/pytest.mdc
- Related command: `/test-coverage`
- Related command: `/integration-tests`
