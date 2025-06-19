# Tests Directory

This directory contains all tests for the Tux project, organized by test type and mirroring the main codebase structure.

## 🚀 **Quick Start: Testing & Coverage**

### **Local Development**

```bash
# Fast development cycle
poetry run tux test quick                    # Run tests without coverage (fastest)
poetry run tux test run                     # Run tests with coverage (recommended)

# Coverage reports  
poetry run tux test coverage --format=html  # Generate HTML coverage report
poetry run tux test coverage --open         # Generate + auto-open in browser
```

### **Coverage Strategy**

- **CI Pipeline**: Automatically handles coverage with XML reports for Codecov
- **Local CLI**: Use `tux test` commands for flexible coverage control
- **pyproject.toml**: Coverage options intentionally commented out for flexibility (see [Coverage Configuration Strategy](#5-coverage-configuration-strategy))

## 📊 Pytest Setup Review & Analysis

### ✅ **Excellent Foundations**

Your pytest setup demonstrates several strong best practices:

- **Modern Configuration**: Using `pyproject.toml` for centralized configuration
- **Proper Test Discovery**: Well-configured paths, patterns, and naming conventions
- **Async Support**: `asyncio_mode = "auto"` properly configured for Discord.py testing
- **Custom Markers**: Well-defined markers for test categorization (`slow`, `docker`, `integration`)
- **Quality Dependencies**: Modern testing stack (pytest 8.0+, pytest-asyncio 0.24+, pytest-mock 3.14+)
- **Enhanced Output**: pytest-sugar for beautiful progress bars and instant failure display  
- **Parallel Execution**: pytest-xdist for faster test runs across multiple CPU cores
- **Test Randomization**: pytest-randomly to catch test dependencies and improve reliability
- **Timeout Protection**: pytest-timeout to prevent hanging tests
- **Rich Reporting**: pytest-html for beautiful HTML test reports with self-contained output
- **Performance Testing**: pytest-benchmark for measuring code performance and regression detection
- **Comprehensive CLI**: Custom test commands via `poetry run tux test <command>` with optimized configurations
- **Docker Integration**: Smart Docker availability detection with auto-skipping

### 🎯 **Codecov Integration Alignment**

Your setup aligns **exceptionally well** with your sophisticated `.codecov.yml` configuration:

```yaml
# Component-Based Coverage Targets:
- Database Layer: 90% target (highest standards)
- Core Infrastructure: 80% target  
- Event Handlers: 80% target
- Bot Commands: 75% target
- UI Components: 70% target
- Utilities: 70% target
- CLI Interface: 65% target
- External Wrappers: 60% target (limited by external dependencies)

# Patch Coverage: 85-95% for new code (very strict standards)
```

**Coverage Configuration Status**: ✅ **EXCELLENT**

- Proper source specification (`source = ["tux"]`)
- Branch coverage enabled (`branch = true`)
- Parallel test execution support (`parallel = true`)
- Comprehensive exclusions (tests, cache, migrations, virtual envs)
- HTML reports configured (`directory = "htmlcov"`)
- Smart exclusion patterns for uncoverable code

### ⚠️ **Critical Gaps & Improvement Areas**

#### 1. **Missing Core Testing Infrastructure**

Your `conftest.py` has good Docker support but lacks Discord.py testing fixtures:

```python
# NEEDED: Discord.py testing fixtures
@pytest.fixture
async def mock_bot():
    """Create a mocked Discord bot for testing."""
    
@pytest.fixture  
async def mock_ctx():
    """Create a mocked command context."""
    
@pytest.fixture
async def mock_interaction():
    """Create a mocked slash command interaction."""

@pytest.fixture
async def mock_guild():
    """Create a mocked Discord guild."""

@pytest.fixture
async def mock_member():
    """Create a mocked Discord member."""
```

#### 2. **Database Testing Infrastructure Missing**

With your **90% database coverage target** (highest in the project), you need:

```python
# NEEDED: Database testing patterns
@pytest.fixture(scope="session")
async def test_db():
    """Set up test database connection."""
    
@pytest.fixture
async def clean_db():
    """Clean database state between tests."""

@pytest.fixture
async def sample_guild_data():
    """Create sample guild data for testing."""
```

#### 3. **Empty Test Directories**

Many test directories exist but contain only placeholder files:

- `tests/unit/tux/cogs/*/` - **Missing cog tests** (75% coverage target)
- `tests/unit/tux/database/controllers/` - **Missing controller tests** (90% target!)
- `tests/integration/tux/*/` - **Missing integration tests**
- Most handler and UI test files are empty

#### 4. **Async Testing Patterns**

Need examples for testing:

- Discord command execution and validation
- Event handlers and error processing  
- Database operations with transactions
- External API calls with proper mocking

#### 5. **Coverage Configuration Strategy**

Your `pyproject.toml` has coverage options intentionally commented out:

```toml
# addopts = [
#     "--cov=tux",
#     "--cov-report=term-missing", 
#     "--cov-report=html",
#     "--cov-branch",
#     "-v",
# ]
```

**Why commented out?** Coverage is handled at two levels:

- **CI Pipeline**: Runs coverage automatically with specific XML outputs for Codecov integration
- **CLI Commands**: Use `tux test` commands for flexible local coverage (`tux test run`, `tux test coverage`, etc.)

**Benefits of this approach**:

- ✅ **Flexibility**: Choose when to run coverage locally (faster iteration)
- ✅ **Performance**: `tux test quick` for fast development cycles
- ✅ **CI Integration**: Specialized coverage reports for different test types (unit, database, integration)
- ✅ **No Conflicts**: CI and local environments use optimal settings for their context

**Recommendation**: Keep commented out. Use CLI commands for coverage control.

### 🚧 **Priority Action Items**

#### **HIGH PRIORITY** (Align with 90% coverage targets)

1. **Database Controllers**: Your highest coverage target (90%) but missing tests
2. **Core Bot Infrastructure**: 80% target, critical for bot stability  
3. **Event Handlers**: 80% target, essential for error handling

#### **MEDIUM PRIORITY** (75-70% targets)

4. **Discord Command Cogs**: User-facing features (75% target)
5. **UI Components**: Discord interface elements (70% target)
6. **Utilities**: Helper functions (70% target)

#### **LOWER PRIORITY** (65-60% targets)

7. **CLI Interface**: Development tools (65% target)
8. **External Wrappers**: Third-party APIs (60% target)

### 💡 **Quick Wins**

1. **Keep coverage options commented** in `pyproject.toml` (current strategy is optimal)
2. **Add basic Discord.py fixtures** to `conftest.py`
3. **Implement database controller tests** (highest impact for coverage goals)
4. **Fill in smoke tests** with actual implementations

## 📁 Structure

The test structure is organized into two main categories:

```text
tests/
├── README.md                       # This file
│
├── conftest.py                     # Global pytest configuration and fixtures
│
├── integration/                    # Integration tests
│   └── tux/                       # Mirrors main package structure
│       ├── cli/                   # CLI integration tests
│       ├── handlers/              # Handler integration tests
│       ├── ui/                    # UI integration tests
│       ├── utils/                 # Utilities integration tests
│       └── wrappers/             # External API integration tests
│
└── unit/                          # Unit tests
    ├── scripts/                   # Tests for standalone scripts
    ├── test_main.py              # Tests for main entry point
    └── tux/                      # Mirrors main package structure
        ├── cli/                  # CLI unit tests
        ├── cogs/                 # Discord cogs tests
        ├── database/            # Database layer tests
        ├── handlers/            # Event handler tests
        ├── ui/                  # UI component tests
        ├── utils/               # Utility module tests
        └── wrappers/           # External API wrapper tests
```

## 🎯 Testing Principles

### 1. **Test Types Separation**

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- Each type has its own directory to maintain clear separation

### 2. **Mirror Structure**: Tests mirror the source code structure

- Makes it easy to find corresponding tests
- Helps maintain test coverage
- Example: `tux/utils/constants.py` → `tests/unit/tux/utils/test_constants.py`

### 3. **Test Categories**

- **Unit Tests**: Focus on individual functions/classes
- **Integration Tests**: Test real interactions between components
- **Benchmark Tests**: Performance testing with `pytest-benchmark`
- **Slow Tests**: Marked with `@pytest.mark.slow`
- **Docker Tests**: Marked with `@pytest.mark.docker`

### 4. **Discord.py Testing Strategy**

- Mock Discord objects for unit tests
- Use real Discord interactions for integration tests
- Test command parsing, validation, and responses separately
- Mock external API calls in unit tests

### 5. **Database Testing Approach**

- Use test database for integration tests
- Mock database calls for unit tests
- Test controllers with real database operations
- Ensure test isolation and cleanup

### 6. **Performance Testing with Benchmarks**

- Use `pytest-benchmark` for performance regression testing
- Benchmark critical performance paths
- Compare performance across code changes
- Example benchmark tests available in `tests/unit/tux/utils/test_benchmark_examples.py`
- Run with `poetry run tux test benchmark`

## 🚀 Running Tests

The project includes a comprehensive CLI for running tests with optimized configurations:

```bash
# Basic test execution
poetry run tux test run         # Standard test run with coverage
poetry run tux test quick       # Fast tests without coverage
poetry run tux test plain       # Tests without pytest-sugar formatting

# Parallel execution
poetry run tux test parallel    # Run tests using multiple CPU cores

# Specialized test types
poetry run tux test html         # Generate HTML test + coverage reports
poetry run tux test benchmark   # Run performance benchmark tests only

# Coverage reports
poetry run tux test coverage                    # Generate coverage report (terminal)
poetry run tux test coverage --format=html     # Generate HTML coverage report
poetry run tux test coverage --format=xml      # Generate XML coverage (CI/CD)
poetry run tux test coverage --format=json     # Generate JSON coverage
poetry run tux test coverage --fail-under=80   # Fail if coverage below threshold
poetry run tux test coverage --open            # Generate and open HTML report
poetry run tux test coverage --clean           # Clean old coverage files first
poetry run tux test coverage --specific=tux/utils  # Coverage for specific module
poetry run tux test coverage --quick           # Quick coverage check only

# Utility commands
poetry run tux test coverage-clean    # Clean coverage files
poetry run tux test coverage-open     # Open existing HTML coverage report
```

### Advanced Test Commands

```bash
# Component-specific coverage testing (align with codecov targets)
poetry run tux test coverage --specific=tux/database    # Database layer (90% target)
poetry run tux test coverage --specific=tux/cogs        # Bot commands (75% target)  
poetry run tux test coverage --specific=tux/handlers    # Event handlers (80% target)

# Specialized test execution
poetry run tux test parallel                            # Parallel execution
poetry run tux test benchmark                           # Performance benchmarks
poetry run tux test quick                               # Fast tests without coverage
poetry run tux test plain                               # Tests without pytest-sugar

# Coverage with thresholds and reporting
poetry run tux test coverage --fail-under=90            # Enforce coverage threshold
poetry run tux test coverage --format=xml --clean       # XML for CI/CD
poetry run tux test coverage --format=json              # JSON for tooling
poetry run tux test coverage --format=html --open       # HTML with auto-open
poetry run tux test html                                # Combined HTML reports

# Utility operations
poetry run tux test coverage-clean                      # Clean coverage files
poetry run tux test coverage-open                       # Open existing HTML report
```

## 📈 Coverage Goals & Status

Based on your `.codecov.yml` configuration:

| Component | Target | Priority | Current Status |
|-----------|--------|----------|----------------|
| Database Layer | 90% | **Critical** | ⚠️ Tests missing |
| Core Infrastructure | 80% | **High** | ⚠️ Tests missing |
| Event Handlers | 80% | **High** | ⚠️ Tests missing |
| Bot Commands | 75% | Medium | ⚠️ Tests missing |
| UI Components | 70% | Medium | ⚠️ Tests missing |
| Utilities | 70% | Medium | ✅ Good example (env.py) |
| CLI Interface | 65% | Low | ⚠️ Tests missing |
| External Wrappers | 60% | Low | ⚠️ Tests missing |

## 🔍 Example Test Implementation

### Unit Test Examples

Your `tests/unit/tux/utils/test_env.py` demonstrates **excellent** testing patterns:

- Comprehensive test classes with clear organization
- Proper setup/teardown with `pytest.fixture(autouse=True)`
- Parameterized tests for multiple scenarios
- Good mocking patterns with context managers
- Environment variable isolation
- Clear test naming and documentation

**Use this as a template** for implementing other component tests!

### Benchmark Test Examples

Your `tests/unit/tux/utils/test_benchmark_examples.py` shows **proper benchmark testing**:

- Performance testing for critical code paths
- Parameterized benchmarks for different input sizes
- Proper use of the `benchmark` fixture
- Statistical analysis with performance metrics
- Example tests include:
  - String concatenation performance
  - List comprehension benchmarks
  - Dictionary creation benchmarks
  - Sorting algorithm performance by data size
  - Recursive function optimization (fibonacci)

Run benchmarks with:

```bash
poetry run tux test benchmark
```

## 🛠️ Next Steps

### ✅ **Completed Improvements**

1. ✅ **Benchmark testing infrastructure** - `pytest-benchmark` installed and configured
2. ✅ **Example benchmark tests** - Template available in `test_benchmark_examples.py`
3. ✅ **Comprehensive CLI commands** - Full `tux test` command suite implemented
4. ✅ **Test environment isolation** - Fixed environment pollution in integration tests
5. ✅ **Enhanced reporting** - HTML reports with coverage integration

### 🔄 **In Progress / Recommended**

1. **Add Discord.py fixtures** to `conftest.py` for better testing infrastructure
2. **Start with database controller tests** (highest priority - 90% coverage target)
3. **Follow the `test_env.py` pattern** for implementing other component tests
4. **Gradually fill in cog tests** to meet the 75% coverage target
5. **Implement integration tests** for end-to-end validation
6. **Add performance benchmarks** for critical code paths using the example template

### 🎯 **Priority Order**

1. **Database Layer** (90% target) - Critical for data integrity
2. **Core Infrastructure** (80% target) - Bot stability foundations  
3. **Event Handlers** (80% target) - Error handling and resilience
4. **Bot Commands** (75% target) - User-facing functionality
5. **Performance Benchmarks** - Prevent performance regressions

Your foundation is **excellent** and getting stronger - the testing infrastructure is now production-ready!
