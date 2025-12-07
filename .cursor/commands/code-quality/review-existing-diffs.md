# Review Existing Diffs

## Overview

Perform quality pass on git diffs to ensure Tux project standards, test coverage, and documentation updates.

## Steps

1. **Scan Recent Changes**
   - Check git status and pending commits
   - Review modified files in `src/tux/`
   - Note database model or migration changes
   - Check for new commands or cogs
2. **Tux-Specific Checks**
   - Database: Run `uv run db status` if models changed
   - Tests: Verify test files updated in `tests/`
   - Docs: Check if `docs/content/` needs updates
   - Scripts: Validate CLI commands in `scripts/`
3. **Code Quality Signals**
   - Run `uv run dev all` to check standards
   - Verify type hints with basedpyright
   - Check for TODOs or debug statements
   - Ensure proper import organization
4. **Documentation Updates**
   - Update docstrings if API changed
   - Add CHANGELOG.md entry if needed
   - Update docs if user-facing changes
   - Verify conventional commit format

## Error Handling

If review finds issues:

- Fix issues before committing
- Run `uv run dev all` after fixes
- Re-run tests to verify
- Update documentation if needed

## Review Checklist

- [ ] Ran `uv run dev all` successfully
- [ ] Database migrations created if models changed
- [ ] Tests added/updated for new functionality
- [ ] Documentation updated for user-facing changes
- [ ] No debug code or TODOs left in
- [ ] Type hints pass basedpyright checks
- [ ] Imports organized correctly
- [ ] Files under 1600 lines
- [ ] Conventional commit format used
- [ ] CHANGELOG.md updated if needed

## See Also

- Related command: `/lint`
- Related command: `/refactor`
- Related command: `/write-unit-tests`
- Related rule: @AGENTS.md
