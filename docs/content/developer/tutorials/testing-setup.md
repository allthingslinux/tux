# Testing Setup

Learn how to set up and configure the testing environment for Tux development.

## Overview

Tux uses pytest as its testing framework with comprehensive test coverage including unit tests, integration tests, and end-to-end tests.

## Prerequisites

Before you begin:

- Python 3.11+ installed
- uv package manager
- PostgreSQL database (for integration tests)
- Discord bot token (for E2E tests)

## Setup Steps

### 1. Install Dependencies

```bash
# Install all dependencies including test dependencies
uv sync --group test
```

### 2. Configure Test Environment

Create a test configuration file:

```bash
# Copy example config
cp config/config.json.example config/test-config.json
```

Edit `config/test-config.json` with test-specific settings:

```json
{
  "bot": {
    "token": "YOUR_TEST_BOT_TOKEN",
    "prefix": "!",
    "case_insensitive": true
  },
  "database": {
    "url": "postgresql://test_user:test_pass@localhost:5432/tux_test"
  }
}
```

### 3. Set Up Test Database

```bash
# Create test database
uv run db create --config config/test-config.json

# Run migrations
uv run db migrate --config config/test-config.json
```

### 4. Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test types
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests only
uv run pytest tests/e2e/           # End-to-end tests only

# Run with coverage
uv run pytest --cov=src/tux --cov-report=html
```

## Test Structure

```
tests/
├── conftest.py           # Pytest configuration and fixtures
├── fixtures/             # Test data and fixtures
├── unit/                 # Unit tests (fast, isolated)
├── integration/          # Integration tests (database, external services)
└── e2e/                  # End-to-end tests (full Discord API)
```

## Writing Tests

### Unit Tests

Test individual functions and classes in isolation:

```python
import pytest
from tux.modules.utility.ping import PingCog

class TestPingCog:
    def test_ping_command(self):
        cog = PingCog()
        result = cog.ping()
        assert "pong" in result.lower()
```

### Integration Tests

Test components working together:

```python
import pytest
from tux.database.controllers.user import UserController

@pytest.mark.asyncio
async def test_user_creation():
    controller = UserController()
    user = await controller.create_user(12345, "test_user")
    assert user.discord_id == 12345
    assert user.username == "test_user"
```

### E2E Tests

Test complete workflows with Discord API:

```python
import pytest
from tests.e2e.base import E2ETestCase

class TestModerationCommands(E2ETestCase):
    @pytest.mark.asyncio
    async def test_ban_command(self):
        # Test actual Discord ban command
        response = await self.send_command("/ban @user reason:test")
        assert "banned" in response.content.lower()
```

## Test Configuration

### Environment Variables

```bash
# Test-specific environment variables
TEST_BOT_TOKEN=your_test_bot_token
TEST_DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/tux_test
TEST_GUILD_ID=your_test_guild_id
```

### Pytest Configuration

The `pyproject.toml` includes pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src/tux",
    "--cov-report=term-missing",
    "--cov-report=html"
]
```

## Continuous Integration

Tests run automatically on:

- **Pull Requests**: Full test suite
- **Main Branch**: Full test suite + coverage report
- **Scheduled**: Daily E2E tests

## Best Practices

1. **Write tests first**: Use TDD when possible
2. **Keep tests isolated**: Each test should be independent
3. **Use fixtures**: Reuse common test data
4. **Mock external services**: Don't hit real APIs in unit tests
5. **Test edge cases**: Include error conditions and boundary values
6. **Maintain coverage**: Aim for >80% code coverage

## Troubleshooting

### Common Issues

**Database connection errors:**

```bash
# Ensure PostgreSQL is running
sudo systemctl start postgresql

# Check database exists
psql -l | grep tux_test
```

**Discord API rate limits:**

- Use test bot tokens with higher limits
- Add delays between E2E tests
- Mock Discord API calls in unit tests

**Import errors:**

```bash
# Ensure you're in the project root
cd /path/to/tux

# Install in development mode
uv pip install -e .
```

## Next Steps

- [Writing Unit Tests](../best-practices/testing/unit.md)
- [Integration Testing](../best-practices/testing/integration.md)
- [E2E Testing](../best-practices/testing/e2e.md)
- [Test Fixtures](../best-practices/testing/fixtures.md)
