<!-- markdownlint-disable MD041 -->

> [!NOTE]
**Tux v0.1.0 is our first major release! If you encounter any issues or need support, please join our community server [on Discord](https://discord.gg/gpmSjcjQxg) for help and announcements.**

<div align="center">
    <p align="center">
        <!-- Latest Release & Tech Stack -->
        <a href="https://github.com/allthingslinux/tux/releases">
            <img alt="GitHub Release" src="https://img.shields.io/github/v/release/allthingslinux/tux?logo=github&logoColor=white"></a>
        <a href="https://python.org">
            <img alt="Python" src="https://img.shields.io/badge/python-3.13.2+-blue?logo=python&logoColor=white"></a>
        <a href="https://docs.astral.sh/uv">
            <img alt="Uv" src="https://img.shields.io/badge/uv-0.4.0+-purple?logo=uv&logoColor=white"></a>
        <!-- CI/CD & Quality -->
        <a href="https://results.pre-commit.ci/latest/github/allthingslinux/tux/main">
            <img alt="pre-commit.ci status" src="https://results.pre-commit.ci/badge/github/allthingslinux/tux/main.svg"></a>
        <a href="https://codecov.io/gh/allthingslinux/tux">
            <img alt="Codecov" src="https://codecov.io/gh/allthingslinux/tux/graph/badge.svg?token=R0AUAS996W"></a>
        <!-- Community & Legal -->
        <a href="https://github.com/allthingslinux/tux/blob/main/LICENSE">
            <img alt="License" src="https://img.shields.io/github/license/allthingslinux/tux?logo=gnu&logoColor=white"></a>
    </p>
</div>

<img align="center" src="assets/readme-banner.png" alt="Banner">

<div align="center" style="display: flex; justify-content: center; align-items: center;">
    <table align="center" style="vertical-align: middle;">
        <tr style="vertical-align: middle;">
            <td style="vertical-align: middle;"><a href="https://tux.atl.dev">📚 Docs</a></td>
            <td style="vertical-align: middle;"><a href="https://github.com/allthingslinux/tux/issues/525">🗺️ Roadmap</a></td>
            <td style="vertical-align: middle;"><a href="https://github.com/allthingslinux/tux/issues/157">📦 Deps</a></td>
            <td style="vertical-align: middle;"><a href="https://discord.gg/gpmSjcjQxg">💬 Support</a></td>
        </tr>
    </table>
</div>

# The all-in-one open source Discord bot

## About

Tux is an all-in-one open source Discord bot, originally designed for the [All Things Linux](https://allthingslinux.org) community.

It is designed to provide a variety of features to the server, including moderation, support, utility, and various fun commands.

<!-- Table of Contents -->

## Table of Contents

- [About](#about)
- [Table of Contents](#table-of-contents)
- [Tech Stack](#tech-stack)
- [Bot Features](#bot-features)
- [Plugin System](#plugin-system)
- [Database Features](#database-features)
- [Installation and Development](#installation-and-development)
  - [Prerequisites](#prerequisites)
  - [Setup & Workflow](#setup--workflow)
- [Documentation & Support](#documentation--support)
- [Quick Commands](#quick-commands)
- [License](#license)
- [Metrics](#metrics)
- [Contributors](#contributors)

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Runtime** | Python 3.13+ with `discord.py` |
| **Dependencies** | `uv` for fast, reliable package management |
| **Database** | Type-safe ORM using `SQLModel` with `SQLAlchemy` |
| **Containers** | Docker & Docker Compose for development environments |
| **Type Safety** | Strict typing with `basedpyright` and comprehensive type hints |
| **Code Quality** | Linting and formatting via `ruff` |
| **Pre-commit** | Automated code quality checks before commits |
| **CLI** | Custom command-line interface built with `typer` and `uv` scripts |
| **Logging** | Structured logging with `loguru` |
| **Error Tracking** | Exception handling and monitoring with `sentry-sdk` |
| **HTTP Client** | Modern async requests with `httpx` |
| **Configuration** | Dynamic environment management with `pydantic-settings` & `python-dotenv` |

<sub>[back to top ↑](#table-of-contents)</sub>

## Bot Features

- **Hybrid Commands**: Support for both slash commands and traditional prefix commands
- **Dynamic Permissions**: Database-driven permission system with configurable ranks (0-10)
- **Hot Reload**: Automatic cog reloading during development with file watching
- **Plugin System**: Modular, hot-reloadable extensions for custom functionality
- **Error Handling**: Centralized error handling with Sentry integration
- **Rich Embeds**: Branded, interactive embeds and components
- **Configuration**: Multi-format config support with interactive setup wizard

<sub>[back to top ↑](#table-of-contents)</sub>

## Plugin System

Modular plugin architecture for extending functionality without modifying core code:

- **Hot-Reloadable**: Load/unload plugins during development without restarts
- **Isolated**: Plugin failures don't affect core bot functionality
- **Database Access**: Full access to bot's database through type-safe controllers
- **Event Integration**: Hook into Discord events and bot lifecycle

**Plugin Development**: Located in `src/tux/plugins/` with automatic discovery and full bot API access.

<sub>[back to top ↑](#table-of-contents)</sub>

## Database Features

**SQLModel**-powered type-safe database operations with async PostgreSQL support:

- **Type Safety**: Compile-time checking with automatic Pydantic serialization
- **Async Operations**: High-performance queries with connection pooling
- **Controller Pattern**: Clean separation of business logic and data access
- **Migration System**: Alembic-powered schema management with version control
- **Advanced Controllers**: CRUD, bulk operations, pagination, and upserts
- **Multi-Database**: PostgreSQL primary, SQLite testing, psycopg backup

<sub>[back to top ↑](#table-of-contents)</sub>

## Installation and Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- A PostgreSQL database (e.g. via [Supabase](https://supabase.io/) or local installation)
- Optional: [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)

### Setup & Workflow

1. **Clone the repository:**

   ```bash
   git clone https://github.com/allthingslinux/tux.git
   cd tux
   ```

2. **Install dependencies:**

   ```bash
   uv sync
   ```

   For developers, you can install the pre-commit hooks with:

   ```bash
   uv run pre-commit install
   ```

   Configure git to ignore formatting commits in blame:

   ```bash
   git config blame.ignoreRevsFile .git-blame-ignore-revs
   ```

3. **Configure your environment:**

   ```bash
   # Generate example config files
   uv run config generate

   # Copy and edit to your needs
   cp .env.example .env
   cp config/config.toml.example config/config.toml
   ```

4. **Start the bot:**

   ```bash
   # Start the bot (or use docker per the docs)
   uv run tux start
   ```

<sub>[back to top ↑](#table-of-contents)</sub>

## Documentation & Support

- **[Full Documentation](https://tux.atl.dev)** - Complete guides for users, admins, developers, and self-hosters
- **[Getting Started](https://tux.atl.dev/getting-started/)** - Setup instructions for all user types
- **[Developer Guide](https://tux.atl.dev/developer/)** - Architecture, contributing, and plugin development
- **[Self-Hosting](https://tux.atl.dev/selfhost/)** - Docker deployment and configuration
- **[API Reference](https://tux.atl.dev/reference/)** - Complete codebase and CLI documentation
- **[Discord Community](https://discord.gg/gpmSjcjQxg)** - Live support and discussions
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Bug reports and feature requests

<sub>[back to top ↑](#table-of-contents)</sub>

## Quick Commands

| Category | Command | Description |
|----------|---------|-------------|
| **Bot** | `uv run tux start` | Start the Tux Discord bot |
| | `uv run tux version` | Show Tux version information |
| **Development** | `uv run dev lint` | Run linting with Ruff |
| | `uv run dev lint-fix` | Run linting with Ruff and apply fixes |
| | `uv run dev format` | Format code with Ruff |
| | `uv run dev type-check` | Check types with basedpyright |
| | `uv run dev lint-docstring` | Lint docstrings with pydoclint |
| | `uv run dev docstring-coverage` | Check docstring coverage |
| | `uv run dev pre-commit` | Run pre-commit checks |
| | `uv run dev all` | Run all development checks |
| **Testing** | `uv run tests all` | Run all tests with coverage and enhanced output |
| | `uv run tests quick` | Run tests without coverage (faster) |
| | `uv run tests plain` | Run tests with plain output |
| | `uv run tests parallel` | Run tests in parallel |
| | `uv run tests html` | Run tests and generate HTML report |
| | `uv run tests coverage` | Generate comprehensive coverage reports |
| | `uv run tests benchmark` | Run benchmark tests |
| **Database** | `uv run db init` | Initialize database with proper migrations |
| | `uv run db dev` | Development workflow: generate migration and apply it |
| | `uv run db push` | Apply all pending migrations to database |
| | `uv run db status` | Show current migration status |
| | `uv run db new "message"` | Generate new migration from model changes |
| | `uv run db health` | Check database connection health |
| | `uv run db schema` | Validate database schema matches models |
| | `uv run db queries` | Check for long-running queries |
| **Docker** | `uv run docker up` | Start Docker services with smart orchestration |
| | `uv run docker down` | Stop Docker services |
| | `uv run docker build` | Build Docker images |
| | `uv run docker logs` | Show Docker service logs |
| | `uv run docker ps` | List running Docker containers |
| | `uv run docker shell` | Open shell in container |
| | `uv run docker health` | Check container health status |
| | `uv run docker config` | Validate Docker Compose configuration |
| **Documentation** | `uv run docs serve` | Start local documentation server |
| | `uv run docs build` | Build documentation site |
| **Configuration** | `uv run config generate` | Generate example configuration files |

<sub>[back to top ↑](#table-of-contents)</sub>

## License

Tux is free and open source software licensed under the [GNU General Public License v3.0](LICENSE), founded by [@kzndotsh](https://github.com/kzndotsh), created for and maintained by the [All Things Linux](https://allthingslinux.org) community.

## Metrics

![Metrics](https://repobeats.axiom.co/api/embed/b988ba04401b7c68edf9def00f5132cd2a7f3735.svg)

## Contributors

![Contributors](https://contrib.rocks/image?repo=allthingslinux/tux)

<sub>[back to top ↑](#table-of-contents)</sub>
