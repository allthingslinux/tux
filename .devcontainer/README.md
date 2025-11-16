# DevContainer Configuration

This directory contains the VS Code DevContainer configuration for Tux development.

## Features

- **Python 3.13** - Matches project requirements
- **UV Package Manager** - Fast Python package management
- **Docker-in-Docker** - For running Docker Compose services
- **Pre-configured Extensions** - All recommended VS Code extensions
- **Aligned Settings** - Matches workspace `.vscode/settings.json`

## Quick Start

1. **Open in VS Code**: Open the project folder in VS Code
2. **Reopen in Container**: When prompted, click "Reopen in Container" or use Command Palette → "Dev Containers: Reopen in Container"
3. **Wait for Setup**: The container will build and run `post-create.sh` to install dependencies
4. **Start Coding**: Everything is ready!

## What Gets Installed

The `post-create.sh` script automatically:
- Installs `uv` package manager
- Syncs all project dependencies (`uv sync --all-groups`)
- Configures Python environment
- Verifies imports work correctly

## Port Forwarding

The following ports are automatically forwarded:
- **8000** - MkDocs documentation server (`uv run docs serve`)
- **5432** - PostgreSQL database (if using Docker Compose)

## Using Docker Compose Services

To use PostgreSQL from `compose.yaml`:

1. Start services: `docker compose up -d`
2. Connect to database at `localhost:5432`
3. Use Adminer at `localhost:8080` (if enabled)

## Environment Variables

The container sets:
- `PYTHONPATH=${workspaceFolder}/src` - For Python imports
- `PATH` includes `~/.cargo/bin` - For `uv` command

## Troubleshooting

### Dependencies Not Installing
- Check that `uv sync --all-groups` completed successfully
- Verify `.venv` directory exists in workspace

### Python Imports Failing
- Ensure `PYTHONPATH` includes `${workspaceFolder}/src`
- Check that `src/tux/` directory exists

### Port Forwarding Not Working
- Check VS Code port forwarding panel
- Verify services are running in container

## Manual Setup

If automatic setup fails, run manually:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Install dependencies
uv sync --all-groups

# Verify setup
python -c "from tux.core.logging import configure_logging; print('✅ Setup complete')"
```
