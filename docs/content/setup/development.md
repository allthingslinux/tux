# Development Setup

Complete guide for setting up a development environment for Tux.

## Prerequisites

### Required Software

### Python 3.13+

```bash
# Check Python version
python3 --version

# Install Python 3.13 (Ubuntu/Debian)
sudo apt update
sudo apt install python3.13 python3.13-dev python3.13-venv

# macOS with Homebrew
brew install python@3.13
```

### uv (Python Package Manager)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Verify installation
uv --version
```

### PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
```

### Git

```bash
# Ubuntu/Debian
sudo apt install git

# macOS
brew install git

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Optional Software

### Docker & Docker Compose

```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# macOS
brew install docker docker-compose
```

### VS Code (Recommended IDE)

```bash
# Download from https://code.visualstudio.com/
# Or install via package manager

# Recommended extensions:
# - Python
# - Pylance
# - Ruff
# - GitLens
# - Docker
```

## Local Development Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/allthingslinux/tux.git
cd tux

# Create development branch
git checkout -b feature/your-feature-name
```

### 2. Python Environment

```bash
# Install dependencies with uv
uv sync

# Verify installation
uv run python --version
uv run python -c "import tux; print('Tux imported successfully')"
```

### 3. Database Setup

**Create Database:**

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE tux_dev;
CREATE USER tux_dev WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE tux_dev TO tux_dev;
\q
```

**Configure Environment:**

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

**Example .env for development:**

```bash
# Discord (create a test bot)
DISCORD_TOKEN=<your_test_discord_token>

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tux_dev
POSTGRES_USER=tux_dev
POSTGRES_PASSWORD=dev_password

# Environment
DEBUG=true

# Optional: Sentry (use test project)
EXTERNAL_SERVICES__SENTRY_DSN=https://your-test-dsn@sentry.io/project-id
```

**Run Migrations:**

```bash
# Apply database migrations
uv run db migrate-push

# Verify database setup
uv run db health
```

### 4. Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run dev pre-commit install

# Test pre-commit hooks
uv run dev pre-commit run --all-files
```

### 5. Start Development

```bash
# Start bot in development mode
uv run tux start --debug

# Or with auto-reload (if available)
uv run tux start --debug --reload
```

## Docker Development Setup

### 1. Docker Compose

**Start Services:**

```bash
# Start all services in background
uv run docker up -d

# View logs
uv run docker logs -f

# Stop services
uv run docker down
```

**Services:**

- `tux` - Main bot application
- `postgres` - PostgreSQL database
- `redis` - Redis cache (optional)

### 2. Development Workflow

**Code Changes:**

```bash
# Rebuild after code changes
uv run docker build

# Restart specific service
docker-compose restart tux

# View service logs
uv run docker logs tux
```

**Database Operations:**

```bash
# Run migrations in container
docker-compose exec tux uv run db migrate-push

# Access database
docker-compose exec postgres psql -U tux tux
```

**Shell Access:**

```bash
# Access container shell
uv run docker shell

# Run commands in container
docker-compose exec tux uv run tux --help
```

## Development Tools

### Code Quality

**Linting and Formatting:**

```bash
# Run all quality checks
uv run dev all

# Individual tools
uv run dev lint        # Ruff linting
uv run dev format      # Code formatting
uv run dev type-check  # Type checking with basedpyright
```

**Pre-commit Checks:**

```bash
# Run pre-commit on all files
uv run dev pre-commit run --all-files

# Run pre-commit on staged files
uv run dev pre-commit
```

### Testing

**Run Tests:**

```bash
# Run all tests with coverage
uv run test run

# Quick tests (no coverage)
uv run test quick

# Run specific test file
uv run test run tests/test_specific.py

# Run tests with specific marker
uv run test run -m "not slow"
```

**Coverage Reports:**

```bash
# Generate HTML coverage report
uv run test html

# View coverage in terminal
uv run test coverage

# Coverage reports available in htmlcov/
```

### Database Development

**Migration Commands:**

```bash
# Generate new migration
uv run db migrate-generate "description of changes"

# Apply migrations
uv run db migrate-push

# Check migration status
uv run db status

# Rollback migration (if needed)
uv run db migrate-rollback
```

**Database Utilities:**

```bash
# Check database health
uv run db health

# Reset database (development only)
uv run db reset

# Seed database with test data
uv run db seed
```

## IDE Configuration

### VS Code Setup

