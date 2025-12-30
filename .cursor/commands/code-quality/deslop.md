# Deslop

## Overview

Produce high-quality Python code following strict Tux project standards, avoiding AI-generated pitfalls. This command guides you through writing consistent, maintainable code free of "slop" - unnecessary complexity, inconsistencies, and anti-patterns.

## Steps

1. **Research-First Protocol (MANDATORY)**
   - Read relevant docs - Search workspace (notes/, docs/, README). Use as context; verify against actual code.
   - Read API documentation - Official docs, in-code comments. Use as context; verify against actual code.
   - Map system end-to-end:
     - Data Flow & Architecture: Request lifecycle, dependencies, integration points, affected components
     - Data Structures & Schemas: Database schemas, API structures, validation rules
     - Configuration & Dependencies: Environment variables, service dependencies, deployment configs
     - Existing Implementation: Search for similar features - leverage or expand existing code instead of creating new
   - Inspect existing code - Study implementations before building. If leveraging existing code, trace all dependencies first.
   - Verify understanding - Explain system flow, data structures, dependencies, impact. Use structured thinking for complex problems.
   - Check for blockers - Ambiguous requirements? Security/risk concerns? Multiple valid architectural choices? Missing critical info?

2. **Write Consistent Code**
   - Match existing style - Use the same naming conventions, import style, and structure as the file.
   - Follow established patterns - If controllers are used for DB access, use controllers. If services handle business logic, use services.
   - Reuse existing code - Don't duplicate - check if utilities, helpers, or similar functions exist.
   - Stay in scope - ONLY modify what's requested. Do NOT change unrelated code.
   - Preserve patterns - If you see a pattern (e.g., `Type | None`, specific exception types), maintain it exactly.
   - Use existing constants - Check for existing constants/config before using magic numbers/strings.

3. **Follow Python Standards**
   - Type hints: ALWAYS use strict typing with `Type | None` syntax, NEVER `Optional[Type]`
   - Docstrings: ALWAYS use NumPy format for all public APIs with Parameters, Returns, Raises, Examples sections
   - Imports: Group as stdlib → third-party → local. Use absolute imports when possible
   - Line length: Maximum 88 characters (ruff default)
   - Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_CASE` for constants
   - File size: NEVER exceed 1600 lines per file - split if needed

4. **Database Layer Standards**
   - Controllers: ALWAYS use controllers for business logic. NEVER bypass controllers for CRUD operations
   - Single service: Use `DatabaseService` singleton pattern. NEVER create parallel DB clients
   - Transactions: Use controller methods (`with_transaction`, `with_session`). NEVER use raw sessions for CRUD
   - Models: ALWAYS inherit from `BaseModel`. Use mixins (`UUIDMixin`, `SoftDeleteMixin`) when appropriate
   - Relationships: ALWAYS configure proper `back_populates`, appropriate `lazy` strategy, correct `cascade`
   - Migrations: ALWAYS use Alembic (`uv run db dev`). NEVER make manual schema changes

5. **Service Layer Standards**
   - Dependency injection: Services MUST receive dependencies via constructor, NEVER use globals
   - Stateless: Services MUST be stateless where possible
   - Async/await: ALL I/O operations MUST be async
   - Error handling: Use custom exceptions from `TuxError` hierarchy, NEVER generic `Exception`
   - Logging: Use `loguru` with appropriate context, NEVER `print()`
   - Sentry: Integrate error tracking with `sentry-sdk` for production errors

6. **Discord Bot Patterns**
   - Commands: Use hybrid commands (slash + traditional) when appropriate
   - Cogs: Follow modular organization with proper `cog_load`/`cog_unload` lifecycle
   - Permissions: ALWAYS check permissions before actions using the permission system
   - Embeds: Use `discord.Embed` for user-facing messages with consistent formatting
   - Rate limits: Handle Discord rate limits gracefully with retries/backoff
   - Error messages: Use user-friendly messages via global error handler

7. **Review Before Submitting**
   - Verify APIs - Check that all methods/functions you used actually exist in the libraries
   - Check consistency - Ensure your code matches the style and patterns of the file
   - Review scope - Verify you only changed what was requested - no extra "improvements"
   - Check for slop - Review your code against anti-patterns (see Error Handling section)
   - Remove debug code - Ensure no `print()`, temporary variables, or test code remains
   - Verify patterns - Ensure you didn't break established patterns or conventions
   - Verify against usage - Read the calling code to see what it expects. Ensure consumers get all fields/data they need.
   - Adversarial verification - Actively try to falsify assumptions. Look for regressions, silent failures, edge cases.

8. **Mandatory Self-Audit**
   - Run all relevant tests and show results
   - Verify against actual usage (read calling code)
   - Check for regressions or unintended side effects
   - Verify all changes match requested scope
   - Provide evidence (test output, code references, verification steps)
   - Use status markers: ✅ (completed), ⚠️ (recoverable issue fixed), 🚧 (blocked after exhausting research)

## Error Handling

### Common Anti-Patterns to Avoid

**Python Anti-Patterns:**

- Bare `except:` - ALWAYS use `except Exception:` or specific exception types
- `Optional[Type]` - Use `Type | None` (Python 3.13+ syntax)
- Mutable default arguments - NEVER use mutable defaults (`[]`, `{}`, `set()`). Use `None` and check inside
- Direct session access - NEVER use `async with db.session() as session:` for CRUD - use controllers
- Synchronous I/O - NEVER use blocking I/O in async functions (`requests`, `open()` without `aiofiles`)
- Comparing to None - Use `is None` or `is not None`, NEVER `== None`
- Generic exceptions - Use specific `TuxError` subclasses, NEVER `Exception`
- Missing type hints - ALL function signatures MUST have type hints
- `# type: ignore` - Fix type errors properly, NEVER suppress them
- `print()` statements - Use `loguru` logger, NEVER `print()`

