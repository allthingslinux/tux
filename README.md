
<!-- markdownlint-disable MD041 -->

<div align="center">
    <p align="center">
        <a href="https://github.com/allthingslinux/tux/releases">
            <img alt="GitHub Release" src="https://img.shields.io/github/v/release/allthingslinux/tux?logo=github&logoColor=white&include_prereleases"></a>
        <a href="https://python.org">
            <img alt="Python" src="https://img.shields.io/badge/python-3.13.2+-blue?logo=python&logoColor=white"></a>
        <a href="https://docs.astral.sh/uv">
            <img alt="uv" src="https://img.shields.io/badge/uv-0.9.0+-purple?logo=uv&logoColor=white"></a>
        <a href="https://results.pre-commit.ci/latest/github/allthingslinux/tux/main">
            <img alt="pre-commit.ci status" src="https://results.pre-commit.ci/badge/github/allthingslinux/tux/main.svg"></a>
        <a href="https://codecov.io/gh/allthingslinux/tux">
            <img alt="Codecov" src="https://codecov.io/gh/allthingslinux/tux/graph/badge.svg?token=R0AUAS996W"></a>
        <a href="https://github.com/allthingslinux/tux/blob/main/LICENSE">
            <img alt="License" src="https://img.shields.io/github/license/allthingslinux/tux?logo=gnu&logoColor=white"></a>
    </p>
</div>

<img align="center" src="assets/readme-banner.png" alt="Banner">

<div align="center">
    <h1>Tux</h1>
    <p><strong>The all-in-one open source Discord bot</strong></p>
    <p>
        <a href="https://tux.atl.dev">📚 Documentation</a> •
        <a href="https://discord.gg/gpmSjcjQxg">💬 Discord</a> •
        <a href="https://github.com/allthingslinux/tux/issues/525">🗺️ Roadmap</a>
    </p>
</div>

> [!WARNING]
> **This codebase is under heavy development and subject to breaking changes.** APIs, configurations, and features may change without notice. Use at your own risk in production environments. Until v0.1.0 is released, the documentation is not guaranteed to be accurate or up to date.

---

## Quick Start

Choose your path to get started with Tux:

| Role          | Get Started                                                                                   |
|---------------|----------------------------------------------------------------------------------------------|
| 👤 Users      | [Get Started](https://tux.atl.dev/user/)                                 |
| ⚙️ Admins     | [Get Started](https://tux.atl.dev/admin/)                                |
| 🐳 Self-Hosters | [Get Started](https://tux.atl.dev/selfhost/)                        |
| 💻 Developers | [Get Started](https://tux.atl.dev/developer/)                            |

## About

Tux is a feature-rich Discord bot originally built for the [All Things Linux](https://allthingslinux.org) community. It provides moderation tools, leveling systems, snippets, utilities, and fun commands - all in one package.

**Key Features:**

- **Moderation** - Comprehensive moderation tools with case management
- **Leveling** - XP and ranking system to reward active members
- **Snippets** - Quick text responses and custom commands
- **Utilities** - Server management and utility commands
- **Fun** - Entertainment commands and interactive features
- **Plugin System** - Extensible architecture for custom functionality

## Why Tux?

- **Modern tech stack** - Type-safe, async-first, powered by Python 3.13+ and discord.py
- **Production-ready** - Battle-tested in large communities with comprehensive error handling
- **Developer-friendly** - Clean architecture, extensive docs, and active development
- **Free and open source** - Free to use, modify, and contribute under GPL-3.0

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Runtime** | Python 3.13+ with `discord.py` |
| **Package Manager** | `uv` for fast dependency management |
| **Database** | PostgreSQL with `SQLModel` (SQLAlchemy + Pydantic) |
| **Type Safety** | `basedpyright` with strict type hints |
| **Code Quality** | `ruff` for linting and formatting |
| **Testing** | `pytest` with async support |
| **CLI** | `typer` with custom command scripts |
| **Logging** | `loguru` for structured logging |
| **Monitoring** | `sentry-sdk` for error tracking |
| **HTTP Client** | `httpx` for async requests |
| **Configuration** | `pydantic-settings` with multi-format support |
| **Containers** | Docker & Docker Compose |

## Documentation

Visit **[tux.atl.dev](https://tux.atl.dev)** for complete documentation including:

- **[User Guide](https://tux.atl.dev/user/)** - Commands, features, and usage
- **[Admin Guide](https://tux.atl.dev/admin/)** - Configuration and server setup
- **[Self-Hosting](https://tux.atl.dev/selfhost/)** - Installation and deployment
- **[Developer Guide](https://tux.atl.dev/developer/)** - Architecture and contributing
- **[API Reference](https://tux.atl.dev/reference/)** - CLI tools and codebase reference
- **[FAQ](https://tux.atl.dev/faq/)** - Common questions and answers

## Support & Community

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Get help, report issues, and discuss features
- **[GitHub Issues](https://github.com/allthingslinux/tux/issues)** - Bug reports and feature requests

**Developer Resources:**

| Getting Started | Development Workflow | Quality & Standards |
|-------------------|------------------------|----------------------|
| [Developer Setup](https://tux.atl.dev/developer/tutorials/development-setup/) | [Git Best Practices](https://tux.atl.dev/developer/best-practices/git/) | [Testing Guide](https://tux.atl.dev/developer/best-practices/testing/) |
| [First Contribution](https://tux.atl.dev/developer/tutorials/first-contribution/) | [Branch Naming](https://tux.atl.dev/developer/best-practices/branch-naming/) | [Code Review](https://tux.atl.dev/developer/best-practices/code-review/) |
| [Project Structure](https://tux.atl.dev/developer/tutorials/project-structure/) | [Creating Commands](https://tux.atl.dev/developer/tutorials/creating-first-command/) | [Error Handling](https://tux.atl.dev/developer/best-practices/error-handling/) |

## Project Stats

![Metrics](https://repobeats.axiom.co/api/embed/b988ba04401b7c68edf9def00f5132cd2a7f3735.svg)

## Contributors

![Contributors](https://contrib.rocks/image?repo=allthingslinux/tux)

## License

Tux is free and open source software licensed under the [GNU General Public License v3.0](LICENSE).

Created by [@kzndotsh](https://github.com/kzndotsh) • Maintained by the [All Things Linux](https://allthingslinux.org) community