**Recommended Settings (.vscode/settings.json):**

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        ".coverage": true,
        "htmlcov": true
    }
}
```

**Recommended Extensions:**

- Python (Microsoft)
- Pylance (Microsoft)
- Ruff (Astral Software)
- GitLens (GitKraken)
- Docker (Microsoft)
- PostgreSQL (Chris Kolkman)

### PyCharm Setup

**Project Configuration:**

1. Open project in PyCharm
2. Configure Python interpreter: `.venv/bin/python`
3. Enable pytest as test runner
4. Configure Ruff as external tool
5. Set up database connection

**Code Style:**

- Import PyCharm code style from `.editorconfig`
- Configure Ruff as external formatter
- Enable type checking with basedpyright

## Development Workflow

### Daily Development

**Start Development Session:**

```bash
# Update repository
git pull origin main

# Update dependencies
uv sync

# Apply any new migrations
uv run db migrate-push

# Start development server
uv run tux start --debug
```

**Code Quality Workflow:**

```bash
# Before committing
uv run dev all          # Run all quality checks
uv run test run         # Run tests
git add .               # Stage changes
git commit -m "feat: add new feature"  # Commit with conventional format
```

### Testing Workflow

**Test-Driven Development:**

```bash
# Write test first
# tests/test_new_feature.py

# Run specific test
uv run test run tests/test_new_feature.py

# Implement feature
# src/tux/modules/new_feature.py

# Run test again to verify
uv run test run tests/test_new_feature.py

# Run all tests
uv run test run
```

**Integration Testing:**

```bash
# Test with real Discord bot (test server)
uv run tux start --debug

# Test commands in Discord
# Verify database changes
# Check logs for errors
```

## Debugging

### Application Debugging

**Debug Mode:**

```bash
# Start with debug logging
uv run tux start --debug

# Enable specific debug categories
LOG_LEVEL=DEBUG uv run tux start
```

**Python Debugger:**

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

**VS Code Debugging:**

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Tux",
            "type": "python",
            "request": "launch",
            "module": "tux",
            "console": "integratedTerminal",
            "env": {
                "LOG_LEVEL": "DEBUG"
            }
        }
    ]
}
```

### Database Debugging

**Query Logging:**

```bash
# Enable SQL query logging
DATABASE_URL=postgresql://user:pass@host:5432/db?echo=true
```

**Database Console:**

```bash
# Access database directly
psql postgresql://tux_dev:dev_password@localhost:5432/tux_dev

# Or through Docker
docker-compose exec postgres psql -U tux tux
```

**Migration Debugging:**

```bash
# Check migration history
uv run db history

# Show current migration
uv run db current

# Show pending migrations
uv run db pending
```

## Performance Profiling

### Application Profiling

**Memory Profiling:**

```bash
# Install memory profiler
uv add memory-profiler

# Profile memory usage
python -m memory_profiler src/tux/__main__.py
```

**Performance Profiling:**

```python
# Add profiling to specific functions
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

### Database Profiling

**Query Performance:**

```sql
-- Enable query timing
\timing on

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM cases WHERE guild_id = 123;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

## Troubleshooting

### Common Issues

**Import Errors:**

```bash
# Reinstall dependencies
uv sync --reinstall

# Check Python path
uv run python -c "import sys; print(sys.path)"
```

**Database Connection Issues:**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql postgresql://tux_dev:dev_password@localhost:5432/tux_dev

# Check environment variables
echo $DATABASE_URL
```

**Bot Permission Issues:**

```bash
# Check bot token
# Verify bot permissions in Discord
# Check OAuth2 scopes
# Re-invite bot if necessary
```

**Docker Issues:**

```bash
# Check Docker status
docker --version
docker-compose --version

# Rebuild containers
uv run docker build --no-cache

# Check container logs
uv run docker logs tux
```

### Getting Help

**Documentation:**

- Check error messages carefully
- Review relevant documentation sections
- Search GitHub issues

**Community:**

- Join Discord support server
- Ask questions in development channels
- Report bugs on GitHub

**Debugging Tools:**

```bash
# Check system resources
htop
df -h
free -h

# Check network connectivity
ping discord.com
nslookup discord.com

# Check application logs
journalctl -u tux -f
tail -f /var/log/tux/tux.log
```

This development setup guide provides everything needed to start contributing to Tux. Follow the
steps appropriate for your development environment and preferred tools.
