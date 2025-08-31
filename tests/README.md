# 🧪 Test Organization Guide

This document explains the organization of tests in the Tux project and how to run them effectively.

## 📁 Test Directory Structure

```text
tests/
├── unit/                           # 🧪 Fast, isolated unit tests
│   ├── test_database_models.py     # ✅ Model validation & relationships
│   └── test_database_postgresql_features.py  # ✅ PostgreSQL features
├── integration/                    # 🔗 Slower, real database tests
│   ├── test_database_service.py   # 🔗 Database service & async operations
│   ├── test_database_controllers.py  # 🔗 Controller interactions
│   └── test_database_migrations.py   # 🔗 Schema & migration testing
├── e2e/                          # 🌐 End-to-end tests (future)
├── fixtures/                      # 🛠️ Shared test fixtures
└── conftest.py                   # ⚙️ Pytest configuration
```

## 🎯 Test Categories

### **Unit Tests** (`tests/unit/`)

- **Purpose**: Test individual components in isolation
- **Speed**: Very fast (milliseconds to seconds)
- **Dependencies**: Mocked or use py-pglite (in-memory PostgreSQL)
- **Scope**: Individual functions, methods, or classes
- **Markers**: `@pytest.mark.unit`

**Examples**:

- Model validation and relationships
- PostgreSQL feature testing
- Individual component logic

### **Integration Tests** (`tests/integration/`)

- **Purpose**: Test component interactions and system behavior
- **Speed**: Slower (seconds to minutes)
- **Dependencies**: Real database connections, actual services
- **Scope**: Component interactions, data flow, end-to-end workflows
- **Markers**: `@pytest.mark.integration`

**Examples**:

- Database service operations
- Controller interactions
- Schema migrations
- Real database constraints

### **End-to-End Tests** (`tests/e2e/`)

- **Purpose**: Test complete system workflows
- **Speed**: Slowest (minutes)
- **Dependencies**: Full system stack
- **Scope**: Complete user journeys, system integration
- **Markers**: `@pytest.mark.e2e` (future)

## 🚀 Running Tests

### **Run All Tests**

```bash
make test                    # Full test suite with coverage
uv run pytest               # All tests without coverage
```

### **Run by Category**

```bash
# Unit tests only (fast)
uv run pytest tests/unit/           # By directory
uv run pytest -m unit               # By marker

# Integration tests only (slower)
uv run pytest tests/integration/    # By directory
uv run pytest -m integration        # By marker

# Specific test files
uv run pytest tests/unit/test_database_models.py
uv run pytest tests/integration/test_database_service.py
```

### **Run by Markers**

```bash
# Unit tests
uv run pytest -m unit

# Integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not integration"

# Run only fast tests
uv run pytest -m unit --tb=short
```

## ⚡ Performance Characteristics

### **Unit Tests** 🧪

- **Execution Time**: ~10 seconds for 28 tests
- **Database**: py-pglite (in-memory, fast)
- **Use Case**: Development, CI/CD, quick feedback

### **Integration Tests** 🔗

- **Execution Time**: ~3 seconds for 31 tests (mostly skipped)
- **Database**: Real PostgreSQL (slower setup)
- **Use Case**: Pre-deployment, regression testing

## 🔧 Test Configuration

### **Fixtures**

- **`db_session`**: Fast py-pglite session for unit tests
- **`db_service`**: Real async database service for integration tests
- **`pglite_manager`**: Module-scoped PGlite manager for performance

### **Environment Variables**

```bash
# For integration tests
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_db
```

## 📊 Test Coverage

### **Current Coverage**

- **Unit Tests**: 28 tests, ~10 seconds
- **Integration Tests**: 31 tests, ~3 seconds (mostly skipped)
- **Total**: 59 tests, ~12 seconds

### **Coverage Reports**

```bash
make test                    # Generates HTML and XML coverage reports
# Reports saved to:
# - htmlcov/ (HTML coverage)
# - coverage.xml (XML coverage)
```

## 🎯 Best Practices

### **Development Workflow**

1. **Write unit tests first** - Fast feedback during development
2. **Add integration tests** - Verify real-world behavior
3. **Use appropriate markers** - `@pytest.mark.unit` or `@pytest.mark.integration`

### **CI/CD Pipeline**

- **Unit tests**: Run on every commit (fast feedback)
- **Integration tests**: Run on pull requests (regression testing)
- **E2E tests**: Run on main branch (system validation)

### **Test Organization**

- **Keep unit tests fast** - Use mocks and in-memory databases
- **Isolate integration tests** - Real dependencies, slower execution
- **Clear separation** - Directory structure matches test behavior

## 🚨 Common Issues

### **Test Location Mismatch**

- **Problem**: Tests in wrong directories
- **Solution**: Move tests to match their actual behavior
- **Example**: `test_database_service.py` was in `unit/` but should be in `integration/`

### **Marker Inconsistency**

- **Problem**: Tests marked incorrectly
- **Solution**: Use `@pytest.mark.unit` for fast tests, `@pytest.mark.integration` for slow tests

### **Performance Issues**

- **Problem**: Slow unit tests
- **Solution**: Use py-pglite instead of real PostgreSQL for unit tests

## 🔮 Future Improvements

1. **Add E2E tests** - Complete system workflows
2. **Performance testing** - Database query optimization
3. **Load testing** - High-traffic scenarios
4. **Security testing** - Authentication and authorization
5. **API testing** - REST endpoint validation

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/testing/)
- [py-pglite Examples](https://github.com/cloudnative-pg/pg_pglite)
- [Test Organization Best Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
