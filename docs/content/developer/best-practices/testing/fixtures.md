---
title: Test Fixtures
tags:
  - developer-guide
  - best-practices
  - testing
---

# Test Fixtures

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Tux uses pytest fixtures to provide a clean, modular, and scalable testing infrastructure. Fixtures handle test setup, teardown, and provide reusable test data and services.

## Overview

Fixtures in Tux are organized into a dedicated package structure that automatically registers with pytest when imported. This design follows pytest's auto-discovery mechanism, where fixtures decorated with `@pytest.fixture` are automatically available to all tests.

## Fixture Organization

All fixtures are located in `tests/fixtures/` and organized by category:

```text
tests/fixtures/
├── __init__.py              # Package initialization and exports
├── database_fixtures.py      # Database and PGlite-related fixtures
├── data_fixtures.py          # Sample data fixtures and test constants
├── sentry_fixtures.py        # Sentry and Discord mock fixtures
└── utils.py                  # Validation and utility functions
```

### Package Structure

The `tests/fixtures/__init__.py` file handles fixture registration and exports non-fixture items:

```python
# Import modules to register fixtures with pytest
from . import database_fixtures
from . import data_fixtures
from . import sentry_fixtures

# Export test constants and utility functions
from .data_fixtures import (
    TEST_CHANNEL_ID,
    TEST_GUILD_ID,
    TEST_MODERATOR_ID,
    TEST_USER_ID,
    validate_guild_config_structure,
    validate_guild_structure,
    validate_relationship_integrity,
)
```

**Important**: Fixtures don't need to be in `__all__` because pytest automatically discovers them when modules are imported. Only non-fixture items (constants, utility functions) are explicitly exported.

## How Fixtures Are Discovered

Tux uses `pytest_plugins` to explicitly register fixture modules with pytest. This is the recommended approach for organizing fixtures in separate modules.

### Registration Mechanism

Fixtures are registered in `tests/conftest.py` using `pytest_plugins`:

```python
# tests/conftest.py
pytest_plugins = [
    "tests.fixtures.database_fixtures",
    "tests.fixtures.data_fixtures",
    "tests.fixtures.sentry_fixtures",
]
```

This explicitly tells pytest which modules contain fixtures, ensuring reliable discovery and registration.

**Important**: `pytest_plugins` should only be used in the **root** `conftest.py` file. Using it in non-root `conftest.py` files is deprecated by pytest.

### Why pytest_plugins?

- **Official**: The documented approach in pytest's official documentation
- **Explicit**: Clearly declares which modules contain fixtures
- **Reliable**: Works consistently across pytest versions and configurations
- **Maintainable**: Easy to see which modules are registered
- **Assertion Rewriting**: Plugins loaded via `pytest_plugins` are automatically marked for assertion rewriting

### Alternative Approaches (Not Recommended)

While you *could* use package imports (`from tests import fixtures`), this approach is less reliable because:

- Import timing can cause fixtures to be missed during pytest's discovery phase
- Relies on side-effect imports which can be fragile
- Less explicit about which modules contain fixtures

**Recommendation**: Always use `pytest_plugins` for fixture modules.

### Fixture Availability

Fixture availability is determined from the perspective of the test. A fixture is only available for tests to request if they are in the scope that fixture is defined in:

- **Global scope**: Fixtures defined in `conftest.py` or fixture modules are available to all tests in that package and subpackages
- **Module scope**: Fixtures defined in a test module are available to all tests in that module
- **Class scope**: Fixtures defined in a test class are only available to tests within that class

Tests can search **upward** through scopes (from test → module → package → root) but cannot search **downward** (from parent package to subpackage).

### conftest.py Pattern

The `conftest.py` file serves as a means of providing fixtures for an entire directory. In Tux, `tests/conftest.py` uses `pytest_plugins` to register fixture modules:

```python
# tests/conftest.py
pytest_plugins = [
    "tests.fixtures.database_fixtures",
    "tests.fixtures.data_fixtures",
    "tests.fixtures.sentry_fixtures",
]
```

This makes all fixtures from these modules available to the entire test suite. You can have multiple nested `conftest.py` files, with each directory adding its own fixtures on top of parent directories.

## Available Fixtures

### Database Fixtures

