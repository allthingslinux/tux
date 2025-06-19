# Testing Guide for Tux Discord Bot

Welcome to the testing documentation for the Tux Discord Bot! This guide will help you understand how to write, run, and maintain tests in this project.

## 🚀 Quick Start

### Running Tests

Use the `poetry runtux test` CLI exclusively for running tests for quick access, instead of direct pytest commands.

```bash
# Fast development cycle
poetry run tux test quick                    # Run tests without coverage (fastest)
poetry run tux test run                     # Run tests with coverage (recommended)

# Parallel execution for speed
poetry run tux test parallel                # Run tests in parallel using multiple CPU cores

# Coverage reports
poetry run tux test coverage --format=html  # Generate HTML coverage report
poetry run tux test coverage --open-browser # Generate and auto-open HTML report

# Specialized test types
poetry run tux test benchmark               # Run performance benchmarks
poetry run tux test html                    # Generate HTML test report
```

### First Time Setup

1. **Install dependencies**: Poetry handles all test dependencies automatically
2. **Verify setup**: Run `poetry run tux test quick` to ensure everything works
3. **Check Docker**: Some tests require Docker for database operations

## 📊 Testing Philosophy & Standards

### Coverage Targets by Component

We follow a **tiered coverage approach** based on component criticality:

| Component | Target | Rationale |
|-----------|--------|-----------|
| **Database Layer** | 90% | Data integrity & security critical |
| **Core Infrastructure** | 80% | Bot stability essential |
| **Event Handlers** | 80% | Error handling crucial |
| **Bot Commands (Cogs)** | 75% | User-facing features |
| **UI Components** | 70% | Discord interface elements |
| **Utilities** | 70% | Helper functions |
| **CLI Interface** | 65% | Development tools |
| **External Wrappers** | 60% | Limited by external dependencies |

### Testing Principles

- **Progressive Enhancement**: Tests should improve over time
- **Component-Based**: Different standards for different components
- **Practical Coverage**: Focus on meaningful tests, not just numbers
- **CI Integration**: Automated coverage tracking via CodeCov

## 📁 Test Organization

### Directory Structure

The test suite mirrors the main codebase structure while seperated into unit and integration tests.

```text
tests/
├── README.md                    # This guide
├── conftest.py                  # Global pytest configuration and fixtures
├── __init__.py                  # Package marker
│
├── unit/                        # Unit tests (isolated components)
│   ├── scripts/                 # Testing for project scripts
│   ├── test_main.py            # Main application tests
│   └── tux/                    # Main codebase tests
│       ├── cli/                # CLI interface tests
│       ├── cogs/               # Discord command tests
│       ├── database/           # Database layer tests
│       │   └── controllers/    # Database controller tests
│       ├── handlers/           # Event handler tests
│       ├── ui/                 # UI component tests
│       │   ├── modals/         # Modal dialog tests
│       │   └── views/          # Discord view tests
│       ├── utils/              # Utility function tests
│       └── wrappers/           # External API wrapper tests
│
└── integration/                # Integration tests (component interaction)
    └── tux/                    # End-to-end workflow tests
        ├── cli/                # CLI integration tests
        ├── handlers/           # Handler integration tests
        ├── ui/                 # UI workflow tests
        ├── utils/              # Cross-component utility tests
        └── wrappers/           # External service integration tests
```

### Test Categories

#### Unit Tests (`tests/unit/`)

- **Purpose**: Test individual components in isolation
- **Scope**: Single functions, classes, or modules
- **Dependencies**: Minimal external dependencies, heavy use of mocks
- **Speed**: Fast execution (< 1 second per test)

#### Integration Tests (`tests/integration/`)

- **Purpose**: Test component interactions and workflows
- **Scope**: Multiple components working together
- **Dependencies**: May use real database connections or external services
- **Speed**: Slower execution (may take several seconds)

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow        # Tests that take >10 seconds
@pytest.mark.docker      # Tests requiring Docker
@pytest.mark.integration # Integration tests
```

## 📝 Writing Tests

### Basic Test Structure

```python
"""Tests for tux.module_name."""

