# Contributing to Tux

Thank you for your interest in contributing to Tux! This guide covers everything you need to know to
contribute effectively.

## Getting Started

### Ways to Contribute

**Code Contributions:**

- Bug fixes
- New features
- Performance improvements
- Code refactoring
- Test improvements

**Documentation:**

- Fix typos and errors
- Improve existing documentation
- Add missing documentation
- Create tutorials and guides

**Community Support:**

- Help users in Discord
- Answer questions on GitHub
- Report bugs
- Test new features

**Design & UX:**

- UI/UX improvements
- Bot response design
- Documentation design
- Asset creation

### Before You Start

1. **Read the Code of Conduct** - Be respectful and inclusive
2. **Check existing issues** - Avoid duplicate work
3. **Join our Discord** - Get help and discuss ideas
4. **Set up development environment** - Follow the development setup guide

## Development Process

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/tux.git
cd tux

# Add upstream remote
git remote add upstream https://github.com/allthingslinux/tux.git
```text

### 2. Create Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Branch naming conventions:
# feature/description  - New features
# fix/description      - Bug fixes
# docs/description     - Documentation updates
# refactor/description - Code refactoring
```text

### 3. Set Up Development Environment

```bash
# Install dependencies
uv sync

# Set up pre-commit hooks
uv run dev pre-commit install

# Configure environment
cp .env.example .env
# Edit .env with your test bot token and database

# Set up database
createdb tux_dev
uv run db migrate-push
```text

### 4. Make Changes

**Code Quality Standards:**

- Follow existing code style
- Add type hints to all functions
- Write docstrings for public functions
- Add tests for new functionality
- Update documentation as needed

**Commit Message Format:**

```text
type(scope): description

Examples:
feat(moderation): add timeout command
fix(database): resolve connection pool issue
docs(api): update database documentation
refactor(core): simplify permission system
test(moderation): add ban command tests
```text

### 5. Test Your Changes

```bash
# Run all quality checks
uv run dev all

# Run tests
uv run test run

# Test manually with your bot
uv run tux start --debug
```text

### 6. Submit Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill out the PR template completely
```text

## Code Guidelines

### Python Style

**Follow PEP 8:**

- Use 4 spaces for indentation
- Line length limit of 88 characters
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants

**Type Hints:**

```python
# Always use type hints
async def create_case(
    self, 
    case_type: str, 
    user_id: int, 
    reason: str | None = None
) -> Case:
    """Create a new moderation case."""
    pass
```text

**Docstrings:**

```python
async def ban_user(self, user_id: int, reason: str) -> Case:
    """Ban a user from the server.
    
    Args:
        user_id: Discord user ID to ban
        reason: Reason for the ban
        
    Returns:
        Created case instance
        
    Raises:
        PermissionError: If bot lacks ban permissions
        ValueError: If user_id is invalid
    """
```text

**Error Handling:**

```python
# Be specific with exception handling
try:
    result = await risky_operation()
