# Tux Development Makefile
# Comprehensive development and management commands for the Tux Discord bot

.PHONY: help help-db help-dev help-docker help-docs help-test

# Default target
help:
	@echo "Tux Development Commands"
	@echo "========================"
	@echo ""
	@echo "Available command groups:"
	@echo "  make help-db      - Database management commands"
	@echo "  make help-dev     - Development tools commands"
	@echo "  make help-docker  - Docker management commands"
	@echo "  make help-docs    - Documentation commands"
	@echo "  make help-test    - Testing commands"
	@echo ""
	@echo "Quick start:"
	@echo "  make start        - Start the Discord bot"
	@echo "  make dev          - Start in development mode"
	@echo "  make test         - Run test suite"
	@echo "  make lint         - Check code quality"
	@echo "  make format       - Format code"
	@echo ""
	@echo "Environment variables:"
	@echo "  MODE=dev|prod    - Environment mode (default: dev)"
	@echo "  PYTHON=uv        - Python package manager (default: uv)"

# Environment setup
MODE ?= dev
PYTHON := uv run python

# ============================================================================
# MAIN COMMANDS
# ============================================================================

# Start the Discord bot
start:
	@echo "🚀 Starting Tux Discord bot..."
	@MODE=$(MODE) $(PYTHON) scripts/tux-start.py

# Start in development mode
dev:
	@echo "🔧 Starting Tux in development mode..."
	@MODE=dev $(PYTHON) scripts/tux-start.py

# Show version
version:
	@echo "📋 Showing Tux version..."
	@$(PYTHON) scripts/tux-version.py

# ============================================================================
# DATABASE COMMANDS
# ============================================================================

help-db:
	@echo "Database Management Commands:"
	@echo "  db-upgrade        - Upgrade database to latest migration"
	@echo "  db-downgrade      - Downgrade database by one migration"
	@echo "  db-revision       - Create new migration revision"
	@echo "  db-current        - Show current migration version"
	@echo "  db-history        - Show migration history"
	@echo "  db-reset          - Reset database to base (WARNING: destroys data)"
	@echo "  db-reset-migrations - Reset all migrations and create clean baseline"
	@echo ""
	@echo "Advanced Database Tools:"
	@echo "  db-health         - Comprehensive database health check"
	@echo "  db-performance    - Analyze database performance metrics"
	@echo "  db-stats          - Show table statistics and metrics"
	@echo "  db-demo           - Demonstrate advanced PostgreSQL features"
	@echo ""
	@echo "Usage examples:"
	@echo "  make MODE=prod db-upgrade  # Upgrade production database"
	@echo "  make db-revision            # Create new migration"
	@echo "  make db-reset              # Reset database (with confirmation)"
	@echo "  make db-health             # Check database health"
	@echo "  make db-performance        # Analyze performance metrics"

# Database operations
db-upgrade:
	@echo "⬆️  Upgrading database to latest migration..."
	@MODE=$(MODE) $(PYTHON) scripts/db-migrate.py upgrade

db-downgrade:
	@echo "⬇️  Downgrading database by one migration..."
	@MODE=$(MODE) $(PYTHON) scripts/db-migrate.py downgrade

db-revision:
	@echo "📝 Creating new migration revision..."
	@MODE=$(MODE) $(PYTHON) scripts/db-migrate.py revision

db-current:
	@echo "📊 Getting current migration version..."
	@MODE=$(MODE) $(PYTHON) scripts/db-migrate.py current

db-history:
	@echo "📚 Showing migration history..."
	@MODE=$(MODE) $(PYTHON) scripts/db-migrate.py history

db-reset:
	@echo "⚠️  WARNING: This will reset the database and destroy all data!"
	@read -p "Are you sure? (type 'yes' to continue): " confirm && [ "$$confirm" = "yes" ] || (echo "Operation cancelled" && exit 1)
	@echo "🔄 Resetting database..."
	@MODE=$(MODE) $(PYTHON) scripts/db-migrate.py reset

db-reset-migrations:
	@echo "⚠️  WARNING: This will reset all migrations and create a clean baseline!"
	@echo "This will:"
	@echo "  1. Drop all database data"
	@echo "  2. Delete all migration files"
	@echo "  3. Create a fresh baseline migration"
	@echo "  4. Apply the new migration"
	@read -p "Are you sure? (type 'yes' to continue): " confirm && [ "$$confirm" = "yes" ] || (echo "Operation cancelled" && exit 1)
	@echo "🔄 Resetting migrations..."
	@MODE=$(MODE) $(PYTHON) scripts/db-migrate.py reset-migrations