Located in `tests/fixtures/database_fixtures.py`, these fixtures provide database setup and controllers:

#### Session-Scoped Fixtures

- **`pglite_async_manager`**: Session-scoped PGlite async manager - shared across all tests in a session

#### Function-Scoped Fixtures

- **`pglite_engine`**: Function-scoped async engine with fresh schema per test
- **`db_service`**: DatabaseService with fresh database per test
- **`db_session`**: Database session for direct database operations
- **`disconnected_async_db_service`**: Database service that's not connected for testing error scenarios

#### Controller Fixtures

- **`guild_controller`**: GuildController with fresh database per test
- **`guild_config_controller`**: GuildConfigController with fresh database per test
- **`permission_rank_controller`**: PermissionRankController with fresh database per test
- **`permission_assignment_controller`**: PermissionAssignmentController with fresh database per test
- **`permission_command_controller`**: PermissionCommandController with fresh database per test
- **`permission_system`**: PermissionSystem with fresh database per test

### Test Data Fixtures

Located in `tests/fixtures/data_fixtures.py`, these fixtures provide sample data:

- **`sample_guild`**: Sample guild for testing
- **`sample_guild_with_config`**: Sample guild with config for testing

### Sentry and Discord Fixtures

Located in `tests/fixtures/sentry_fixtures.py`, these fixtures provide mocks for Sentry and Discord:

- **`mock_sentry_sdk`**: Mock sentry_sdk for testing
- **`mock_discord_user`**: Create mock Discord user
- **`mock_discord_member`**: Create mock Discord member
- **`mock_discord_guild`**: Create mock Discord guild
- **`mock_discord_channel`**: Create mock Discord channel
- **`mock_discord_interaction`**: Create mock Discord interaction
- **`mock_discord_context`**: Create mock Discord command context
- **`mock_tux_bot`**: Create mock Tux bot
- **`mock_command_error`**: Create mock command error
- **`mock_app_command_error`**: Create mock app command error
- **`sentry_capture_calls`**: Track Sentry capture calls for assertions
- **`sentry_context_calls`**: Track Sentry context calls for assertions

## Using Fixtures in Tests

### Basic Usage

Fixtures are automatically available to tests. Simply include them as function parameters:

```python
def test_guild_creation(guild_controller):
    """Test creating a guild."""
    guild = await guild_controller.create_guild(guild_id=123456789)
    assert guild.id == 123456789
```

### Fixture Dependencies

Fixtures can depend on other fixtures. Pytest automatically resolves dependencies:

```python
@pytest.fixture(scope="function")
async def sample_guild(guild_controller: GuildController):
    """Sample guild fixture depends on guild_controller fixture."""
    return await guild_controller.insert_guild_by_id(TEST_GUILD_ID)

def test_with_sample_data(sample_guild):
    """Test automatically gets both sample_guild and its dependencies."""
    assert sample_guild.id == TEST_GUILD_ID
```

### Multiple Fixtures

Tests can request multiple fixtures:

```python
def test_guild_with_config(
    guild_controller,
    guild_config_controller,
    sample_guild
):
    """Test using multiple fixtures."""
    config = await guild_config_controller.get_by_id(sample_guild.id)
    assert config is not None
```

### Fixture Scopes

Fixtures use different scopes to optimize performance:

- **`session`**: Created once per test session (e.g., `pglite_async_manager`)
- **`function`**: Created fresh for each test (e.g., `db_service`, `guild_controller`)

Function-scoped fixtures ensure test isolation - each test gets a clean database state.

## Test Constants and Utilities

Non-fixture items are exported from `tests.fixtures` for use in tests:

### Test Constants

```python
from tests.fixtures import (
    TEST_CHANNEL_ID,
    TEST_GUILD_ID,
    TEST_MODERATOR_ID,
    TEST_USER_ID,
)
```

### Validation Functions

```python
from tests.fixtures import (
    validate_guild_config_structure,
    validate_guild_structure,
    validate_relationship_integrity,
)
```

## Best Practices

### 1. Use Appropriate Fixture Scopes

- **Session scope** for expensive setup (database managers, external services)
- **Function scope** for test isolation (database services, controllers, test data)

### 2. Leverage Fixture Dependencies

Build complex test setups by composing fixtures:

