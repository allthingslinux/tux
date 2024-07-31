<div align="center">
    <img src="docs/resources/tux.gif" width=128 height=128></img>
    <h1>Tux</h1>
    <h3><b>A Discord bot for the All Things Linux Discord server</b></h3>
</div>

<div align="center">
    <p align="center">
        <a href="https://github.com/allthingslinux/tux/forks">
            <img alt="Forks" src="https://img.shields.io/github/commit-activity/m/allthingslinux/tux?style=for-the-badge&logo=git&color=EBA0AC&logoColor=EBA0AC&labelColor=302D41"></a>
        <a href="https://github.com/allthingslinux/tux">
            <img alt="Repo size" src="https://img.shields.io/github/repo-size/allthingslinux/tux?style=for-the-badge&logo=github&color=FAB387&logoColor=FAB387&labelColor=302D41"/></a>
        <a href="https://github.com/allthingslinux/tux/issues">
            <img alt="Issues" src="https://img.shields.io/github/issues/allthingslinux/tux?style=for-the-badge&logo=githubactions&color=F9E2AF&logoColor=F9E2AF&labelColor=302D41"></a>
        <a href="https://www.gnu.org/licenses/gpl-3.0.html">
            <img alt="License" src="https://img.shields.io/github/license/allthingslinux/tux?style=for-the-badge&logo=gitbook&color=A6E3A1&logoColor=A6E3A1&labelColor=302D41"></a>
        <a href="https://discord.gg/linux">
            <img alt="Discord" src="https://img.shields.io/discord/1172245377395728464?style=for-the-badge&logo=discord&color=B4BEFE&logoColor=B4BEFE&labelColor=302D41"></a>
    </p>
</div>

# NOTE: This bot (without plenty of tweaking) is not ready for multi-server use, we recommend against using it until it is more complete

## About

Tux is a Discord bot for the All Things Linux Discord server. It is designed to provide a variety of features to the server, including moderation, support, utility, and various fun commands. The bot is written in Python using the discord.py library.


## Tech Stack
- Poetry for dependency management
- Docker and Docker Compose for development and deployment
- Strict typing with Pyright and type hints
- Type safe ORM using Prisma
- PostgreSQL database with Supabase
- Linting and formatting via Ruff and Pre-commit
- Justfile for easy CLI commands
- Beautiful logging with Loguru
- Exception handling with Sentry

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
- Optional: [Docker](https://docs.docker.com/get-docker/) if you want to run the bot in a container.
- Optional: [Docker Compose](https://docs.docker.com/compose/install/) if you want to define the container environment in a `docker-compose.yml` file.
- Optional: [Just](https://github.com/casey/just/) if you want to use the Justfile for easy CLI commands.

### Steps
1. Clone the repository
   
   ```bash
   git clone https://github.com/allthingslinux/tux && cd tux
   ```

2. Install the dependencies
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

6. Copy the `.env.example` file to `.env` and fill in the required values
    ```bash
    cp .env.example .env
    ```

7. Copy the `config/settings.json.example` file to `config/settings.json` and fill in the required values
    ```bash
    cp config/settings.json.example config/settings.json
    ```

8. Run the bot
    ```bash
    poetry run python tux/main.py
    ```

9. Run the sync command in the server to sync the slash command tree.
   ```
   {prefix}dev sync <server id>
   ```

## Development Notes
- Make sure to add your discord ID to the sys admin list if you are testing locally.
- Make sure to set the prisma schema database ENV variable to the DEV database URL.

## License
This project is licensed under the terms of the The GNU General Public License v3.0. See the [LICENSE](LICENSE.md) file for details.