# Advanced database tools
db-health:
	@echo "🏥 Running comprehensive database health check..."
	@MODE=$(MODE) $(PYTHON) scripts/db-health.py

db-performance:
	@echo "📊 Analyzing database performance metrics..."
	@MODE=$(MODE) $(PYTHON) scripts/db-metrics.py

db-stats:
	@echo "📋 Showing table statistics and metrics..."
	@MODE=$(MODE) $(PYTHON) scripts/db-metrics.py

db-demo:
	@echo "🎮 Demonstrating advanced PostgreSQL features..."
	@MODE=$(MODE) $(PYTHON) scripts/db-metrics.py

# ============================================================================
# DEVELOPMENT COMMANDS
# ============================================================================

help-dev:
	@echo "Development Tools Commands:"
	@echo "  lint              - Run linting with Ruff"
	@echo "  lint-fix          - Run linting with Ruff and apply fixes"
	@echo "  format            - Format code with Ruff"
	@echo "  type-check       - Check types with basedpyright"
	@echo "  pre-commit       - Run pre-commit checks"
	@echo ""
	@echo "Usage examples:"
	@echo "  make lint         # Check code quality"
	@echo "  make lint-fix     # Fix code quality issues"
	@echo "  make format       # Format code"
	@echo "  make type-check   # Check type annotations"

# Development tools
lint:
	@echo "🔍 Running linting with Ruff..."
	@$(PYTHON) scripts/dev-tools.py lint

lint-fix:
	@echo "🔧 Running linting with Ruff and applying fixes..."
	@$(PYTHON) scripts/dev-tools.py lint-fix

format:
	@echo "✨ Formatting code with Ruff..."
	@$(PYTHON) scripts/dev-tools.py format

type-check:
	@echo "🔍 Checking types with basedpyright..."
	@$(PYTHON) scripts/dev-tools.py type-check

pre-commit:
	@echo "✅ Running pre-commit checks..."
	@$(PYTHON) scripts/dev-tools.py pre-commit

# ============================================================================
# DOCKER COMMANDS
# ============================================================================

help-docker:
	@echo "Docker Management Commands:"
	@echo "  docker-build     - Build Docker images"
	@echo "  docker-up        - Start Docker services"
	@echo "  docker-down      - Stop Docker services"
	@echo "  docker-logs      - Show Docker service logs"
	@echo "  docker-ps        - List running Docker containers"
	@echo "  docker-exec      - Execute command in container"
	@echo "  docker-shell     - Open shell in container"
	@echo "  docker-restart   - Restart Docker services"
	@echo "  docker-health    - Check container health status"
	@echo "  docker-test      - Run Docker tests"
	@echo "  docker-cleanup   - Clean up Docker resources"
	@echo "  docker-config    - Validate Docker Compose config"
	@echo "  docker-pull      - Pull latest Docker images"
	@echo ""
	@echo "Advanced Docker Tools:"
	@echo "  docker-toolkit-test      - Run comprehensive Docker test suite"
	@echo "  docker-toolkit-quick     - Run quick Docker validation tests"
	@echo "  docker-toolkit-perf      - Run Docker performance tests"
	@echo "  docker-toolkit-security  - Run Docker security tests (not implemented)"
	@echo "  docker-toolkit-comprehensive - Run full Docker test suite"
	@echo ""
	@echo "Options:"
	@echo "  NO_CACHE=1       - Build without cache"
	@echo "  TARGET=dev       - Build specific stage"
	@echo "  DETACH=1         - Run containers in background"
	@echo "  BUILD=1          - Build images before starting"
	@echo "  WATCH=1          - Enable file watching (dev mode)"
	@echo "  VOLUMES=1        - Remove volumes on down"
	@echo "  REMOVE_ORPHANS=1 - Remove orphaned containers"
	@echo "  FOLLOW=1         - Follow log output"
	@echo "  TAIL=100         - Show last N log lines"
	@echo "  SERVICE=tux      - Target specific service"
	@echo "  FORCE=1          - Force operations without confirmation"
	@echo "  DRY_RUN=1        - Show what would be done without doing it"
	@echo ""
	@echo "Usage examples:"
	@echo "  make docker-build NO_CACHE=1        # Build without cache"
	@echo "  make docker-up BUILD=1 WATCH=1      # Build and start with watching"
	@echo "  make docker-logs FOLLOW=1 TAIL=50   # Follow logs with tail"
	@echo "  make docker-cleanup FORCE=1         # Force cleanup without confirmation"
	@echo "  make docker-toolkit-test            # Run comprehensive Docker tests"

