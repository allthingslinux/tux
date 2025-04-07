# Developer Guide: Tux

Welcome to the Tux developer guide! This guide provides instructions for setting up your development environment and contributing to the project. You can develop either directly on your local machine (recommended) or using an optional Docker-based environment.

## Prerequisites

Before you begin, ensure you have the following installed:

* **Git:** For version control.
* **Python:** Version 3.11+ recommended.
* **Poetry:** For Python dependency management (version 1.2+ recommended).
* **(Optional) Docker:** Only required if you prefer a containerized development environment (includes Docker Compose V2).

## Getting Started

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/allthingslinux/tux && cd tux
    ```

2. **Install Dependencies:**

    Use Poetry to set up a virtual environment and install all project dependencies, including development tools:

    Activates or creates a new virtualenv for the current project:

    ```bash
    poetry env use 3.13.2
    ```

    Install all project dependencies:

    ```bash
    poetry install
    ```

    Install the `pre-commit` hooks:

    ```bash
    poetry run pre-commit install
    ```

3. **Configure the `.env` file:**
    Copy the example environment file and fill in the necessary values:

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file and fill out the required variables. The `.env` file is used for both local and Docker development.

    At a minimum, you will need to fill in the `DEV_BOT_TOKEN` and `DEV_DATABASE_URL` variables for local development when using the CLI to start the bot with `poetry run tux --dev bot start`.

    ```bash
    DEV_BOT_TOKEN=your_dev_discord_token
    PROD_BOT_TOKEN=your_prod_discord_token

    DEV_DATABASE_URL=postgresql://username:password@localhost:5432/database_name
    PROD_DATABASE_URL=postgresql://username:password@localhost:5432/database_name
    ```

    **Do not commit the `.env` file.**

4. **Configure the `config/settings.yml` file:**
    Configure the `config/settings.yml` file to your liking.

    ```bash
    cp config/settings.yml.example config/settings.yml
    ```

    This file is used to configure the bot's settings and provides a way to override the default settings.

   ### Make sure to add your discord ID to the bot owner list

## Local Development (Recommended)

This is the simplest and recommended way to get started and develop Tux.

**Running the Bot:**

1. **Push Database Schema:**
    For the first time, you will need to push the database schema to the development database:

    This will also generate the Prisma client if it is not already generated, you can re-generate the client by running `poetry run tux --dev db generate` as needed.

    ```bash
    poetry run tux --dev db push
    ```

2. **Start the Bot:**

    Start the bot in development mode:

    ```bash
    poetry run tux --dev bot start
    ```

    This command will:
    * Parse the `.env` file for the `DEV_DATABASE_URL` and `DEV_BOT_TOKEN` variables.
    * Map the `DEV_DATABASE_URL` to the `DATABASE_URL` in the Prisma client.
    * Use the `DEV_BOT_TOKEN` to authenticate with Discord.
    * Load all cogs.
    * Start the Discord bot.
    * Enable the built-in **Hot Reloading** system.

**Hot Reloading:**

The project includes a hot-reloading utility (`tux/utils/hot_reload.py`).

When the bot is running locally via `poetry run tux --dev bot start`, this utility watches for changes in the `tux/cogs/` directory and attempts to automatically reload modified or affected cogs without requiring a full bot restart.

This significantly speeds up development for cog-related changes. Note that changes outside the `tux/cogs/` directory (e.g., utility files, core bot logic) may still require a manual restart (`Ctrl+C` and run the start command again).

**Database Management (Local):**

Perform database tasks directly using the `tux` CLI. It will connect to your development database as specified in `.env`. Ensure you use `--dev` or rely on the default behavior.

* **Generate Prisma Client:**

    ```bash
    poetry run tux --dev db generate
    ```

* **Apply Schema Changes (Dev):** Pushes schema changes directly without creating migration files. Suitable for development.

    ```bash
    poetry run tux --dev db push
    ```

* **Create Migrations:** Creates SQL migration files based on schema changes.

    ```bash
    # Use --dev for the development database
    poetry run tux --dev db migrate --name <migration-name>
    ```

* **Apply Migrations:** Runs pending migrations.

    ```bash
    poetry run tux --dev db migrate
    ```

* **Pull Schema:** Introspects the database and updates `schema.prisma`.

    ```bash
    poetry run tux --dev db pull
    ```

* **Reset Database:** **(Destructive!)** Drops and recreates the database.

    ```bash
    poetry run tux --dev db reset
    ```

**Linting, Formatting, Type Checking (Local):**

Run these checks directly on your host machine using the `dev` command group. No environment flag is needed as this will run all checks in the development environment.

* **Lint:**

    This will lint the project using Ruff.

    ```bash
    poetry run tux dev lint
    ```

* **Lint Fix:**

    This will lint the project using Ruff and fix linting errors.

    ```bash
    poetry run tux dev lint-fix
    ```

* **Format:**

    This will format the project using Ruff.

    ```bash
    poetry run tux dev format
    ```

* **Type Check:**

    This will type check the project using Pyright.

    ```bash
    poetry run tux dev type-check
    ```

* **Run all checks:**

    This will run all pre-commit hooks.

    ```bash
    poetry run tux dev pre-commit
    ```

## Docker-based Development (Optional)

This method provides a containerized environment, useful for ensuring consistency or isolating dependencies, but it bypasses the built-in hot-reloading mechanism in favor of Docker's file synchronization which can sometimes be a bit flaky.

**Docker Setup Overview:**

* `docker-compose.yml`: Defines the base configuration, primarily used for production.
* `docker-compose.dev.yml`: Contains overrides specifically for local development. It uses the `dev` Dockerfile stage, enables file watching via `develop: watch:`, and runs the container as `root` for sync compatibility.
* `Dockerfile`: A multi-stage Dockerfile defines the build process (see file for details).

**Starting the Docker Environment:**

1. **Build Images (First time or after Dockerfile changes):**

    ```bash
    poetry run tux --dev docker build
    ```

2. **Run Services:**

    ```bash
    # Use the global --dev flag for the tux command itself
    poetry run tux --dev docker up

    # Use --build option for the 'up' command to rebuild images first
    poetry run tux --dev docker up --build
    ```

    This uses Docker Compose with the development overrides. The `develop: watch:` feature syncs code changes into the container. The container runs `python -m tux --dev bot start`.

**Stopping the Docker Environment:**

```bash
poetry run tux --dev docker down
```

**Interacting with Docker Environment:**

* **Logs:**

    ```bash
    poetry run tux --dev docker logs -f
    ```

* **Shell inside container:**

    ```bash
    poetry run tux --dev docker exec app bash
    ```

* **Database Commands (via Docker):** Remember to execute *inside* the container.

    ```bash
    # Example: Push schema changes
    poetry run tux --dev docker exec app poetry run tux --dev db push

    # Example: Create migration
    poetry run tux --dev docker exec app poetry run tux --dev db migrate --name <migration-name>
    ```

* **Linting/Formatting/Type Checking (via Docker):**

    ```bash
    poetry run tux --dev docker exec app poetry run tux dev lint
    poetry run tux --dev docker exec app poetry run tux dev format
    # etc.
    ```

## General Information

**Environment Selection:**

The `tux` CLI now defaults to **development mode** for all commands. This ensures that operations like database migrations or starting the bot target your development resources unless explicitly told otherwise.

* **Production Mode:** To run a command in production mode (e.g., for deployment scripts or connecting to the production database), you **must** use the global `--prod` flag immediately after `tux`:

    ```bash
    poetry run tux --prod <command-group> <sub-command>
    ```

* **Development Mode (Default):** Running any command without the `--prod` flag will automatically use development mode.

    ```bash
    poetry run tux <command-group> <sub-command> # Runs in development mode
    ```

* **`--dev` Flag:** The `--dev` flag is still accepted (`poetry run tux --dev ...`) but behaves the same as the default (no flag) execution.

This approach prioritizes safety by preventing accidental operations on production environments. The environment determination logic resides in `tux/utils/env.py`.