```python
@pytest.fixture
async def complex_setup(db_service, guild_controller, guild_config_controller):
    """Compose multiple fixtures for complex test scenarios."""
    guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
    config = await guild_config_controller.insert_guild_config(
        guild_id=TEST_GUILD_ID,
        prefix="!"
    )
    return {"guild": guild, "config": config}
```

### 3. Use Test Constants

Always use exported test constants instead of hardcoding values:

```python
# ✅ Good
from tests.fixtures import TEST_GUILD_ID

def test_something(guild_controller):
    guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

# ❌ Bad
def test_something(guild_controller):
    guild = await guild_controller.create_guild(guild_id=123456789012345678)
```

### 4. Request Only What You Need

Only request fixtures that your test actually uses:

```python
# ✅ Good - only requests what's needed
def test_guild_creation(guild_controller):
    guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

# ❌ Bad - requests unnecessary fixtures
def test_guild_creation(guild_controller, db_service, db_session, sample_guild):
    # Only using guild_controller
    pass
```

### 5. Use Validation Functions

Use validation functions to ensure data integrity:

```python
from tests.fixtures import validate_guild_structure

def test_guild_model(guild_controller):
    guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
    assert validate_guild_structure(guild)
```

### 6. Understand Fixture Scoping

Fixture scope determines when fixtures are created and torn down:

- **`session`**: Created once per test session (e.g., `pglite_async_manager`)
- **`package`**: Created once per package/directory
- **`module`**: Created once per test module
- **`class`**: Created once per test class
- **`function`**: Created fresh for each test (default, ensures isolation)

**Always use `function` scope for test isolation** unless you have a specific reason to use a broader scope.

### 7. Be Careful with Autouse Fixtures

Autouse fixtures execute automatically for all tests in their scope, even if not requested:

```python
@pytest.fixture(autouse=True, scope="function")
def auto_setup():
    """Runs automatically for every test in this module."""
    # Setup code
    yield
    # Teardown code
```

**Use autouse sparingly** - they can make tests harder to understand and debug. Only use when setup is truly needed for all tests in a scope.

## Creating New Fixtures

When creating new fixtures, follow these guidelines:

### 1. Place in Appropriate Module

- Database-related fixtures → `database_fixtures.py`
- Sample data fixtures → `data_fixtures.py`
- Mock fixtures → `sentry_fixtures.py`

### 2. Use Proper Scoping

```python
# Session scope for expensive setup
@pytest.fixture(scope="session")
async def expensive_setup():
    # Setup code
    yield resource
    # Teardown code

# Function scope for test isolation
@pytest.fixture(scope="function")
async def isolated_resource():
    # Setup code
    yield resource
    # Teardown code
```

### 3. Document Fixtures

Always provide clear docstrings:

```python
@pytest.fixture(scope="function")
async def my_fixture(db_service: DatabaseService):
    """Brief description of what this fixture provides.

    More detailed explanation if needed.
    """
    # Fixture implementation
    yield resource
```

### 4. Export Non-Fixture Items

If you create constants or utility functions, export them in `__init__.py`:

```python
# In data_fixtures.py
MY_CONSTANT = "value"

def my_utility_function():
    pass

# In __init__.py
from .data_fixtures import MY_CONSTANT, my_utility_function

__all__ = [
    # ... existing exports
    "MY_CONSTANT",
    "my_utility_function",
]
```

## Fixture Lifecycle

Understanding fixture lifecycle helps write better tests:

1. **Session Start**: Session-scoped fixtures are created
2. **Test Collection**: Pytest collects all tests
3. **Test Execution**: For each test:
   - Function-scoped fixtures are created (in dependency order)
   - Test function runs
   - Function-scoped fixtures are torn down (in reverse order)
4. **Session End**: Session-scoped fixtures are torn down

### Fixture Instantiation Order

Pytest determines fixture execution order based on three factors:

1. **Scope**: Higher-scoped fixtures (session, package, module, class) execute before lower-scoped fixtures (function)
2. **Dependencies**: When fixture `a` requests fixture `b`, fixture `b` executes first
3. **Autouse**: Autouse fixtures execute before non-autouse fixtures within their scope

**Important**: Names, definition order, and request order have no bearing on execution order. Always rely on scope, dependencies, and autouse to control order.

