# Tux Database Operations Makefile
# Unified database management using scripts/db.py

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
	@echo "  make db-connect    # Test database connection"
	@echo "  make MODE=prod db-current  # Check current migration in prod"
	@echo "  make db-upgrade    # Upgrade database to latest"
	@echo "  make db-init       # Initialize fresh database"
	@echo "  make db-reset      # Reset database (with confirmation)"

# Environment setup
MODE ?= dev
PYTHON := uv run python

# Database operations using unified db.py script
# All commands delegate to scripts/db.py with appropriate arguments
db-connect:
	@echo "🔍 Testing database connection..."
	@MODE=$(MODE) $(PYTHON) scripts/db.py test

# Show current migration
db-current:
	@echo "📊 Getting current migration version..."
	@MODE=$(MODE) $(PYTHON) scripts/db.py current

# Upgrade database
db-upgrade:
	@echo "⬆️  Upgrading database to latest migration..."
	@MODE=$(MODE) $(PYTHON) scripts/db.py upgrade

# Downgrade database
db-downgrade:
	@echo "⬇️  Downgrading database by one migration..."
	@MODE=$(MODE) $(PYTHON) scripts/db.py downgrade

# Create new migration
db-revision:
	@echo "📝 Creating new migration revision..."
	@MODE=$(MODE) $(PYTHON) scripts/db.py revision

# Initialize database schema
db-init:
	@echo "🏗️  Initializing database schema..."
	@MODE=$(MODE) $(PYTHON) scripts/db.py init

# Reset database (DANGER!)
db-reset:
	@echo "⚠️  WARNING: This will reset the database and destroy all data!"
	@read -p "Are you sure? (type 'yes' to continue): " confirm && [ "$$confirm" = "yes" ] || (echo "Operation cancelled" && exit 1)
	@echo "🔄 Resetting database..."
	@MODE=$(MODE) $(PYTHON) scripts/db.py reset

# ============================================================================
# TESTING TARGETS
# ============================================================================

# Run all database unit tests
test-unit:
	@echo "🧪 Running database unit tests..."
	$(PYTHON) -m pytest tests/unit/ -v --tb=short

# Run database integration tests (currently empty)
test-integration:
	@echo "🔗 Database integration tests directory is empty - skipping..."

# Run database end-to-end tests (currently empty)
test-e2e:
	@echo "🌍 Database E2E tests directory is empty - skipping..."

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
	$(PYTHON) -m pytest tests/unit/test_database_migrations.py -m "not integration" -v --tb=short

# Run model-specific tests
test-models:
	@echo "📊 Running model tests..."
	$(PYTHON) -m pytest tests/unit/test_database_models.py -v --tb=short

# Run controller-specific tests (unit tests only by default)
test-controllers:
	@echo "🎛️  Running controller tests..."
	$(PYTHON) -m pytest tests/unit/test_database_controllers.py -m "not integration" -v --tb=short

# Run database service tests (unit tests only by default)
test-service:
	@echo "🔧 Running database service tests..."
	$(PYTHON) -m pytest tests/unit/test_database_service.py -m "not integration" -v --tb=short

# Integration test targets (require real database)
test-controllers-integration:
	@echo "🎛️  Running controller integration tests..."
	$(PYTHON) -m pytest tests/unit/test_database_controllers.py -m "integration" --integration -v --tb=short

test-service-integration:
	@echo "🔧 Running service integration tests..."
	$(PYTHON) -m pytest tests/unit/test_database_service.py -m "integration" --integration -v --tb=short

test-migrations-integration:
	@echo "🔄 Running migration integration tests..."
	$(PYTHON) -m pytest tests/unit/test_database_migrations.py -m "integration" --integration -v --tb=short

# Run all integration tests
test-integration-all: test-controllers-integration test-service-integration test-migrations-integration
	@echo "🎉 All integration tests passed!"

# Comprehensive database test suite (unit tests only - fast & reliable)
test-db-all: test-alembic test-migrations test-models test-controllers test-service
	@echo "🎉 Complete database test suite passed!"

# Full test suite including integration tests (requires test database)
test-db-full: test-alembic test-migrations test-models test-controllers test-service test-integration-all test-e2e
	@echo "🎉 Complete database test suite with integration tests passed!"

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
	@echo "  make db-connect          # Test database connection"
	@echo "  make MODE=prod db-current # Check current migration in prod"
	@echo "  make db-upgrade          # Upgrade database to latest"
	@echo "  make test-unit           # Run unit tests"
	@echo "  make test-db             # Run database test suite"
	@echo "  make test-alembic        # Run alembic-specific tests"
	@echo "  make test-db-all         # Run comprehensive test suite"
