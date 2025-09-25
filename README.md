<h1 align="center">Tux</h1>
<h3 align="center">A Discord bot for the All Things Linux Discord server</h3>

<div align="center">
    <p align="center">
        <a href="https://github.com/allthingslinux/tux/actions">
            <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/allthingslinux/tux/ci.yml?branch=main&label=CI"></a>
        <a href="https://results.pre-commit.ci/latest/github/allthingslinux/tux/main">
            <img alt="pre-commit.ci status" src="https://results.pre-commit.ci/badge/github/allthingslinux/tux/main.svg"></a>
        <a href="https://codecov.io/gh/allthingslinux/tux">
            <img alt="Codecov" src="https://codecov.io/gh/allthingslinux/tux/graph/badge.svg?token=R0AUAS996W"></a>
        <a href="https://github.com/allthingslinux/tux/commits/main">
            <img alt="Commit Activity" src="https://img.shields.io/github/commit-activity/m/allthingslinux/tux"></a>
        <a href="https://github.com/allthingslinux/tux/releases">
            <img alt="GitHub Release" src="https://img.shields.io/github/v/release/allthingslinux/tux"></a>
        <a href="https://github.com/allthingslinux/tux/stargazers">
            <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/allthingslinux/tux"></a>
        <a href="https://github.com/allthingslinux/tux/network/members">
            <img alt="GitHub forks" src="https://img.shields.io/github/forks/allthingslinux/tux"></a>
        <a href="https://github.com/allthingslinux/tux/graphs/contributors">
            <img alt="GitHub contributors" src="https://img.shields.io/github/contributors/allthingslinux/tux"></a>
        <a href="https://github.com/allthingslinux/tux/issues">
            <img alt="Issues" src="https://img.shields.io/github/issues/allthingslinux/tux"></a>
        <a href="https://github.com/allthingslinux/tux">
            <img alt="Repo size" src="https://img.shields.io/github/repo-size/allthingslinux/tux"></a>
        <a href="https://python.org">
            <img alt="Python" src="https://img.shields.io/badge/python-3.13+-blue.svg"></a>
        <a href="https://docs.astral.sh/uv">
            <img alt="Uv" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json"></a>
        <a href="https://github.com/allthingslinux/tux/blob/main/LICENSE">
            <img alt="License" src="https://img.shields.io/github/license/allthingslinux/tux"></a>
        <a href="https://discord.gg/linux">
            <img alt="Discord" src="https://img.shields.io/discord/1172245377395728464?logo=discord"></a>
    </p>
</div>

> [!WARNING]
**This bot is still a work in progress and issues are expected. If you self-host our bot please join our support server [on Discord](https://discord.gg/gpmSjcjQxg) for announcements and support.**

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About](#about)
- [Tech Stack](#tech-stack)
- [Bot Features](#bot-features)
- [Installation and Development](#installation-and-development)
  - [Prerequisites](#prerequisites)
  - [Setup \& Workflow](#setup--workflow)
  - [Quick Commands](#quick-commands)
- [License](#license)
- [Metrics](#metrics)
- [Contributors](#contributors)

## About

Tux is an all-in-one Discord bot originally designed for the All Things Linux Discord server.

It is designed to provide a variety of features to the server, including moderation, support, utility, and various fun commands.

## Tech Stack

- Python 3.13+ alongside the `discord.py` library
- Uv for dependency management
- Docker and Docker Compose for optional containerized environments
- Strict typing with `basedpyright` and type hints
- Type safe ORM using `SQLModel` with `SQLAlchemy`
- Linting and formatting via `ruff`
- Custom CLI via `typer` and `uv` scripts
- Rich logging with `loguru`
- Exception handling with `sentry-sdk`
- Request handling with `httpx`
- Custom dynamic environment management with `python-dotenv`

## Bot Features

- Asynchronous codebase
- Hybrid command system with both slash commands and traditional commands
- Automatic cog loading system
- Hot-reloading for local development changes
- Branded embeds and messages
- Robust error handling
- Activity rotation
- Custom help command
- Configuration system (environment variables + `.env` file)
- Dynamic role-based (access level) permission system
- Plugin system (see [plugins](src/tux/plugins/README.md))

## Installation and Development

### Prerequisites

- Python 3.13+
- [Uv](https://docs.astral.sh/uv/)
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
   cp env.example .env
   # Edit .env with your bot tokens and database URLs
   ```

4. **Start the bot:**

   ```bash
   # Start the bot (auto-detects environment, defaults to development)
   uv run tux start

   # Start with debug mode
   uv run tux start --debug
   ```

### Quick Commands

```bash
# Development
uv run tux start                # Start bot in development mode
uv run tux start --debug        # Start bot with debug mode
uv run dev lint                 # Check code quality with Ruff
uv run dev format               # Format code with Ruff
uv run dev type-check           # Check types with basedpyright
uv run dev pre-commit           # Run pre-commit checks
uv run dev all                  # Run all development checks

# Testing
uv run test run                 # Run tests with coverage
uv run test quick               # Run tests without coverage (faster)
uv run test html                # Run tests and generate HTML report
uv run test coverage            # Generate coverage reports

# Database
uv run db migrate-dev           # Create and apply migrations for development
uv run db migrate-push          # Push pending migrations to database
uv run db migrate-generate "message"  # Generate a new migration
uv run db health                # Check database health

# Docker
uv run docker up                # Start Docker services
uv run docker down              # Stop Docker services
uv run docker build             # Build Docker images
uv run docker logs              # Show Docker service logs
uv run docker ps                # List running containers
uv run docker shell             # Open shell in container
```

**For detailed setup instructions, see [SETUP.md](SETUP.md)**

**For developer information, see [DEVELOPER.md](DEVELOPER.md)**

**For configuration documentation, see [CONFIG.md](CONFIG.md)**

## License

This project is licensed under the GNU General Public License v3.0.

See [LICENSE](LICENSE) for details.

## Metrics

<sub>Made with [Repobeats](https://repobeats.axiom.co).</sub>

![Metrics](https://repobeats.axiom.co/api/embed/b988ba04401b7c68edf9def00f5132cd2a7f3735.svg)

## Contributors

<sub>Made with [contrib.rocks](https://contrib.rocks).</sub>

[![Contributors](https://contrib.rocks/image?repo=allthingslinux/tux)](https://github.com/allthingslinux/tux/graphs/contributors)
