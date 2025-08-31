.PHONY: help help-db help-dev help-docker help-docs help-test

help:
	@echo "Tux - Simple Discord Bot Commands"
	@echo "=================================="
	@echo ""
	@echo "🚀 QUICK START:"
	@echo "  make start        - Start the bot (auto-detects environment)"
	@echo "  make run          - Quick alias for start"
	@echo "  uv run tux        - Direct command (bypass Makefile)"
	@echo ""
	@echo "🔧 DEVELOPMENT:"
	@echo "  make docker-up    - Start PostgreSQL in Docker"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make adminer      - Start Adminer database admin tool"
	@echo "  make test         - Run test suite"
	@echo "  make lint         - Check code quality"
	@echo "  make format       - Format code"
	@echo ""
	@echo "📚 DOCUMENTATION:"
	@echo "  make docs         - Build documentation"
	@echo "  make docs-env     - Generate .env template"
	@echo "  make help-db      - Database management commands"
	@echo ""
	@echo "Environment variables:"
	@echo "  PYTHON=uv        - Python package manager (default: uv)"

# Environment setup
PYTHON := uv run python

# ============================================================================
# MAIN COMMANDS
# ============================================================================

# Start the Discord bot (auto-detects environment)
start:
	@echo "🚀 Starting Tux Discord bot..."
	@uv run tux

# Quick run command
run:
	@echo "🚀 Starting Tux..."
	@uv run tux

# Start in development mode (local)
dev:
	@echo "🔧 Starting Tux in development mode..."
	@uv run tux

# Start in production mode (Docker)
prod:
	@echo "🚀 Starting Tux in production mode..."
	@uv run tux

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
	@echo "  db-tables         - List all database tables with row counts"
	@echo "  db-queries        - Check for long-running queries"
	@echo "  db-analyze        - Analyze table statistics for optimization"
	@echo "  db-reindex        - Reindex tables for performance"
	@echo "  db-vacuum         - Vacuum database for maintenance"
	@echo "  db-optimize       - Analyze database and suggest optimizations"
	@echo "  adminer          - Start Adminer database admin tool"
	@echo "  adminer-stop     - Stop Adminer database admin tool"
	@echo "  adminer-logs     - Show Adminer logs"
	@echo "  adminer-plugins-list     - List available Adminer plugins"
	@echo "  adminer-plugins-install  - Install Adminer plugins"
	@echo "  adminer-plugins-remove   - Remove Adminer plugins"
	@echo "  db-config         - Show PostgreSQL configuration details"
	@echo "  db-demo           - Demonstrate advanced PostgreSQL features"
	@echo ""

help-adminer:
	@echo "Adminer Database Admin Tool Commands:"
	@echo "  adminer               - Start Adminer web interface"
	@echo "  adminer-stop          - Stop Adminer web interface"
	@echo "  adminer-logs          - Show Adminer container logs"
	@echo ""
	@echo "Adminer Plugin Management:"
	@echo "  adminer-plugins-list          - List all available plugins"
	@echo "  adminer-plugins-install       - Install default plugin set"
	@echo "  adminer-plugins-install PLUGINS='plugin1 plugin2'  - Install specific plugins"
	@echo "  adminer-plugins-remove PLUGINS='plugin1'           - Remove plugins"
	@echo ""
	@echo "Examples:"
	@echo "  make adminer                          # Start Adminer"
	@echo "  make adminer-plugins-install          # Install default plugins"
	@echo "  make adminer-plugins-list             # See available plugins"
	@echo ""
	@echo "Usage examples:"
	@echo "  make db-upgrade          # Upgrade database"
	@echo "  make db-revision            # Create new migration"
	@echo "  make db-reset              # Reset database (with confirmation)"
	@echo "  make db-health             # Check database health"
	@echo "  make db-performance        # Analyze performance metrics"
	@echo "  make db-tables             # List all tables"
	@echo "  make db-vacuum             # Run database maintenance"
	@echo "  make db-optimize           # Get optimization recommendations"
	@echo "  make adminer               # Start database admin tool"
	@echo "  make adminer-plugins-list      # List available plugins"
	@echo "  make adminer-plugins-install   # Install default plugins"
	@echo "  make adminer-plugins-install PLUGINS='tables-filter dump-json'  # Install specific plugins"
	@echo "  uv run python3 docker/adminer/install-plugins.py --list  # Direct Python usage"