except SpecificError as e:
    logger.warning(f"Expected error: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```text

### Discord.py Best Practices

**Command Structure:**

```python
@commands.hybrid_command()
@has_permission("moderator")
async def example(self, ctx: TuxContext, user: discord.Member, *, reason: str = None):
    """Example command with proper structure."""
    try:
        # Validate input
        if user == ctx.author:
            await ctx.send("You cannot target yourself.")
            return
            
        # Perform action
        result = await self.perform_action(user, reason)
        
        # Send response
        embed = discord.Embed(
            title="Action Completed",
            description=f"Successfully performed action on {user.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        # Error handling is done by global error handler
        raise
```text

**Database Operations:**

```python
# Use the database coordinator
async def create_case_example(self, user_id: int, guild_id: int):
    case = await self.db.case.create_case(
        case_type="BAN",
        case_user_id=user_id,
        case_moderator_id=self.bot.user.id,
        guild_id=guild_id,
        case_reason="Example ban"
    )
    return case
```text

### Testing Guidelines

**Test Structure:**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_ban_command(mock_ctx, mock_db):
    """Test ban command functionality."""
    # Arrange
    cog = ModerationCog(mock_bot)
    user = MagicMock()
    user.id = 123456789
    
    # Act
    await cog.ban(mock_ctx, user, reason="Test ban")
    
    # Assert
    mock_db.case.create_case.assert_called_once()
    mock_ctx.send.assert_called_once()
```text

**Test Categories:**

- Unit tests for individual functions
- Integration tests for command workflows
- Database tests for data operations
- Mock tests for external dependencies

## Documentation Guidelines

### Writing Style

**Clear and Concise:**

- Use simple, direct language
- Avoid jargon when possible
- Explain technical terms
- Use active voice

**Structure:**

- Start with overview/purpose
- Provide step-by-step instructions
- Include code examples
- Add troubleshooting section

**Code Examples:**

```python
# Always include complete, working examples
# Add comments to explain complex parts
# Use realistic data in examples

# Good example:
async def example_function():
    """Example with clear purpose and usage."""
    user_id = 123456789  # Discord user ID
    case = await db.case.create_case(
        case_type="WARN",
        case_user_id=user_id,
        case_reason="Example warning"
    )
    return case
```text

### Documentation Types

**API Documentation:**

- Use docstrings for all public functions
- Include parameter types and descriptions
- Document return values and exceptions
- Provide usage examples

**User Documentation:**

- Focus on practical usage
- Include screenshots when helpful
- Provide troubleshooting tips
- Keep up-to-date with features

**Developer Documentation:**

- Explain architecture decisions
- Document development workflows
- Include setup instructions
- Provide debugging guides

## Issue Guidelines

### Bug Reports

**Use the bug report template:**

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment information
- Relevant logs or screenshots

**Good Bug Report:**

```text
**Bug Description:**
The ban command fails when trying to ban a user with a very long username.

**Steps to Reproduce:**
1. Use `/ban @user_with_very_long_username spam`
2. Bot responds with "An error occurred"

**Expected Behavior:**
User should be banned and case created

**Actual Behavior:**
Command fails with database error

**Environment:**
- Tux version: v1.2.3
- Python version: 3.13.0
- Database: PostgreSQL 15

**Logs:**
```text

ERROR: value too long for type character varying(50)

```text
```text

### Feature Requests

**Use the feature request template:**

- Clear description of the feature
- Use cases and benefits
- Possible implementation approach
- Alternative solutions considered

**Good Feature Request:**

```text
**Feature Description:**
Add ability to set temporary bans with automatic unbanning

**Use Case:**
Moderators want to ban users for specific time periods (1 day, 1 week, etc.) 
without manually tracking when to unban them.

**Proposed Solution:**
Add duration parameter to ban command:
`/ban @user spam --duration 7d`

**Benefits:**
- Reduces moderator workload
- Ensures consistent enforcement
- Prevents forgotten unbans
```text

## Pull Request Guidelines

### PR Requirements

**Before Submitting:**

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Feature tested manually

**PR Description:**

- Clear title describing the change
- Detailed description of what changed
- Link to related issues
- Screenshots for UI changes
- Breaking changes noted

**Good PR Example:**

```text
## Add timeout command for moderation

### Changes
- Added new `/timeout` command to moderation module
- Implemented database support for timeout cases
- Added tests for timeout functionality
- Updated documentation

### Related Issues
Closes #123

### Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manually tested in development server
- [x] Tested edge cases (invalid duration, missing permissions)

### Screenshots
[Include screenshots of command in action]

### Breaking Changes
None
```text

### Review Process

**What Reviewers Look For:**

- Code quality and style
- Test coverage
- Documentation completeness
- Performance implications
- Security considerations

**Addressing Feedback:**

- Respond to all review comments
- Make requested changes promptly
- Ask questions if feedback is unclear
- Update PR description if scope changes

## Community Guidelines

### Code of Conduct

**Be Respectful:**

- Treat everyone with respect
- Be inclusive and welcoming
- Avoid discriminatory language
- Respect different opinions

**Be Constructive:**

- Provide helpful feedback
- Focus on the code, not the person
- Suggest improvements
- Help others learn

**Be Professional:**

- Keep discussions on-topic
- Avoid personal attacks
- Use appropriate language
- Maintain confidentiality when needed

### Communication Channels

**Discord Server:**

- General discussion
- Getting help
- Feature discussions
- Community support

**GitHub Issues:**

- Bug reports
- Feature requests
- Technical discussions
- Project planning

**GitHub Discussions:**

- Long-form discussions
- Ideas and proposals
- Q&A
- Show and tell

### Recognition

**Contributors are recognized through:**

- GitHub contributor list
- Discord contributor role
- Mention in release notes
- Special thanks in documentation

**Types of Contributions Recognized:**

- Code contributions
- Documentation improvements
- Bug reports and testing
- Community support
- Design and UX work

## Getting Help

### Resources

**Documentation:**

- Developer setup guide
- API documentation
- Architecture overview
- Troubleshooting guides

**Community:**

- Discord server for real-time help
- GitHub discussions for detailed questions
- Stack Overflow for general Python/Discord.py questions

**Mentorship:**

- New contributors can request mentorship
- Experienced contributors help review PRs
- Pair programming sessions available
- Code review feedback and guidance

### Common Questions

**Q: How do I get started contributing?**
A: Start with the "good first issue" label on GitHub, set up your development environment, and join
our Discord for help.

**Q: What should I work on?**
A: Check the issues labeled "help wanted" or "good first issue". You can also propose new features
or improvements.

**Q: How long do PR reviews take?**
A: We aim to review PRs within 48-72 hours. Complex PRs may take longer.

**Q: Can I work on multiple issues at once?**
A: It's better to focus on one issue at a time, especially when starting out.

Thank you for contributing to Tux! Your contributions help make the bot better for everyone.
