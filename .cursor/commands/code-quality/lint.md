# Lint and Fix Code

## Overview

Run Tux project linters (ruff, basedpyright) and automatically fix issues according to project coding standards.

## Steps

1. **Run Linters**
   - Format code: `uv run ruff format .`
   - Fix auto-fixable issues: `uv run ruff check --fix .`
   - Check types: `uv run basedpyright`
   - Run all checks: `uv run dev all`
2. **Identify Issues**
   - Ruff linting violations (imports, style, complexity)
   - Type errors from basedpyright
   - Unused imports and variables
   - Missing type hints (`Type | None` not `Optional[Type]`)
   - NumPy docstring format violations
3. **Apply Fixes**
   - Auto-fix with ruff where possible
   - Add type hints with strict typing
   - Use `Type | None` convention
   - Fix import organization (stdlib → third-party → local)
   - Update docstrings to NumPy format
4. **Verify Standards**
   - 88 character line length
   - snake_case for functions/variables
   - PascalCase for classes
   - UPPER_CASE for constants
   - Absolute imports preferred

## Error Handling

If linting fails:

- Review error messages carefully
- Some issues may require manual fixes
- Type errors may need code changes
- Import organization can be auto-fixed

## Lint Checklist

- [ ] Ran `uv run ruff format .`
- [ ] Ran `uv run ruff check --fix .`
- [ ] Ran `uv run basedpyright`
- [ ] Fixed all type errors
- [ ] Added missing type hints
- [ ] Used `Type | None` convention
- [ ] Organized imports correctly
- [ ] Updated docstrings to NumPy format
- [ ] Verified naming conventions
- [ ] Ran `uv run dev all` successfully

## See Also

- Related command: `/refactor`
- Related command: `/review-existing-diffs`
- Related rule: @core/tech-stack.mdc