# Database operations
db-upgrade:
	@echo "⬆️  Upgrading database to latest migration..."
	@$(PYTHON) scripts/db-migrate.py upgrade

db-downgrade:
	@echo "⬇️  Downgrading database by one migration..."
	@$(PYTHON) scripts/db-migrate.py downgrade

db-revision:
	@echo "📝 Creating new migration revision..."
	@$(PYTHON) scripts/db-migrate.py revision

db-current:
	@echo "📊 Getting current migration version..."
	@$(PYTHON) scripts/db-migrate.py current

db-history:
	@echo "📚 Showing migration history..."
	@$(PYTHON) scripts/db-migrate.py history

db-reset:
	@echo "⚠️  WARNING: This will reset the database and destroy all data!"
	@read -p "Are you sure? (type 'yes' to continue): " confirm && [ "$$confirm" = "yes" ] || (echo "Operation cancelled" && exit 1)
	@echo "🔄 Resetting database..."
	@$(PYTHON) scripts/db-migrate.py reset

db-reset-migrations:
	@echo "⚠️  WARNING: This will reset all migrations and create a clean baseline!"
	@echo "This will:"
	@echo "  1. Drop all database data"
	@echo "  2. Delete all migration files"
	@echo "  3. Create a fresh baseline migration"
	@echo "  4. Apply the new migration"
	@read -p "Are you sure? (type 'yes' to continue): " confirm && [ "$$confirm" = "yes" ] || (echo "Operation cancelled" && exit 1)
	@echo "🔄 Resetting migrations..."
	@$(PYTHON) scripts/db-migrate.py reset-migrations

# Advanced database tools
db-health:
	@echo "🏥 Running comprehensive database health check..."
	@$(PYTHON) scripts/db-health.py

db-performance:
	@echo "📊 Analyzing database performance metrics..."
	@$(PYTHON) scripts/db-metrics.py

db-stats:
	@echo "📋 Showing table statistics and metrics..."
	@$(PYTHON) scripts/db-metrics.py

db-tables:
	@echo "📋 Listing all database tables..."
	@$(PYTHON) scripts/db-tables.py

db-queries:
	@echo "🔍 Checking for long-running queries..."
	@$(PYTHON) scripts/db-queries.py

db-analyze:
	@echo "📊 Analyzing table statistics..."
	@$(PYTHON) scripts/db-analyze.py

db-reindex:
	@echo "🔄 Reindexing database tables..."
	@$(PYTHON) scripts/db-reindex.py

db-vacuum:
	@echo "📊 Showing database information and maintenance status..."
	@$(PYTHON) scripts/db-vacuum.py

db-optimize:
	@echo "🔧 Analyzing database optimization opportunities..."
	@$(PYTHON) scripts/db-optimize.py

# ============================================================================
# ADMINER MANAGEMENT
# ============================================================================

adminer:
	@echo "🗄️  Starting Adminer database admin tool..."
	@echo "🌐 Access at: http://localhost:$${ADMINER_PORT:-8081}"
	@echo "🔒 Manual login required for security"
	@$(PYTHON) scripts/docker-compose.py up tux-adminer -d

adminer-stop:
	@echo "🛑 Stopping Adminer database admin tool..."
	@$(PYTHON) scripts/docker-compose.py down tux-adminer

adminer-logs:
	@echo "📋 Showing Adminer logs..."
	@$(PYTHON) scripts/docker-compose.py logs tux-adminer -f

# Adminer plugin management
adminer-plugins-list:
	@echo "📋 Listing available Adminer plugins..."
	@uv run python3 docker/adminer/install-plugins.py --list

adminer-plugins-install:
	@echo "📥 Installing Adminer plugins..."
	@if [ -z "$(PLUGINS)" ]; then \
		echo "Installing default plugins..."; \
		uv run python3 docker/adminer/install-plugins.py --default; \
	else \
		echo "Installing plugins: $(PLUGINS)"; \
		uv run python3 docker/adminer/install-plugins.py --install $(PLUGINS); \
	fi
	@echo "🔄 Restarting Adminer to apply plugin changes..."
	@$(PYTHON) scripts/docker-compose.py restart tux-adminer

