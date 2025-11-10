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

### Core Architecture

- **Asynchronous Design**: Fully async codebase for high-performance Discord operations
- **Hybrid Commands**: Support for both modern slash commands and traditional prefix commands
- **Automatic Cog Loading**: Intelligent module discovery and loading system with eligibility checks
- **Hot Reload**: File watching system for automatic cog reloading during development

### Advanced Features

- **Dynamic Permission System**: Database-driven permissions with configurable ranks (0-10)
- **Comprehensive Error Handling**: Centralized error handling with Sentry integration
- **Activity Rotation**: Dynamic status messages with bot statistics placeholders
- **Custom Help System**: Paginated help embeds with command navigation and subcommand display
- **Configuration Management**: Interactive setup wizard for guild onboarding and permission ranks

### User Experience

- **Branded Embeds**: Consistent visual design across all bot responses
- **Rich Information Commands**: Support for Discord entities (members, channels, roles, emojis)
- **Server Statistics**: Member count displays with human/bot breakdowns
- **Interactive Components**: Buttons, modals, and views for enhanced user interaction

### Extensibility

- **Modular Plugin System**: Hot-reloadable extensions without core modifications
- **Multi-format Configuration**: Support for TOML, YAML, JSON, and environment variables
- **Event-Driven Architecture**: Comprehensive event handling for Discord gateway events

<sub>[back to top ↑](#table-of-contents)</sub>

## Plugin System

Tux features a modular plugin architecture that allows extending functionality without modifying core code:

### Architecture

- **Hot-Reloadable**: Plugins can be loaded/unloaded during development without restarting
- **Isolated Error Handling**: Plugin failures don't affect core bot functionality
- **Database Integration**: Plugins can access the bot's database through controllers
- **Configuration Management**: Plugin-specific settings through the main config system
- **Event System**: Plugins can hook into Discord events and bot lifecycle events

### Plugin Development

Plugins are located in `src/tux/plugins/` and follow a simple structure:

- Automatic discovery and loading
- Access to all bot services and utilities
- Type-safe database operations
- Rich embed and component support

<sub>[back to top ↑](#table-of-contents)</sub>

## Database Features

### Type-Safe Operations

Tux uses **SQLModel** for type-safe database operations with full Pydantic integration:

- **Type Safety**: Compile-time type checking for all database operations
- **Async Operations**: Full async/await support for high-performance queries
- **Automatic Serialization**: Convert database models to/from JSON automatically
- **Relationship Management**: Type-safe foreign key relationships and joins

### Advanced Architecture

- **Controller Pattern**: Clean separation between business logic and data access
- **Migration System**: Alembic-powered schema management with version control
- **Connection Pooling**: Optimized PostgreSQL connection management with asyncpg
- **Transaction Safety**: Automatic transaction handling with rollback on errors

### Specialized Controllers

- **BaseController**: CRUD operations with type safety and relationship loading
- **Bulk Operations**: Efficient batch inserts, updates, and deletes
- **Pagination**: Cursor-based pagination with metadata
- **Upsert Operations**: Get-or-create patterns for data synchronization
- **Query Optimization**: Advanced filtering, sorting, and indexing

### Supported Databases

- **Primary**: PostgreSQL 17+ with asyncpg driver
- **Testing**: In-memory SQLite via py-pglite for fast test execution
- **Backup**: psycopg driver support for compatibility

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

Tux provides comprehensive documentation for all user types and use cases:

### Documentation

- **[Full Documentation Site](https://tux.atl.dev)** - Complete online documentation
- **[Getting Started Guide](https://tux.atl.dev/getting-started/)** - Setup instructions for all user types
- **[API Reference](https://tux.atl.dev/reference/)** - Complete codebase documentation
- **[CLI Reference](https://tux.atl.dev/reference/cli)** - Command-line interface documentation

### User Guides

- **[For Users](https://tux.atl.dev/getting-started/for-users/)** - Bot commands and features
- **[For Administrators](https://tux.atl.dev/getting-started/for-admins/)** - Server setup and management
- **[For Developers](https://tux.atl.dev/getting-started/for-developers/)** - Development environment setup
- **[For Self-Hosters](https://tux.atl.dev/getting-started/for-self-hosters/)** - Deployment and hosting

### Developer Resources

- **[Architecture Overview](https://tux.atl.dev/developer/concepts/)** - System design and components
- **[Contributing Guide](https://tux.atl.dev/developer/contributing/)** - Development workflow and standards
- **[Plugin Development](https://tux.atl.dev/developer/guides/)** - Creating custom extensions
- **[Database Operations](https://tux.atl.dev/developer/guides/database-operations/)** - Database integration guide

### Self-Hosting

- **[Docker Installation](https://tux.atl.dev/selfhost/install/docker/)** - Container deployment
- **[Configuration Guide](https://tux.atl.dev/selfhost/config/)** - Multi-format config setup
- **[Database Setup](https://tux.atl.dev/selfhost/config/database/)** - PostgreSQL configuration
- **[Operations Guide](https://tux.atl.dev/selfhost/manage/)** - Maintenance and monitoring

### Support & Community

- **[Discord Community](https://discord.gg/gpmSjcjQxg)** - Live support and discussions
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Bug reports and feature requests
- **[Roadmap](https://github.com/allthingslinux/tux/issues/525)** - Planned features and milestones
- **[Dependencies](https://github.com/allthingslinux/tux/issues/157)** - Third-party integrations

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

Tux is free and open source software licensed under the [GNU General Public License v3.0](LICENSE), created by [@kzndotsh](https://github.com/kzndotsh), created for the and maintained by the [All Things Linux](https://allthingslinux.org) community.

## Metrics

![Metrics](https://repobeats.axiom.co/api/embed/b988ba04401b7c68edf9def00f5132cd2a7f3735.svg)

## Contributors

![Contributors](https://contrib.rocks/image?repo=allthingslinux/tux)

<sub>[back to top ↑](#table-of-contents)</sub>
