---
title: Code Review Best Practices
description: Code review best practices for Tux development, including effective review techniques, common patterns, and collaboration guidelines.
tags:
  - developer-guide
  - best-practices
  - code-review
---

# Code Review Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Why Code Reviews Matter

Code reviews are essential for maintaining code quality, catching bugs early, sharing knowledge, and ensuring consistency across the Tux codebase.

### Key Benefits

- **Quality Assurance**: Catch bugs, security issues, and design problems
- **Knowledge Sharing**: Spread understanding of the codebase and best practices
- **Consistency**: Ensure all code follows established patterns and standards
- **Learning**: Help developers improve their skills through constructive feedback
- **Team Culture**: Build trust and collaboration through open, respectful discussion

## Preparing for Code Review

### For Contributors

Before submitting a PR for review, ensure your code meets basic quality standards:

#### Self-Review Checklist

- [ ] **Tests pass**: All tests run and pass (`uv run test all`)
- [ ] **Linting clean**: Code quality checks pass (`uv run dev all`)
- [ ] **Type hints**: All public functions have complete type hints
- [ ] **Documentation**: Public APIs have docstrings, complex logic is commented
- [ ] **No debug code**: Remove print statements, debug logs, and temporary code
- [ ] **Commits clean**: Logical commits with conventional commit messages
- [ ] **Branch updated**: Rebased on latest main branch
- [ ] **Changes focused**: PR addresses one specific feature or fix

#### Write a Clear PR Description

```markdown
## Summary
Brief description of what this PR does and why it's needed.

## Changes Made
- List of key changes and files modified
- Any breaking changes or migration notes
- Database schema changes (if applicable)

## Testing
- How to test the changes
- Edge cases covered
- Manual testing steps

## Screenshots/Examples
If UI changes, include before/after screenshots.
If new commands, show usage examples.
```

### PR Size Guidelines

- **Small PRs (< 200 lines)**: Ideal for quick reviews
- **Medium PRs (200-500 lines)**: Acceptable but may need multiple reviewers
- **Large PRs (> 500 lines)**: Split into smaller PRs when possible

## Conducting Effective Code Reviews

### For Reviewers

Approach reviews systematically and constructively:

#### Review Process

1. **Understand the Context**
   - Read the PR description and related issues
   - Understand the problem being solved
   - Check if changes align with project goals

2. **Automated Checks First**
   - Verify CI passes all quality gates
   - Check test coverage and performance metrics
   - Review automated linting and type checking results

3. **High-Level Review**
   - Does the solution make sense architecturally?
   - Are there security or performance concerns?
   - Does this follow established patterns?

4. **Detailed Code Review**
   - Examine logic for correctness and efficiency
   - Check error handling and edge cases
   - Verify naming, documentation, and style consistency

5. **Testing Review**
   - Are tests comprehensive and meaningful?
   - Do tests cover edge cases and error conditions?
   - Are integration tests included for complex features?

### Review Comment Guidelines

#### Be Specific and Actionable

```diff
# ❌ Vague comment
- "This function is too long"

# ✅ Specific and actionable
+ "Consider breaking this function into smaller functions:
  - `validate_input()` for input validation
  - `process_data()` for core logic
  - `format_response()` for output formatting"
```

#### Explain Reasoning

```diff
# ❌ Just says "wrong"
- "Don't use a list here"

# ✅ Explains why
+ "Use a set instead of a list for `user_ids` since:
  - We only need unique values
  - Sets have O(1) lookup vs O(n) for lists
  - Memory usage will be more efficient"
```

#### Use Positive Language

```diff
# ❌ Negative framing
- "You shouldn't do this because it's bad"

# ✅ Positive framing
+ "Consider this approach instead, as it:
  - Improves performance
  - Follows our established patterns
  - Makes the code more testable"
```

#### Suggest Solutions, Not Just Problems

```diff
# ❌ Only identifies issue
- "This error handling could be improved"

# ✅ Provides solution
+ "Consider using Tux's custom exceptions:
  ```python
  try:
      result = api_call()
  except httpx.HTTPStatusError as e:
      if e.response.status_code == 404:
          raise TuxAPIResourceNotFoundError("User not found") from e
      raise TuxAPIRequestError("API request failed") from e
  ```"
```

## Common Code Review Issues

### Architecture & Design

#### Database Query Optimization

```python
# ❌ N+1 Query Problem
async def get_users_with_posts(self, user_ids: list[int]):
    users = []
    for user_id in user_ids:
        # This executes N separate queries!
        user = await self.db.get_user(user_id)
        posts = await self.db.get_user_posts(user_id)
        users.append({"user": user, "posts": posts})
    return users

# ✅ Single Query with JOIN
async def get_users_with_posts(self, user_ids: list[int]):
    # Use a single query with JOIN
    result = await self.db.execute("""
        SELECT u.*, p.*
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        WHERE u.id = ANY(:user_ids)
    """, {"user_ids": user_ids})
    return result.fetchall()
```