adminer-plugins-remove:
	@echo "🗑️  Removing Adminer plugins: $(PLUGINS)"
	@if [ -z "$(PLUGINS)" ]; then \
		echo "❌ No plugins specified. Use: make adminer-plugins-remove PLUGINS='plugin1 plugin2'"; \
		exit 1; \
	fi
	@uv run python3 docker/adminer/install-plugins.py --remove $(PLUGINS)
	@echo "🔄 Restarting Adminer to apply changes..."
	@$(PYTHON) scripts/docker-compose.py restart tux-adminer

db-config:
	@echo "⚙️  PostgreSQL configuration analysis..."
	@echo "📁 Config file: docker/postgres/postgresql.conf"
	@echo "🔧 Key optimizations:"
	@echo "  - shared_buffers: 256MB (25% RAM)"
	@echo "  - work_mem: 16MB (complex queries)"
	@echo "  - maintenance_work_mem: 128MB (maintenance)"
	@echo "  - random_page_cost: 1.1 (SSD optimized)"
	@echo "  - effective_io_concurrency: 200 (parallel I/O)"

db-demo:
	@echo "🎮 Demonstrating advanced PostgreSQL features..."
	@$(PYTHON) scripts/db-metrics.py

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
	@echo "Environment-specific Docker commands:"
	@echo "  docker-dev       - Start development environment"
	@echo "  docker-prod      - Start production environment"
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
	@echo "  make docker-dev              # Start development environment"
	@echo "  make docker-prod             # Start production environment"
	@echo "  make docker-build NO_CACHE=1 # Build without cache"
	@echo "  make docker-logs FOLLOW=1 TAIL=50   # Follow logs with tail"

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

# Environment-specific Docker commands
docker-dev:
	@echo "🔧 Starting development environment..."
	@$(PYTHON) scripts/docker-compose.py up \
		$(if $(DETACH),-d) \
		$(if $(BUILD),--build) \
		$(if $(WATCH),--watch)

docker-prod:
	@echo "🚀 Starting production environment..."
	@$(PYTHON) scripts/docker-compose.py up \
		$(if $(DETACH),-d) \
		$(if $(BUILD),--build)

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
	@echo "Configuration Documentation:"
	@echo "  docs-config      - Generate configuration documentation from Pydantic settings"
	@echo "  docs-env         - Generate .env file template from Pydantic settings"
	@echo "  docs-env-example - Generate env.example template from Pydantic settings"
	@echo "  docs-config-markdown - Generate Markdown configuration documentation"
	@echo "  docs-config-update - Update README with configuration documentation"
	@echo ""
	@echo "Usage examples:"
	@echo "  make docs-serve  # Start local documentation server"
	@echo "  make docs-build  # Build static documentation site"
	@echo "  make docs-env    # Generate .env template"
	@echo "  make docs-env-example # Generate env.example template"

# Documentation operations
docs-serve:
	@echo "📚 Serving documentation locally..."
	@$(PYTHON) scripts/docs-serve.py serve

docs-build:
	@echo "🏗️  Building documentation site..."
	@$(PYTHON) scripts/docs-serve.py build

# Configuration documentation using settings-doc
docs-config:
	@echo "📋 Generating configuration documentation from Pydantic settings..."
	@uv run settings-doc generate --module tux.shared.config.settings --output-format markdown

docs-env:
	@echo "🔧 Generating .env file template from Pydantic settings..."
	@uv run settings-doc generate --module tux.shared.config.settings --output-format dotenv --update .env

docs-env-example:
	@echo "🔧 Generating env.example template from Pydantic settings..."
	@uv run settings-doc generate --module tux.shared.config.settings --output-format dotenv --update env.example

docs-config-markdown:
	@echo "📝 Generating Markdown configuration documentation..."
	@uv run settings-doc generate --module tux.shared.config.settings --output-format markdown --update CONFIG.md --between "<!-- CONFIGURATION START -->" "<!-- CONFIGURATION END -->" --heading-offset 1