**AI Code Slop Detection:**

- Extra comments inconsistent with file style
- Over-defensive programming: unnecessary `| None` unions, excessive null checks
- Type system abuse: Using `cast(Any, ...)` or `# type: ignore` to get around type issues
- Code organization issues: Over-engineering, duplicating existing functionality, breaking existing patterns
- Consistency violations: Inconsistent naming, not following file structure, magic numbers/strings
- Debug artifacts: `print()` statements, unused imports, test code in production
- Pattern violations: Not following existing patterns, breaking conventions, adding features not requested
- Generic & vague code: Empty AI-words ("robust", "seamless", "efficient"), generic variable names

If you encounter any of these patterns:

- Remove them immediately
- Replace with proper patterns from the codebase
- Verify the fix doesn't break existing functionality

## Checklist

- [ ] Read and understood the entire file being edited
- [ ] Checked similar files to understand existing patterns
- [ ] Searched for existing implementations - found similar functionality and leveraged/expanded it
- [ ] Traced dependencies - verified changes won't break other things
- [ ] Matched existing naming conventions exactly
- [ ] Followed existing import style and organization
- [ ] Used existing constants/config instead of magic values
- [ ] ALL tests pass (`uv run test all`)
- [ ] Quality checks pass (`uv run dev all`)
- [ ] Type checking passes (`uv run basedpyright`)
- [ ] No unused imports (`ruff check --select F401`)
- [ ] No commented-out code
- [ ] All public APIs have docstrings (NumPy format)
- [ ] All functions have type hints
- [ ] No `# type: ignore` or `cast(Any, ...)` comments
- [ ] No `print()` statements (use `loguru`)
- [ ] Database operations use controllers via `DatabaseCoordinator`
- [ ] Error handling uses custom exceptions (`TuxError` hierarchy)
- [ ] Only requested changes were made (no scope creep)
- [ ] No unrelated code was modified
- [ ] Established patterns were preserved exactly
- [ ] All API calls verified to exist in actual libraries
- [ ] Verified against usage - read calling code, checked what fields/properties are accessed
- [ ] Adversarial verification - tested edge cases, null/undefined, empty payloads

## See Also

- Related command: `/lint`
- Related command: `/refactor`
- Related command: `/review-existing-diffs`
- Related rule: @core/tech-stack.mdc
- Related rule: @database/controllers.mdc
- Related rule: @database/models.mdc
- Related rule: @modules/commands.mdc