#### Async/Await Misuse

```python
# ❌ Blocking async code
async def process_users(self, users: list[User]):
    for user in users:
        # This blocks the event loop!
        result = requests.get(f"/api/users/{user.id}")
        await self.save_result(result)

# ✅ Proper async code
async def process_users(self, users: list[User]):
    # Use asyncio.gather for concurrent requests
    tasks = [http_client.get(f"/api/users/{user.id}") for user in users]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for response in responses:
        if isinstance(response, Exception):
            logger.error(f"API call failed: {response}")
        else:
            await self.save_result(response)
```

### Error Handling

#### Missing Exception Types

```python
# ❌ Too broad exception handling
try:
    await self.process_data(data)
except Exception as e:
    logger.error(f"Processing failed: {e}")

# ✅ Specific exception handling
try:
    await self.process_data(data)
except TuxDatabaseConnectionError:
    logger.warning("Database temporarily unavailable")
    await self.retry_with_backoff()
except TuxValidationError as e:
    await ctx.reply(f"Invalid input: {e}")
    return
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    await ctx.reply("An unexpected error occurred")
```

#### Silent Failures

```python
# ❌ Silent failure hides bugs
try:
    result = await risky_operation()
except Exception:
    result = None  # Bug swallowed!

# ✅ Proper error handling
try:
    result = await risky_operation()
except TuxAPIConnectionError:
    logger.warning("API unavailable, using fallback")
    result = await self.get_fallback_data()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise  # Let global error handler deal with it
```

### Security Issues

#### Input Validation

```python
# ❌ SQL Injection vulnerability
async def get_user_by_name(self, name: str):
    # Direct string interpolation in SQL!
    result = await self.db.execute(f"SELECT * FROM users WHERE name = '{name}'")

# ✅ Parameterized queries
async def get_user_by_name(self, name: str):
    result = await self.db.execute(
        "SELECT * FROM users WHERE name = :name",
        {"name": name}
    )
```

#### Authentication Checks

```python
# ❌ Missing permission check
@commands.command()
async def delete_server(self, ctx: commands.Context[Tux]):
    # Anyone can run this!
    await ctx.guild.delete()

# ✅ Proper permission validation
@commands.command()
@commands.has_permissions(administrator=True)
async def delete_server(self, ctx: commands.Context[Tux]):
    # Only administrators can run this
    confirm_embed = EmbedCreator.create_embed(
        embed_type=EmbedCreator.WARNING,
        title="⚠️ Dangerous Action",
        description="This will permanently delete the server. Type 'CONFIRM' to proceed."
    )
    await ctx.send(embed=confirm_embed)

    def check(m):
        return m.author == ctx.author and m.content.upper() == "CONFIRM"

    try:
        await self.bot.wait_for('message', check=check, timeout=30.0)
        await ctx.guild.delete()
    except asyncio.TimeoutError:
        await ctx.send("Server deletion cancelled.")
```

### Performance Issues

#### Memory Leaks

```python
# ❌ Potential memory leak
class MessageCache:
    def __init__(self):
        self._cache = {}  # Grows indefinitely!

    def cache_message(self, msg_id: int, content: str):
        self._cache[msg_id] = content

# ✅ Bounded cache with cleanup
class MessageCache:
    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self._max_size = max_size

    def cache_message(self, msg_id: int, content: str):
        if len(self._cache) >= self._max_size:
            # Remove oldest entries (simple LRU)
            oldest_keys = list(self._cache.keys())[:100]
            for key in oldest_keys:
                del self._cache[key]

        self._cache[msg_id] = content
```

#### Inefficient Algorithms

```python
# ❌ O(n²) complexity
def find_duplicate_users(self, users: list[User]) -> list[tuple[User, User]]:
    duplicates = []
    for i, user1 in enumerate(users):
        for user2 in users[i+1:]:
            if user1.email == user2.email:  # O(n²) string comparisons!
                duplicates.append((user1, user2))
    return duplicates

# ✅ O(n) complexity with set
def find_duplicate_users(self, users: list[User]) -> list[tuple[User, User]]:
    seen_emails = set()
    duplicates = []

    for user in users:
        if user.email in seen_emails:
            # Find existing user with same email
            existing = next(u for u in users if u.email == user.email and u != user)
            duplicates.append((existing, user))
        else:
            seen_emails.add(user.email)

    return duplicates
```

