#!/bin/bash
# ==============================================================================
# CLOUDFLARE WORKERS BUILDS - BUILD DOCS WITH FRESH COVERAGE
# ==============================================================================
# This script runs on Cloudflare Workers to:
# 1. Run tests to generate fresh coverage reports
# 2. Copy coverage reports to docs directory for MkDocs
# 3. Build MkDocs documentation with coverage included
# ==============================================================================

set -e  # Exit on any error

echo "🚀 Starting docs build with fresh test coverage..."

# Change to project root (docs/ is the working directory)
cd ..

# Set up test environment
echo "🔧 Setting up test environment..."
export BOT_TOKEN=test_token_for_cloudflare
export DEBUG=True

# Install test dependencies
echo "📦 Installing test dependencies..."
uv sync --group test --no-dev

# Run tests with coverage
echo "🧪 Running tests with coverage..."
uv run pytest \
    --cov-report=xml:coverage.xml \
    --cov-report=html:htmlcov \
    --cov-report=term-missing:skip-covered \
    --junitxml=junit.xml \
    --cov-fail-under=0 \
    tests/unit/ tests/integration/ tests/e2e/

echo "✅ Tests completed successfully"

# Copy coverage reports to docs directory for MkDocs
echo "📋 Copying coverage reports to docs directory..."
if [ -d "htmlcov" ]; then
    cp -r htmlcov docs/
    echo "✅ Copied htmlcov to docs/"
else
    echo "❌ htmlcov directory not found"
    exit 1
fi

# Change back to docs directory for MkDocs build
cd docs

# Build MkDocs documentation
echo "📚 Building MkDocs documentation..."
uv run mkdocs build

echo "✅ Documentation build completed successfully"