# Docker operations
docker-build:
	@echo "🐳 Building Docker images..."
	@$(PYTHON) scripts/docker-compose.py build \
		$(if $(NO_CACHE),--no-cache) \
		$(if $(TARGET),--target $(TARGET))

docker-up:
	@echo "🚀 Starting Docker services..."
	@$(PYTHON) scripts/docker-compose.py up \
		$(if $(DETACH),-d) \
		$(if $(BUILD),--build) \
		$(if $(WATCH),--watch)

docker-down:
	@echo "🛑 Stopping Docker services..."
	@$(PYTHON) scripts/docker-compose.py down \
		$(if $(VOLUMES),-v) \
		$(if $(REMOVE_ORPHANS),--remove-orphans)

docker-logs:
	@echo "📋 Showing Docker service logs..."
	@$(PYTHON) scripts/docker-compose.py logs \
		$(if $(FOLLOW),-f) \
		$(if $(TAIL),-n $(TAIL)) \
		$(if $(SERVICE),$(SERVICE))

docker-ps:
	@echo "📊 Listing running Docker containers..."
	@$(PYTHON) scripts/docker-compose.py ps

docker-exec:
	@echo "🔧 Executing command in container..."
	@$(PYTHON) scripts/docker-compose.py exec \
		$(if $(INTERACTIVE),-it) \
		$(SERVICE) $(COMMAND)

docker-shell:
	@echo "🐚 Opening shell in container..."
	@$(PYTHON) scripts/docker-compose.py shell $(SERVICE)

docker-restart:
	@echo "🔄 Restarting Docker services..."
	@$(PYTHON) scripts/docker-compose.py restart $(SERVICE)

docker-health:
	@echo "🏥 Checking container health status..."
	@$(PYTHON) scripts/docker-compose.py health

docker-test:
	@echo "🧪 Running Docker tests..."
	@$(PYTHON) scripts/docker-compose.py test \
		$(if $(NO_CACHE),--no-cache) \
		$(if $(FORCE_CLEAN),--force-clean) \
		$(if $(QUICK),--quick) \
		$(if $(COMPREHENSIVE),--comprehensive)

docker-cleanup:
	@echo "🧹 Cleaning up Docker resources..."
	@$(PYTHON) scripts/docker-compose.py cleanup \
		$(if $(VOLUMES),--volumes) \
		$(if $(FORCE),--force) \
		$(if $(DRY_RUN),--dry-run)

docker-config:
	@echo "⚙️  Validating Docker Compose configuration..."
	@$(PYTHON) scripts/docker-compose.py config

docker-pull:
	@echo "⬇️  Pulling latest Docker images..."
	@$(PYTHON) scripts/docker-compose.py pull

# Advanced Docker toolkit commands
docker-toolkit-test:
	@echo "🧪 Running comprehensive Docker test suite..."
	@$(PYTHON) scripts/docker-test-comprehensive.py

docker-toolkit-quick:
	@echo "⚡ Running quick Docker validation tests..."
	@$(PYTHON) scripts/docker-test-quick.py

docker-toolkit-perf:
	@echo "📊 Running Docker performance tests..."
	@$(PYTHON) scripts/docker-test-standard.py

docker-toolkit-security:
	@echo "🔒 Running Docker security tests..."
	@$(PYTHON) scripts/docker-test.py security

docker-toolkit-comprehensive:
	@echo "🎯 Running full Docker comprehensive test suite..."
	@$(PYTHON) scripts/docker-test-comprehensive.py

# ============================================================================
# DOCUMENTATION COMMANDS
# ============================================================================

help-docs:
	@echo "Documentation Commands:"
	@echo "  docs-serve       - Serve documentation locally"
	@echo "  docs-build       - Build documentation site"
	@echo ""
	@echo "Usage examples:"
	@echo "  make docs-serve  # Start local documentation server"
	@echo "  make docs-build  # Build static documentation site"

# Documentation operations
docs-serve:
	@echo "📚 Serving documentation locally..."
	@$(PYTHON) scripts/docs-serve.py serve

docs-build:
	@echo "🏗️  Building documentation site..."
	@$(PYTHON) scripts/docs-serve.py build

# ============================================================================
# TESTING COMMANDS
# ============================================================================