#### Example: Scope-Based Order

```python
@pytest.fixture(scope="session")
def session_fixture():
    yield "session"

@pytest.fixture(scope="module")
def module_fixture():
    yield "module"

@pytest.fixture(scope="function")
def function_fixture():
    yield "function"

def test_order(session_fixture, module_fixture, function_fixture):
    # Execution order: session → module → function
    pass
```

#### Example: Dependency-Based Order

```python
@pytest.fixture
def a():
    yield "a"

@pytest.fixture
def b(a):  # b depends on a, so a executes first
    yield "b"

@pytest.fixture
def c(b):  # c depends on b, so b executes before c
    yield "c"

def test_order(c):
    # Execution order: a → b → c
    pass
```

#### Example: Autouse Fixtures

```python
@pytest.fixture(autouse=True)
def auto_fixture():
    # Executes automatically for all tests in scope
    yield

@pytest.fixture
def regular_fixture():
    # Executes after autouse fixtures
    yield
```

## Common Patterns

### Pattern: Database Test with Sample Data

```python
def test_guild_operations(guild_controller, sample_guild):
    """Test operations on a sample guild."""
    # sample_guild is already created by the fixture
    assert sample_guild.id == TEST_GUILD_ID
    
    # Perform operations
    updated = await guild_controller.update_guild(
        guild_id=sample_guild.id,
        case_count=5
    )
    assert updated.case_count == 5
```

### Pattern: Mock Discord Interaction

```python
def test_command_handler(mock_discord_interaction):
    """Test command with mocked Discord interaction."""
    # mock_discord_interaction provides a fully configured mock
    handler = MyCommandHandler()
    await handler.handle(mock_discord_interaction)
    # Assertions
```

### Pattern: Multiple Assertions with Shared Setup

```python
@pytest.fixture(scope="class")
async def shared_setup(guild_controller):
    """Shared setup for multiple tests."""
    guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
    yield guild
    # Teardown if needed

class TestGuildOperations:
    def test_operation1(self, shared_setup):
        """First test using shared setup."""
        assert shared_setup.id == TEST_GUILD_ID
    
    def test_operation2(self, shared_setup):
        """Second test using same shared setup."""
        # Uses same guild instance
        pass
```

## Troubleshooting

### Fixture Not Found

If pytest can't find a fixture:

1. **Check fixture name**: Ensure the parameter name matches the fixture function name exactly
2. **Verify import**: Ensure `conftest.py` imports the fixtures package
3. **Check scope**: Ensure fixture scope is appropriate for your use case

### Fixture Dependency Issues

If fixtures have circular dependencies:

1. **Review fixture dependencies**: Check which fixtures depend on each other
2. **Restructure if needed**: Break circular dependencies by creating intermediate fixtures
3. **Use session scope**: For shared resources that don't need to be recreated

### Test Isolation Problems

If tests are affecting each other:

1. **Check fixture scope**: Use `function` scope for test isolation
2. **Verify cleanup**: Ensure fixtures properly clean up after themselves
3. **Check for global state**: Avoid modifying global state in tests

## Built-in Pytest Fixtures

Pytest provides several useful built-in fixtures that you can use in your tests:

- **`tmp_path`**: Provides a `pathlib.Path` object to a temporary directory unique to each test
- **`tmp_path_factory`**: Creates session-scoped temporary directories
- **`monkeypatch`**: Temporarily modify classes, functions, dictionaries, `os.environ`, and other objects
- **`capsys`**: Capture output to `sys.stdout` and `sys.stderr` as text
- **`caplog`**: Control logging and access log entries
- **`pytestconfig`**: Access to configuration values, pluginmanager and plugin hooks
- **`request`**: Provide information on the executing test function

See the [pytest fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html#built-in-fixtures) for a complete list.

## Related Documentation

- [Pytest Fixtures Documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) - Official pytest fixture guide
- [Pytest Fixtures Reference](https://docs.pytest.org/en/stable/reference/fixtures.html) - Complete fixture API reference
- [Database Testing](../../concepts/database/testing.md) - Database-specific testing patterns
- [Unit Testing](./unit.md) - Unit testing best practices
- [Integration Testing](./integration.md) - Integration testing patterns
