# Tux Database Operations Makefile
# Use this to test database operations without the CLI

.PHONY: help help-db db-connect db-current db-upgrade db-downgrade db-revision db-reset db-init test-unit test-integration test-e2e test-db test-alembic test-migrations test-models test-controllers test-service test-db-all test-coverage test-smoke test-clean

# Default target
help:
	@echo "Tux Database Operations"
	@echo "======================="
	@echo ""
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  help-db       - Show database-specific help"
	@echo ""
	@echo "Database Operations:"
	@echo "  db-connect    - Test database connection"
	@echo "  db-current    - Show current migration version"
	@echo "  db-upgrade    - Upgrade database to latest migration"
	@echo "  db-downgrade  - Downgrade database by one migration"
	@echo "  db-revision   - Create new migration revision"
	@echo "  db-reset      - Reset database (WARNING: destroys data)"
	@echo "  db-init       - Initialize database schema"
	@echo ""
	@echo "Testing:"
	@echo "  test-unit     - Run unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  test-e2e      - Run end-to-end tests"
	@echo "  test-db       - Run all database tests"
	@echo "  test-db-all   - Run comprehensive database test suite"
	@echo ""
	@echo "Environment variables:"
	@echo "  MODE=dev|prod  - Environment mode (default: dev)"
	@echo ""
	@echo "Examples:"
	@echo "  make db-connect"
	@echo "  make MODE=prod db-current"
	@echo "  make db-upgrade"

# Environment setup
MODE ?= dev
PYTHON := uv run python

# Database connection test
db-connect:
	@echo "🔍 Testing database connection..."
	@MODE=$(MODE) $(PYTHON) scripts/db_connect_test.py

# Show current migration
db-current:
	@echo "📊 Getting current migration version..."
	@MODE=$(MODE) $(PYTHON) scripts/db_current.py

# Upgrade database
db-upgrade:
	@echo "⬆️  Upgrading database to latest migration..."
	@MODE=$(MODE) $(PYTHON) scripts/db_upgrade.py

# Downgrade database
db-downgrade:
	@echo "⬇️  Downgrading database by one migration..."
	@MODE=$(MODE) $(PYTHON) scripts/db_downgrade.py

# Create new migration
db-revision:
	@echo "📝 Creating new migration revision..."
	@MODE=$(MODE) $(PYTHON) scripts/db_revision.py

# Initialize database schema
db-init:
	@echo "🏗️  Initializing database schema..."
	@MODE=$(MODE) $(PYTHON) scripts/db_init.py

# Reset database (DANGER!)
db-reset:
	@echo "⚠️  WARNING: This will reset the database and destroy all data!"
	@read -p "Are you sure? (type 'yes' to continue): " confirm && [ "$$confirm" = "yes" ] || (echo "Operation cancelled" && exit 1)
	@echo "🔄 Resetting database..."
	@MODE=$(MODE) $(PYTHON) scripts/db_reset.py

# ============================================================================
# TESTING TARGETS
# ============================================================================

# Run all database unit tests
test-unit:
	@echo "🧪 Running database unit tests..."
	$(PYTHON) -m pytest tests/unit/ -v --tb=short

# Run database integration tests
test-integration:
	@echo "🔗 Running database integration tests..."
	$(PYTHON) -m pytest --run-integration tests/integration/ -v --tb=short

# Run database end-to-end tests
test-e2e:
	@echo "🌍 Running database E2E tests..."
	$(PYTHON) -m pytest --run-e2e tests/e2e/ -v --tb=short

# Run all database tests
test-db: test-unit test-integration test-e2e
	@echo "✅ All database tests completed!"

# Run pytest-alembic tests
test-alembic:
	@echo "🗃️  Running pytest-alembic tests..."
	$(PYTHON) -m pytest --test-alembic -v --tb=short

# Run migration-specific tests
test-migrations:
	@echo "🔄 Running migration tests..."
	$(PYTHON) -m pytest tests/unit/test_database_migrations.py -v --tb=short

# Run model-specific tests
test-models:
	@echo "📊 Running model tests..."
	$(PYTHON) -m pytest tests/unit/test_database_models.py -v --tb=short

# Run controller-specific tests
test-controllers:
	@echo "🎛️  Running controller tests..."
	$(PYTHON) -m pytest tests/unit/test_database_controllers.py -v --tb=short

# Run database service tests
test-service:
	@echo "🔧 Running database service tests..."
	$(PYTHON) -m pytest tests/unit/test_database_service.py -v --tb=short

# Comprehensive database test suite
test-db-all: test-alembic test-migrations test-models test-controllers test-service test-integration test-e2e
	@echo "🎉 Complete database test suite passed!"

# Run database tests with coverage
test-coverage:
	@echo "📊 Running database tests with coverage..."
	$(PYTHON) -m pytest --cov=tux.database --cov-report=html --cov-report=term tests/unit/ tests/integration/ tests/e2e/

# Quick smoke test for database functionality
test-smoke:
	@echo "🚀 Running database smoke tests..."
	@make db-connect || (echo "❌ Database connection failed" && exit 1)
	@make db-current || (echo "❌ Database current check failed" && exit 1)
	@echo "✅ Database smoke tests passed!"

# Clean test artifacts
test-clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf tests/**/__pycache__/
	rm -rf htmlcov/
	rm -f .coverage

# ============================================================================
# DEVELOPMENT HELPERS
# ============================================================================

# Show available database targets
help-db:
	@echo "Database Management Targets:"
	@echo "  db-connect     - Test database connection"
	@echo "  db-current     - Show current migration version"
	@echo "  db-upgrade     - Upgrade database to latest migration"
	@echo "  db-downgrade   - Downgrade database by one migration"
	@echo "  db-revision    - Create new migration revision"
	@echo "  db-init        - Initialize database schema"
	@echo "  db-reset       - Reset database (DANGER!)"
	@echo ""
	@echo "Database Testing Targets:"
	@echo "  test-unit      - Run all unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  test-e2e       - Run end-to-end tests"
	@echo "  test-db        - Run unit + integration + e2e tests"
	@echo "  test-db-all    - Run comprehensive database test suite"
	@echo "  test-alembic   - Run pytest-alembic tests"
	@echo "  test-migrations - Run migration-specific tests"
	@echo "  test-models    - Run model-specific tests"
	@echo "  test-controllers - Run controller-specific tests"
	@echo "  test-service   - Run database service tests"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-smoke     - Quick smoke test (connection + current)"
	@echo "  test-clean     - Clean test artifacts"
	@echo ""
	@echo "Usage examples:"
	@echo "  make db-connect"
	@echo "  make MODE=prod db-current"
	@echo "  make test-unit"
	@echo "  make test-db"
	@echo "  make test-alembic"
	@echo "  make test-db-all"
