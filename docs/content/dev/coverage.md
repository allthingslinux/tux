# Code Coverage with pytest-cov

This project uses [pytest-cov](https://pytest-cov.readthedocs.io/) to measure test coverage. Coverage helps identify which parts of your code are tested and which need more attention.

## Quick Start

### Using the Tux CLI (Recommended)

The easiest way to run coverage is through the built-in Tux CLI:

```bash
# Run tests with coverage
poetry run tux test run

# Run tests without coverage (faster)
poetry run tux test quick

# Generate coverage reports
poetry run tux test coverage --format=html
poetry run tux test coverage --format=xml
poetry run tux test coverage --fail-under=90

# Clean coverage files
poetry run tux test coverage-clean
```

### Direct pytest Commands

You can also run pytest directly:

```bash
# Basic coverage report in terminal
poetry run pytest --cov=tux

# With missing lines highlighted
poetry run pytest --cov=tux --cov-report=term-missing

# Generate HTML report
poetry run pytest --cov=tux --cov-report=html
```

### Using the Coverage Commands

Coverage functionality is integrated into the main CLI:

```bash
# Run tests with coverage report
poetry run tux test coverage

# Generate HTML report
poetry run tux test coverage --format=html

# Clean coverage files
poetry run tux test coverage-clean

# See all available options
poetry run tux test coverage --help
```

## Configuration

Coverage is configured in `pyproject.toml`:

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

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "@abstract",
]

[tool.pytest.ini_options]
addopts = [
    "--cov=tux",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-branch",
    "--cov-fail-under=80",
    "-v",
]
```

## Coverage Reports

### Terminal Report

Shows coverage statistics directly in the terminal:

```text
Name                     Stmts   Miss Branch BrPart   Cover   Missing
---------------------------------------------------------------------
tux/utils/constants.py      28      0      0      0 100.00%
tux/utils/functions.py     151    151     62      0   0.00%   1-560
---------------------------------------------------------------------
TOTAL                      179    151     62      0  15.64%
```

### HTML Report

Generates a detailed interactive HTML report in `htmlcov/`:

```bash
poetry run tux test coverage --format=html
# Generates htmlcov/index.html

# Open the report in browser
poetry run tux test coverage --format=html --open
# or open it separately
poetry run tux test coverage-open
```

The HTML report provides:

- **File-by-file coverage**: Click on any file to see line-by-line coverage
- **Missing lines**: Highlighted lines that aren't covered by tests
- **Branch coverage**: Shows which conditional branches are tested
- **Search functionality**: Find specific files or functions

### XML Report

For CI/CD integration:

```bash
poetry run tux test coverage --format=xml
# Generates coverage.xml
```

### JSON Report

Machine-readable format:

```bash
poetry run tux test coverage --format=json
# Generates coverage.json
```

## Coverage Targets

- **Current target**: 80% overall coverage
- **Goal**: Gradually increase coverage for new code
- **Focus areas**: Utility functions, core business logic, and critical paths

## Best Practices

### 1. Write Tests for New Code

Always write tests for new functionality:

```python
# tests/test_new_feature.py
def test_new_feature():
    result = new_feature("input")
    assert result == "expected_output"
```

### 2. Use Coverage to Find Gaps

Run coverage reports to identify untested code:

```bash
poetry run tux test coverage | grep "0.00%"
```

### 3. Exclude Appropriate Code

Use `# pragma: no cover` for code that shouldn't be tested:

```python
def debug_function():  # pragma: no cover
    """Only used for debugging, don't test."""
    print("Debug info")
```

### 4. Focus on Critical Paths

Prioritize testing:

- **Core business logic**
- **Error handling**
- **Edge cases**
- **Integration points**

### 5. Branch Coverage

Enable branch coverage to test all code paths:

```python
def process_data(data):
    if data:  # Both True and False paths should be tested
        return process_valid_data(data)
    else:
        return handle_empty_data()
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests with coverage
  run: |
    poetry run tux dev coverage --format=xml

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Common Commands

### Tux CLI Commands

```bash
# Basic testing
poetry run tux dev test                              # Run tests with coverage
poetry run tux dev test-quick                        # Run tests without coverage

# Coverage reports
poetry run tux dev coverage                          # Terminal report (default)
poetry run tux dev coverage --format=html            # HTML report
poetry run tux dev coverage --format=html --open     # HTML report + open browser
poetry run tux dev coverage --format=xml             # XML report for CI
poetry run tux dev coverage --format=json            # JSON report
poetry run tux dev coverage --fail-under=90          # Set coverage threshold

# Advanced options
poetry run tux dev coverage --quick                  # Quick coverage check (no detailed reports)
poetry run tux dev coverage --specific=tux/utils     # Test specific module
poetry run tux dev coverage --clean                  # Clean coverage files before running
poetry run tux dev coverage-clean                    # Clean coverage files only
poetry run tux dev coverage-open                     # Open HTML report in browser
```

## Troubleshooting

### No Coverage Data

If you see "No data was collected":

1. Ensure tests import the code being tested
2. Check that the source path is correct in `pyproject.toml`
3. Verify tests are actually running

### Low Coverage Warnings

If coverage is below the threshold:

1. Add tests for uncovered code
2. Review if the threshold is appropriate
3. Use `--cov-report=term-missing` to see missing lines

### Performance Issues

For faster test runs during development:

```bash
# Skip coverage for quick tests
poetry run pytest tests/test_specific.py

# Use the quick option
poetry run tux dev coverage --quick
```

## Resources

- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/latest/explanation/goodpractices.html)
