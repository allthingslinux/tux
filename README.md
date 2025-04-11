# Tux

## A Discord bot for the All Things Linux Discord server

<div align="center">
    <p align="center">
        <a href="https://github.com/allthingslinux/tux/forks">
            <img alt="Forks" src="https://img.shields.io/github/commit-activity/m/allthingslinux/tux?style=for-the-badge&logo=git&color=EBA0AC&logoColor=EBA0AC&labelColor=302D41"></a>
        <a href="https://github.com/allthingslinux/tux">
            <img alt="Repo size" src="https://img.shields.io/github/repo-size/allthingslinux/tux?style=for-the-badge&logo=github&color=FAB387&logoColor=FAB387&labelColor=302D41"/></a>
        <a href="https://github.com/allthingslinux/tux/issues">
            <img alt="Issues" src="https://img.shields.io/github/issues/allthingslinux/tux?style=for-the-badge&logo=githubactions&color=F9E2AF&logoColor=F9E2AF&labelColor=302D41"></a>
        <a href="https://discord.gg/linux">
            <img alt="Discord" src="https://img.shields.io/discord/1172245377395728464?style=for-the-badge&logo=discord&color=B4BEFE&logoColor=B4BEFE&labelColor=302D41"></a>
    </p>
</div>

> [!WARNING]
**This bot is still a work in progress and issues are expected. If you self-host our bot please join our support server [here](https://discord.gg/gpmSjcjQxg) for announcements and support.**

## About

Tux is an all-in-one Discord bot originally designed for the All Things Linux Discord server.

It is designed to provide a variety of features to the server, including moderation, support, utility, and various fun commands.

## Tech Stack

- Python 3.13+ alongside the `discord.py` library
- Poetry for dependency management
- Docker and Docker Compose for optional containerized environments
- Strict typing with `pyright` and type hints
- Type safe ORM using `prisma`
- Linting and formatting via `ruff`
- Custom CLI via `click` and `poetry` scripts
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
- Configuration system (`config/settings.yml.example`)
- Dynamic role-based (access level) permission system

## Installation and Development

### Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/docs/)
- A PostgreSQL database (e.g. via [Supabase](https://supabase.io/) or local installation)
- Optional: [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)

### Setup & Workflow

1. **Clone the repository:**

    ```bash
    git clone https://github.com/allthingslinux/tux && cd tux
    ```

2. **Follow the Developer Guide:**

    For detailed instructions on setting up:
    - your environment (local or Docker)
    - installing dependencies
    - configuring `.env` and `settings.yml`
    - managing the database
    - running the bot
    - using hot-reloading
    - linting/formatting
    - understanding the `tux` CLI commands

   ### Please refer to the **[DEVELOPER.md](DEVELOPER.md)** guide

   Any documentation found in the `docs` directory is currently outdated and will be updated soon.

## License

This project is licensed under the GNU General Public License v3.0.

See [LICENSE](LICENSE.md) for details.

## Metrics

<sub>Made with [Repobeats](https://repobeats.axiom.co).</sub>

![Metrics](https://repobeats.axiom.co/api/embed/b988ba04401b7c68edf9def00f5132cd2a7f3735.svg)

## Contributors

<sub>Made with [contrib.rocks](https://contrib.rocks).</sub>

[![Contributors](https://contrib.rocks/image?repo=allthingslinux/tux)](https://github.com/allthingslinux/tux/graphs/contributors)
