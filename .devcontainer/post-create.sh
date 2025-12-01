#!/bin/bash
set -e

echo "🚀 Setting up Tux development environment..."

# Install uv if not already installed
if ! command -v uv > /dev/null 2>&1; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"

    # Add to bashrc for persistence
    # Use single quotes to write literal $HOME and $PATH (they'll expand when bashrc is sourced)
    # shellcheck disable=SC2016
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
fi

# Verify uv installation
if command -v uv > /dev/null 2>&1; then
    echo "✅ uv installed: $(uv --version)"
else
    echo "❌ Failed to install uv"
    exit 1
fi

# Sync all dependencies
echo "📥 Installing dependencies..."
uv sync --all-groups

# Verify Python environment
echo "🐍 Python environment:"
python --version
which python

# Verify imports work
echo "🔍 Verifying Python path..."
python -c "import sys; print('Python path:'); [print(f'  {p}') for p in sys.path if 'tux' in p.lower() or 'src' in p.lower()]"

echo "✅ Development environment setup complete!"
