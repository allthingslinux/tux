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
**This bot (without plenty of tweaking) is not ready for production use, we suggest against using it until announced. Join our support server: [atl.dev](https://discord.gg/gpmSjcjQxg) for more info!**

## About

Tux is an all in one Discord bot for the All Things Linux Discord server.

It is designed to provide a variety of features to the server, including moderation, support, utility, and various fun commands.

## Tech Stack

- Python 3.12 alongside the Discord.py library
- Poetry for dependency management
- Docker and Docker Compose for development and deployment
- Strict typing with Pyright and type hints
- Type safe ORM using Prisma
- PostgreSQL database with Supabase
- Linting and formatting via Ruff and Pre-commit
- Justfile for easy CLI commands
- Beautiful logging with Loguru
- Exception handling with Sentry
- Request handling with HTTPX

## Bot Features

- Asynchronous codebase
- Hybrid command system with both slash commands and traditional commands
- Cog loading system with hot reloading
- Branded embeds and messages
- Robust error handling
- Activity rotation
- Custom help command
- Configuration system
- Dynamic role-based (access level) permission system

## Installation

### Prerequisites

- Python 3.12
- [Poetry](https://python-poetry.org/docs/)
- [Supabase](https://supabase.io/)
- Optional: [Docker](https://docs.docker.com/get-docker/)
- Optional: [Docker Compose](https://docs.docker.com/compose/install/)
- Optional: [Just](https://github.com/casey/just/)

### Steps to Install

Assuming you have the prerequisites installed, follow these steps to get started with the development of the project:

Further detailed instructions can be found in the [development guide](docs/development.md).

1. Clone the repository

   ```bash
   git clone https://github.com/allthingslinux/tux && cd tux
   ```

2. Install the project's dependencies

    ```bash
    poetry install
    ```

3. Activate the virtual environment

    ```bash
    poetry shell
    ```

4. Install the pre-commit hooks

    ```bash
    pre-commit install
    ```

5. Generate the prisma client

    ```bash
    prisma generate
    ```

    Currently, you will need to have a Supabase database set up and the URL set in the `DATABASE_URL` environment variable.

    In the future, we will provide a way to use a local database. We can provide a dev database on request.

6. Copy the `.env.example` file to `.env` and fill in the required values.

    ```bash
    cp .env.example .env
    ```

    You'll need to fill in your Discord bot token here, as well as the Sentry DSN if you want to use Sentry for error tracking.

    We offer dev tokens on request in our Discord server.

7. Copy the `config/settings.yml.example` file to `config/settings.yml` and fill in the required values.

    ```bash
    cp config/settings.yml.example config/settings.yml
    ```

    Be sure to add your Discord user ID to the `BOT_OWNER` key in the settings file.

    You can also add your custom prefix here.

8. Start the bot!

    ```bash
    poetry run python tux/main.py
    ```

9. Run the sync command in the server to sync the slash command tree.

   ```bash
   {prefix}dev sync <server id>
   ```

## Development Notes

> [!NOTE]
Make sure to add your discord ID to the sys admin list if you are testing locally.

> [!NOTE]
Make sure to set the prisma schema database ENV variable to the DEV database URL.

## License

This project is licensed under the terms of the The GNU General Public License v3.0.

See [LICENSE](LICENSE.md) for details.

## Metrics

![Alt](https://repobeats.axiom.co/api/embed/b988ba04401b7c68edf9def00f5132cd2a7f3735.svg "Repobeats analytics image")

## Lines of Code

<!-- LOC-REPORT -->
