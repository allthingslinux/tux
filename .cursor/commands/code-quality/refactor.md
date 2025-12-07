# Refactor Code

## Overview

Refactor code to follow Tux project patterns, Discord.py best practices, and Python standards while maintaining functionality.

## Steps

1. **Code Quality Improvements**
   - Extract reusable functions following DRY principle
   - Eliminate code duplication across cogs
   - Improve naming (snake_case, PascalCase, UPPER_CASE)
   - Simplify nested async/await patterns
2. **Discord.py Patterns**
   - Use hybrid commands (slash + traditional)
   - Implement proper command error handlers
   - Use embeds from `tux.ui.embeds`
   - Follow cog structure from `src/modules/`
3. **Database Patterns**
   - Use service layer for business logic
   - Use controllers for database operations
   - Never access database session directly
   - Implement proper transaction handling
4. **Python Best Practices**
   - Add strict type hints
   - Use NumPy docstring format
   - Follow async/await patterns
   - Keep files under 1600 lines

## Error Handling

During refactoring:

- Run tests frequently to catch regressions
- Use `uv run test quick` for fast feedback
- Check for breaking changes
- Verify all functionality still works

## Refactor Checklist

- [ ] Extracted reusable functions
- [ ] Eliminated code duplication
- [ ] Improved naming conventions
- [ ] Simplified complex nested logic
- [ ] Used proper Discord.py command patterns
- [ ] Implemented service layer architecture
- [ ] Added strict type hints
- [ ] Updated to NumPy docstrings
- [ ] Verified async/await patterns
- [ ] Kept files under 1600 lines
- [ ] Ran tests to verify functionality

## See Also

- Related command: `/lint`
- Related command: `/write-unit-tests`
- Related rule: @modules/cogs.mdc
- Related rule: @database/controllers.mdc
