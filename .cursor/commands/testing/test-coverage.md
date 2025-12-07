# Test Coverage

## Overview

Generate and review test coverage reports to ensure adequate test coverage.

## Steps

1. **Generate Coverage Report**
   - Run `uv run test html` for HTML report
   - Or `uv run test all` for terminal report
   - Review coverage percentages
   - Identify uncovered code

2. **Analyze Coverage**
   - Check overall coverage percentage
   - Review coverage by module
   - Identify critical paths with low coverage
   - Note missing edge case tests

3. **Improve Coverage**
   - Add tests for uncovered code
   - Test edge cases and error paths
   - Add integration tests where needed
   - Focus on critical business logic

4. **Review Coverage Goals**
   - Aim for 80%+ overall coverage
   - Ensure 100% coverage on critical paths
   - Maintain high coverage on new code
   - Gradually improve legacy code coverage

## Checklist

- [ ] Coverage report generated
- [ ] Coverage percentages reviewed
- [ ] Uncovered code identified
- [ ] Tests added for uncovered code
- [ ] Coverage goals met (80%+ overall)
- [ ] Critical paths have 100% coverage
- [ ] Coverage report reviewed

## See Also

- Related rule: @testing/coverage.mdc
- Related command: `/run-all-tests-and-fix`
- Related command: `/integration-tests`
