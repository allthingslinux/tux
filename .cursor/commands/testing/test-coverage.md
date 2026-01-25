# Test Coverage

## Overview

Generate and review test coverage reports to identify gaps in test coverage. **Important**: Write tests to verify requirements and behavior, not just to hit coverage metrics. Coverage is a tool to find untested code, not a goal in itself.

## Steps

1. **Generate Coverage Report**
   - Run `uv run test html` for HTML report (detailed analysis)
   - Or `uv run test all` for terminal report (quick overview)
   - Review coverage percentages
   - Identify uncovered code and branches

2. **Analyze Coverage Gaps**
   - Check overall coverage percentage
   - Review coverage by module
   - Identify critical paths with low coverage
   - Note missing edge case tests
   - **Focus on behavior, not just lines**: Ask "What behavior is untested?" not just "What lines are uncovered?"

3. **Improve Coverage Meaningfully**
   - **Test business logic**: Add tests that verify requirements and behavior
   - **Test edge cases**: Cover error paths and boundary conditions
   - **Test integration points**: Verify components work together
   - **Focus on critical paths**: Ensure 100% coverage on critical business logic
   - **Avoid pointless tests**: Don't test trivial code just for coverage

4. **Review Coverage Goals**
   - **Overall**: Aim for 80%+ overall coverage
   - **Critical paths**: Ensure 100% coverage on critical code (database, services, core)
   - **New code**: 100% coverage requirement for new features
   - **Legacy code**: Improve gradually, focusing on behavior

## Coverage Analysis Best Practices

When reviewing coverage:

- ✅ **Test for behavior**: Write tests that verify what the code does, not how
- ✅ **Focus on requirements**: Test business logic and specifications
- ✅ **Cover edge cases**: Test error handling and boundary conditions
- ✅ **Critical paths first**: Ensure 100% coverage on critical business logic
- ❌ **Don't test for coverage**: Avoid writing tests just to hit metrics
- ❌ **Don't test trivial code**: Skip simple getters/setters unless they have business logic
- ❌ **Don't test implementation details**: Test behavior, not internal methods

## Checklist

- [ ] Coverage report generated
- [ ] Coverage percentages reviewed
- [ ] Uncovered code identified
- [ ] Untested behavior identified (not just uncovered lines)
- [ ] Tests added for uncovered behavior (following ACT pattern)
- [ ] Tests validate business logic, not implementation
- [ ] Coverage goals met (80%+ overall, 100% critical paths)
- [ ] Critical paths have 100% coverage
- [ ] Coverage report reviewed

## See Also

- Related rule: @testing/test-quality.mdc - Test quality philosophy (test for behavior, not coverage)
- Related rule: @testing/coverage.mdc - Coverage requirements and best practices
- Related rule: @testing/pytest.mdc - Pytest configuration
- Related command: `/run-tests` - Run tests and fix failures
- Related command: `/write-tests` - Create new tests