import pytest
from unittest.mock import AsyncMock, patch

from tux.module_name import function_to_test


class TestFunctionName:
    """Test the function_to_test function."""

    def test_basic_functionality(self):
        """Test basic functionality with valid input."""
        result = function_to_test("valid_input")
        assert result == "expected_output"

    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError, match="specific error message"):
            function_to_test("invalid_input")

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test asynchronous function."""
        result = await async_function_to_test()
        assert result is not None
```

### Discord.py Testing Patterns

For Discord bot components, use these patterns:

```python
import discord
import pytest
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock


class TestDiscordCommand:
    """Test Discord command functionality."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot."""
        bot = AsyncMock(spec=commands.Bot)
        bot.user = MagicMock(spec=discord.User)
        bot.user.id = 12345
        return bot

    @pytest.fixture
    def mock_ctx(self, mock_bot):
        """Create a mock command context."""
        ctx = AsyncMock(spec=commands.Context)
        ctx.bot = mock_bot
        ctx.author = MagicMock(spec=discord.Member)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.channel = MagicMock(spec=discord.TextChannel)
        return ctx

    @pytest.mark.asyncio
    async def test_command_execution(self, mock_ctx):
        """Test command executes successfully."""
        # Your command testing logic here
        await your_command(mock_ctx, "test_argument")
        
        # Assert expected behavior
        mock_ctx.send.assert_called_once()
```

### Database Testing Patterns

For database operations:

```python
import pytest
from unittest.mock import AsyncMock

from tux.database.controllers.example import ExampleController