help-test:
	@echo "Testing Commands:"
	@echo "  test             - Run tests with coverage and enhanced output"
	@echo "  test-quick       - Run tests without coverage (faster)"
	@echo "  test-plain       - Run tests with plain output"
	@echo "  test-parallel    - Run tests in parallel using multiple workers"
	@echo "  test-html        - Run tests and generate HTML report"
	@echo "  test-benchmark   - Run benchmark tests to measure performance"
	@echo "  test-coverage    - Generate comprehensive coverage reports"
	@echo "  test-coverage-clean - Clean coverage files and data"
	@echo "  test-coverage-open - Open HTML coverage report in browser"
	@echo ""
	@echo "Coverage options:"
	@echo "  FORMAT=html|xml|json|term - Coverage report format"
	@echo "  FAIL_UNDER=80             - Fail if coverage below percentage"
	@echo "  OPEN_BROWSER=1            - Open HTML report in browser"
	@echo "  QUICK=1                   - Quick coverage check without reports"
	@echo "  CLEAN=1                   - Clean coverage files before running"
	@echo "  SPECIFIC=tux/utils        - Run coverage for specific path"
	@echo "  PLAIN=1                   - Use plain output (disable pytest-sugar)"
	@echo "  XML_FILE=coverage.xml     - Custom XML filename"
	@echo ""
	@echo "Usage examples:"
	@echo "  make test                  # Run tests with coverage"
	@echo "  make test-quick            # Run tests without coverage"
	@echo "  make test-coverage FORMAT=html OPEN_BROWSER=1  # HTML coverage with browser"
	@echo "  make test-coverage FORMAT=xml XML_FILE=coverage-unit.xml  # Custom XML"

# Testing operations
test:
	@echo "🧪 Running tests with coverage and enhanced output..."
	@$(PYTHON) scripts/test-runner.py run

test-quick:
	@echo "⚡ Running tests without coverage (faster)..."
	@$(PYTHON) scripts/test-runner.py quick

test-plain:
	@echo "📝 Running tests with plain output..."
	@$(PYTHON) scripts/test-runner.py plain

test-parallel:
	@echo "🔄 Running tests in parallel..."
	@$(PYTHON) scripts/test-runner.py parallel

test-html:
	@echo "🌐 Running tests and generating HTML report..."
	@$(PYTHON) scripts/test-runner.py html

test-benchmark:
	@echo "📊 Running benchmark tests..."
	@$(PYTHON) scripts/test-runner.py benchmark

test-coverage:
	@echo "📈 Generating comprehensive coverage reports..."
	@$(PYTHON) scripts/test-runner.py coverage \
		$(if $(FORMAT),--format $(FORMAT)) \
		$(if $(FAIL_UNDER),--fail-under $(FAIL_UNDER)) \
		$(if $(OPEN_BROWSER),--open-browser) \
		$(if $(QUICK),--quick) \
		$(if $(CLEAN),--clean) \
		$(if $(SPECIFIC),--specific $(SPECIFIC)) \
		$(if $(PLAIN),--plain) \
		$(if $(XML_FILE),--xml-file $(XML_FILE))

test-coverage-clean:
	@echo "🧹 Cleaning coverage files and data..."
	@rm -rf .coverage htmlcov/ coverage.xml coverage.json

test-coverage-open:
	@echo "🌐 Opening HTML coverage report in browser..."
	@if [ -f "htmlcov/index.html" ]; then \
		xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html manually"; \
	else \
		echo "❌ HTML coverage report not found. Run 'make test-coverage FORMAT=html' first."; \
		exit 1; \
	fi

# ============================================================================
# CONVENIENCE TARGETS
# ============================================================================

# Run all quality checks
quality: lint type-check test-quick
	@echo "✅ All quality checks passed!"

# Run full development workflow
dev-workflow: quality format test
	@echo "🎉 Development workflow completed!"

# Clean all generated files
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf .pytest_cache/
	rm -rf tests/**/__pycache__/
	rm -rf htmlcov/
	rm -f .coverage
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	uv sync --group dev

# Install test dependencies
install-test:
	@echo "🧪 Installing test dependencies..."
	uv sync --group test

# Install documentation dependencies
install-docs:
	@echo "📚 Installing documentation dependencies..."
	uv sync --group docs

# Install all dependencies
install-all: install-dev install-test install-docs
	@echo "🎉 All dependencies installed!"

# Update dependencies
update-deps:
	@echo "⬆️  Updating dependencies..."
	uv lock --upgrade
	uv sync

# Show project status
status:
	@echo "📊 Tux Project Status"
	@echo "====================="
	@echo "Python version: $(shell $(PYTHON) --version)"
	@echo "Environment: $(MODE)"
	@echo "Package manager: $(PYTHON)"
	@echo ""
	@echo "Database:"
	@make -s db-current || echo "  ❌ Database connection failed"
	@echo ""
	@echo "Docker:"
	@make -s docker-ps || echo "  ❌ Docker not available"
	@echo ""
	@echo "Tests:"
	@make -s test-quick || echo "  ❌ Tests failed"