## Best Practices by Category

### Naming & Style

- [ ] **Descriptive names**: Variables and functions clearly indicate their purpose
- [ ] **Consistent naming**: Follow snake_case for variables/functions, PascalCase for classes
- [ ] **No abbreviations**: Use full words unless universally understood (e.g., `id` is OK)
- [ ] **Boolean naming**: Use `is_`, `has_`, `can_` prefixes for boolean variables

### Code Organization

- [ ] **Single responsibility**: Each function/class has one clear purpose
- [ ] **Logical grouping**: Related functions grouped together
- [ ] **Appropriate abstractions**: Not over-engineered, but not too concrete
- [ ] **Import organization**: Standard library → third-party → local imports

### Testing Requirements

- [ ] **Unit tests**: Test individual functions/classes in isolation
- [ ] **Integration tests**: Test component interactions
- [ ] **Edge cases**: Test error conditions and boundary values
- [ ] **Mocking**: Use appropriate mocks for external dependencies

### Documentation Standards

- [ ] **Function docstrings**: NumPy format for all public functions
- [ ] **Class documentation**: Describe purpose, attributes, and usage
- [ ] **Inline comments**: Explain complex logic, not obvious code
- [ ] **Type hints**: Complete type annotations for all parameters and returns

## Review Communication

### Tone and Language

#### Constructive Feedback

**Example of good review comment:**

> "This approach works, but I noticed we have a similar pattern in `UserService.get_profile()`.
> Consider extracting a shared utility function to avoid duplication:
>
> ```python
> def format_user_display_name(user: User) -> str:
>     return f"{user.name}#{user.discriminator}"
> ```
>
> This would make the code more maintainable and consistent across the codebase."

#### Handling Disagreements

```markdown
# ✅ Professional disagreement resolution
"I see your point about using a global cache, but I'm concerned about memory usage in long-running bot instances. 

Could we consider:
1. Adding cache size limits
2. Implementing TTL-based expiration  
3. Adding cache metrics for monitoring

This would address the performance concerns while maintaining the caching benefits."
```

### Review Timing

- **Response time**: Aim to review PRs within 24 hours of assignment
- **Follow-up**: If changes are needed, check back within 1-2 days
- **Blocking issues**: Address security, correctness, or performance issues immediately
- **Nitpicks**: Save style/formatting comments for final review pass

## Automation and Tools

### Automated Checks

Tux uses comprehensive automation to catch common issues:

#### Pre-commit Hooks

```bash
# Run before committing
uv run dev pre-commit

# Includes:
# - Code formatting (ruff)
# - Import sorting
# - Type checking (basedpyright)
# - Docstring validation (pydoclint)
# - Secret scanning (gitleaks)
```

#### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml checks:
# - Tests pass on multiple Python versions
# - Code coverage meets minimum thresholds
# - Linting and type checking pass
# - Security vulnerability scans
# - Documentation builds successfully
```

### Code Review Tools

#### GitHub Features

- **Suggested changes**: Use GitHub's "Add a suggestion" feature for small fixes
- **Code review threads**: Keep related discussion in single threads
- **File filters**: Review by file type or directory
- **PR templates**: Use structured PR descriptions

#### Local Review Tools

```bash
# Review changes locally
git checkout feature-branch
uv run test all
uv run dev all

# Check specific files
uv run basedpyright src/tux/modules/feature.py
uv run ruff check src/tux/modules/feature.py
```

## Cultural Aspects

### Building Trust

- **Assume good intent**: Contributors are trying their best
- **Focus on code, not person**: Critique the code, not the developer
- **Explain reasoning**: Help reviewers learn and improve
- **Celebrate improvements**: Acknowledge when code gets better

### Continuous Learning

- **Share knowledge**: Explain why certain patterns are preferred
- **Document decisions**: Update best practices guides when patterns emerge
- **Mentor juniors**: Use reviews as teaching opportunities
- **Stay open-minded**: Be willing to learn from contributors

### Review Load Management

- **Balanced assignments**: Don't overwhelm reviewers with too many large PRs
- **Batch small reviews**: Handle multiple small PRs efficiently
- **Take breaks**: Don't review when tired or distracted
- **Delegate appropriately**: Let junior developers review simple changes

## Resources

- [Google Code Review Guidelines](https://google.github.io/eng-practices/review/) - Comprehensive review practices
- [Thoughtbot Code Review](https://github.com/thoughtbot/guides/tree/main/code-review) - Ruby-focused but broadly applicable
- [Code Review Best Practices](https://www.evoketechnology.com/blog/code-review-best-practices) - General best practices
- [Conventional Commits](https://conventionalcommits.org/) - Commit message standards
