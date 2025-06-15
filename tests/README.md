# Tests Directory

This directory contains all tests for the Tux project, organized to mirror the main codebase structure.

## 📁 Structure

The test structure directly mirrors the `tux/` directory structure for easy navigation:

```text
tests/
├── __init__.py
├── conftest.py                     # pytest configuration and fixtures
├── README.md                       # This file
├── tux/                           # Tests for the main tux package
│   ├── __init__.py
│   ├── cli/                       # Tests for CLI commands (tux/cli/)
│   │   ├── __init__.py
│   │   ├── test_core.py          # Tests for tux/cli/core.py
│   │   ├── test_dev.py           # Tests for tux/cli/dev.py
│   │   ├── test_database.py      # Tests for tux/cli/database.py
│   │   ├── test_docker.py        # Tests for tux/cli/docker.py
│   │   └── test_ui.py            # Tests for tux/cli/ui.py
│   ├── cogs/                      # Tests for Discord cogs (tux/cogs/)
│   │   ├── __init__.py
│   │   ├── admin/                # Tests for admin cogs
│   │   │   ├── __init__.py
│   │   │   ├── test_dev.py
│   │   │   ├── test_eval.py
│   │   │   └── test_git.py
│   │   ├── moderation/           # Tests for moderation cogs
│   │   │   ├── __init__.py
│   │   │   ├── test_ban.py
│   │   │   ├── test_cases.py
│   │   │   └── test_jail.py
│   │   ├── utility/              # Tests for utility cogs
│   │   │   ├── __init__.py
│   │   │   ├── test_poll.py
│   │   │   ├── test_remindme.py
│   │   │   └── test_wiki.py
│   │   └── ...                   # Other cog categories
│   ├── database/                  # Tests for database layer (tux/database/)
│   │   ├── __init__.py
│   │   ├── test_client.py        # Tests for database client
│   │   └── controllers/          # Tests for database controllers
│   │       ├── __init__.py
│   │       ├── test_base.py
│   │       ├── test_case.py
│   │       └── test_levels.py
│   ├── handlers/                  # Tests for event handlers (tux/handlers/)
│   │   ├── __init__.py
│   │   ├── test_error.py
│   │   ├── test_event.py
│   │   └── test_sentry.py
│   ├── ui/                       # Tests for UI components (tux/ui/)
│   │   ├── __init__.py
│   │   ├── test_embeds.py
│   │   ├── views/
│   │   │   ├── __init__.py
│   │   │   └── test_confirmation.py
│   │   └── modals/
│   │       ├── __init__.py
│   │       └── test_report.py
│   ├── utils/                    # Tests for utility modules (tux/utils/)
│   │   ├── __init__.py
│   │   ├── test_constants.py     # ✅ Example test file
│   │   ├── test_config.py
│   │   ├── test_env.py
│   │   ├── test_functions.py
│   │   └── test_logger.py
│   └── wrappers/                 # Tests for external API wrappers (tux/wrappers/)
│       ├── __init__.py
│       ├── test_github.py
│       ├── test_tldr.py
│       └── test_xkcd.py
└── scripts/                      # Tests for scripts/ directory
    ├── __init__.py
    └── docker/
        ├── __init__.py
        └── test_docker_toolkit.py  # ✅ Tests scripts/docker_toolkit.py
```

## 🎯 Organization Principles

1. **Mirror Structure**: Each test file corresponds directly to a source file
   - `tests/tux/utils/test_constants.py` tests `tux/utils/constants.py`
   - `tests/tux/cli/test_dev.py` tests `tux/cli/dev.py`

2. **Clear Naming**: Test files use the `test_` prefix
   - Makes them easily discoverable by pytest
   - Clear indication of what's being tested

3. **Logical Grouping**: Tests are grouped by functionality
   - All cog tests under `tests/tux/cogs/`
   - All CLI tests under `tests/tux/cli/`
   - All utility tests under `tests/tux/utils/`

## 🚀 Running Tests

### Run All Tests

```bash
poetry run pytest tests/
```

### Run Specific Test Categories

```bash
# Test only utilities
poetry run pytest tests/tux/utils/

# Test only CLI commands
poetry run pytest tests/tux/cli/

# Test only cogs
poetry run pytest tests/tux/cogs/

# Test specific cog category
poetry run pytest tests/tux/cogs/moderation/
```

### Run Specific Test Files

```bash
# Test constants
poetry run pytest tests/tux/utils/test_constants.py

# Test Docker toolkit
poetry run pytest tests/scripts/docker/test_docker_toolkit.py
```

### Run with Coverage

```bash
# Using pytest-cov directly
poetry run pytest tests/ --cov=tux --cov-report=html

# Using the Tux CLI
poetry run tux dev test
poetry run tux dev coverage --format=html
```

## ✅ Test Examples

### Current Tests

- **`tests/tux/utils/test_constants.py`**: Tests the Constants class and CONST instance
- **`tests/scripts/docker/test_docker_toolkit.py`**: Tests Docker integration toolkit

### Adding New Tests

When adding a new test file:

1. **Find the corresponding source file**: `tux/path/to/module.py`
2. **Create the test file**: `tests/tux/path/to/test_module.py`
3. **Follow naming conventions**:
   - Test classes: `TestClassName`
   - Test functions: `test_function_name`
   - Use `@pytest.mark.parametrize` for multiple test cases

### Example Test Structure

```python
"""Tests for the example module."""

import pytest
from tux.path.to.module import ExampleClass


class TestExampleClass:
    """Test cases for the ExampleClass."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        instance = ExampleClass()
        assert instance.method() == expected_result

    @pytest.mark.parametrize("input_value,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_parameterized(self, input_value: str, expected: str) -> None:
        """Test with multiple parameters."""
        instance = ExampleClass()
        assert instance.process(input_value) == expected
```

## 🔧 Configuration

- **pytest configuration**: `pyproject.toml` under `[tool.pytest.ini_options]`
- **Test fixtures**: `conftest.py` for shared fixtures
- **Coverage settings**: `pyproject.toml` under `[tool.coverage.*]`

## 📈 Coverage Goals

- **Target**: 80% overall coverage
- **Reports**: HTML reports generated in `htmlcov/`
- **CI Integration**: Coverage reports integrated with test runs

This structure makes it easy to:

- Find tests for specific modules
- Maintain test organization as the codebase grows
- Run targeted test suites during development
- Onboard new contributors with clear test patterns