class TestExampleController:
    """Test the ExampleController."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        return AsyncMock()

    @pytest.fixture
    def controller(self, mock_db):
        """Create controller instance with mock database."""
        return ExampleController(mock_db)

    @pytest.mark.asyncio
    async def test_create_record(self, controller, mock_db):
        """Test record creation."""
        # Mock database response
        mock_db.example.create.return_value = {"id": 1, "name": "test"}
        
        result = await controller.create_example("test")
        
        assert result["name"] == "test"
        mock_db.example.create.assert_called_once()
```

### Error Handling Tests

Always test error conditions:

```python
def test_error_handling(self):
    """Test proper error handling."""
    with pytest.raises(SpecificException) as exc_info:
        function_that_should_fail("bad_input")
    
    assert "Expected error message" in str(exc_info.value)

@pytest.mark.asyncio
async def test_async_error_handling(self):
    """Test async error handling."""
    with pytest.raises(AsyncSpecificException):
        await async_function_that_should_fail()
```

## 🔧 Test Configuration

### Pytest Configuration

The project uses `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (may take several minutes)",
    "docker: marks tests that require Docker to be running",
    "integration: marks tests as integration tests",
]
```

### Global Fixtures (`conftest.py`)

Currently provides:

- **Docker availability detection**: Automatically skips Docker-required tests
- **Custom pytest markers**: For test categorization

Planned additions:

- Discord.py testing fixtures (bot, context, interaction mocks)
- Database testing infrastructure
- Common test data factories

## 📈 CodeCov Integration

### How Coverage Works

1. **Local Development**: Use `tux test coverage` commands for flexible coverage control
2. **CI Pipeline**: Automatic coverage reporting to [CodeCov](https://codecov.io/gh/allthingslinux/tux)
3. **Pull Requests**: Coverage reports appear as PR comments
4. **Component Tracking**: Different coverage targets for different components

### Coverage Configuration

Coverage settings are defined in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["tux"]
branch = true
parallel = true
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*",
    "*/venv/*",
    "*/.venv/*",
]
```

### Viewing Coverage Reports

```bash
# Terminal report
poetry run tux test coverage --format=term

# HTML report (detailed)
poetry run tux test coverage --format=html

# Open HTML report in browser
poetry run tux test coverage --format=html --open-browser

# XML report (for CI)
poetry run tux test coverage --format=xml
```

### CodeCov Dashboard

Visit [codecov.io/gh/allthingslinux/tux](https://codecov.io/gh/allthingslinux/tux) to:

- View overall project coverage
- See component-specific coverage
- Track coverage trends over time
- Review coverage on pull requests

## 🔄 Development Workflow

### Test-Driven Development

1. **Write failing test**: Start with a test that describes desired behavior
2. **Implement feature**: Write minimal code to make test pass
3. **Refactor**: Improve code while keeping tests green
4. **Repeat**: Continue with next feature

### Before Committing

1. **Run tests**: `poetry run tux test run` to ensure all tests pass with coverage
2. **Check style**: Pre-commit hooks will check code formatting
3. **Review coverage**: Ensure new code has appropriate test coverage

### Adding New Tests

1. **Create test file**: Follow naming convention `test_*.py`
2. **Mirror structure**: Place tests in directory matching source code
3. **Use appropriate markers**: Mark slow or Docker-dependent tests
4. **Follow patterns**: Use established testing patterns for consistency

## 🐛 Debugging Tests

### Common Issues

1. **Docker tests failing**: Ensure Docker is running (`docker version`)
2. **Async tests hanging**: Check for proper `pytest.mark.asyncio` usage
3. **Import errors**: Verify test paths and module structure
4. **Flaky tests**: Use `pytest-randomly` to catch test dependencies

### Debug Commands

```bash
# Run with verbose output
poetry run tux test run -v

# Run specific test file
poetry run tux test run tests/unit/tux/utils/test_env.py

# Run tests with debugger
poetry run tux test run --pdb

# Run only failed tests from last run
poetry run tux test run --lf
```

## 🚀 Performance Testing

### Benchmark Tests

Use `pytest-benchmark` for performance tests:

```python
def test_performance_critical_function(benchmark):
    """Test performance of critical function."""
    result = benchmark(performance_critical_function, "test_input")
    assert result == "expected_output"
```

Run benchmarks:

```bash
poetry run tux test benchmark
```

## 🎯 Best Practices

### Test Writing

- **Clear names**: Test names should describe what they test
- **Single responsibility**: One test should test one thing
- **Arrange-Act-Assert**: Structure tests clearly
- **Independent tests**: Tests should not depend on each other

### Test Organization

- **Group related tests**: Use test classes to group related functionality
- **Use descriptive docstrings**: Explain what each test verifies
- **Parametrize similar tests**: Use `@pytest.mark.parametrize` for similar tests with different inputs

### Mocking

- **Mock external dependencies**: Database calls, API requests, file operations
- **Verify interactions**: Assert that mocked functions were called correctly
- **Use appropriate mock types**: `Mock`, `AsyncMock`, `MagicMock` as needed

### Coverage

- **Focus on meaningful coverage**: Don't just chase percentages
- **Test edge cases**: Error conditions, boundary values, invalid inputs
- **Exclude uncoverable code**: Use `# pragma: no cover` for defensive code

## 📚 Additional Resources

- **Pytest Documentation**: [docs.pytest.org](https://docs.pytest.org/)
- **Discord.py Testing**: [discordpy.readthedocs.io](https://discordpy.readthedocs.io/)
- **CodeCov Documentation**: [docs.codecov.com](https://docs.codecov.com/)
- **Project CodeCov Dashboard**: [codecov.io/gh/allthingslinux/tux](https://codecov.io/gh/allthingslinux/tux)

## 🤝 Contributing

When contributing tests:

1. **Follow existing patterns**: Maintain consistency with current test structure
2. **Add appropriate coverage**: Ensure new features have corresponding tests
3. **Update documentation**: Update this README if adding new testing patterns
4. **Review coverage impact**: Check how your changes affect component coverage targets

Happy testing! 🧪✨