docs-config-update:
	@echo "🔄 Updating README with configuration documentation..."
	@uv run settings-doc generate \
		--module tux.shared.config.settings \
		--output-format markdown \
		--update README.md \
		--between "<!-- CONFIGURATION START -->" "<!-- CONFIGURATION END -->" \
		--heading-offset 2

# ============================================================================
# TESTING COMMANDS
# ============================================================================

help-test:
	@echo "Testing Commands:"
	@echo "  test             - Run tests with coverage and enhanced output"
	@echo "  test-unit        - Run only unit tests (fast, isolated)"
	@echo "  test-integration - Run only integration tests (slower, real deps)"
	@echo "  test-e2e         - Run only end-to-end tests"
	@echo "  test-slow        - Run only slow tests"
	@echo "  test-all         - Run complete test suite with full coverage"
	@echo "  test-validate    - Validate testing infrastructure alignment"
	@echo "  test-setup       - Test configuration setup and validation"
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
	@echo "  make test-setup            # Test configuration setup"
	@echo "  make test-quick            # Run tests without coverage"
	@echo "  make test-coverage FORMAT=html OPEN_BROWSER=1  # HTML coverage with browser"
	@echo "  make test-coverage FORMAT=xml XML_FILE=coverage-unit.xml  # Custom XML"

# Testing operations
test:
	@echo "🧪 Running tests with coverage and enhanced output..."
	@$(PYTHON) scripts/test-runner.py run

test-unit:
	@echo "🧪 Running unit tests (fast, isolated)..."
	@uv run pytest tests/unit/ -m "unit and not slow"

test-integration:
	@echo "🔗 Running integration tests (slower, real dependencies)..."
	@uv run pytest tests/integration/ -m "integration and not slow" --integration

test-e2e:
	@echo "🌐 Running end-to-end tests..."
	@uv run pytest tests/e2e/ -m "e2e and not slow"

test-slow:
	@echo "🐌 Running slow tests..."
	@uv run pytest tests/ -m "slow"



test-all:
	@echo "🚀 Running complete test suite with coverage..."
	@uv run pytest tests/

test-validate:
	@echo "🔍 Validating testing infrastructure alignment..."
	@echo "✅ Checking CI configuration..."
	@grep -q "UNIT_MARKERS" .github/workflows/tests.yml && echo "  ✓ CI unit markers configured" || echo "  ✗ CI unit markers missing"
	@grep -q "INTEGRATION_MARKERS" .github/workflows/tests.yml && echo "  ✓ CI integration markers configured" || echo "  ✗ CI integration markers missing"
	@echo "✅ Checking pytest configuration..."
	@grep -q "unit:" pyproject.toml && echo "  ✓ Unit test markers defined" || echo "  ✗ Unit markers missing"
	@grep -q "integration:" pyproject.toml && echo "  ✓ Integration test markers defined" || echo "  ✗ Integration markers missing"
	@echo "✅ Checking Make commands..."
	@grep -q "test-unit:" Makefile && echo "  ✓ Make test-unit command exists" || echo "  ✗ test-unit missing"
	@grep -q "test-integration:" Makefile && echo "  ✓ Make test-integration command exists" || echo "  ✗ test-integration missing"
	@echo "✅ Checking coverage configuration..."
	@grep -q "src/tux" pyproject.toml && echo "  ✓ Coverage source path correct" || echo "  ✗ Coverage source path incorrect"
	@echo "✅ Checking Codecov flags..."
	@grep -q "unit:" codecov.yml && echo "  ✓ Unit flag configured" || echo "  ✗ Unit flag missing"
	@grep -q "integration:" codecov.yml && echo "  ✓ Integration flag configured" || echo "  ✗ Integration flag missing"
	@grep -q "e2e:" codecov.yml && echo "  ✓ E2E flag configured" || echo "  ✗ E2E flag missing"
	@echo "🎉 Testing infrastructure validation complete!"

test-setup: ## Test configuration setup
	@echo "🔧 Testing configuration setup..."
	@$(PYTHON) scripts/test-setup.py

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
	@echo "Environment: $(shell $(PYTHON) -c 'from tux.shared.config.environment import get_environment_name; print(get_environment_name())' 2>/dev/null || echo 'unknown')"
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
