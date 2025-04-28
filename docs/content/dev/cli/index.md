# CLI Reference

This section provides details on using the custom `tux` command-line interface, built with Click.

## Environment Selection

The `tux` CLI defaults to **development mode** for all command groups (`bot`, `db`, `dev`, `docker`). This ensures that operations like database migrations or starting the bot target your development resources unless explicitly specified otherwise.

* **Production Mode:**
    To run a command targeting production resources (e.g., production database, production bot token), you **must** use the global `--prod` flag immediately after `tux`:

    ```bash
    # Example: Apply migrations to production database
    poetry run tux --prod db migrate

    # Example: Start the bot using production token/DB
    poetry run tux --prod bot start
    ```

* **Development Mode (Default / Explicit):**
    Running any command without `--prod` automatically uses development mode. You can also explicitly use the `--dev` flag, although it is redundant.

    ```bash
    # These are equivalent and run in development mode:
    poetry run tux db push
    poetry run tux --dev db push

    poetry run tux bot start
    poetry run tux --dev bot start
    ```

This default-to-development approach prioritizes safety by preventing accidental operations on production environments. The environment determination logic can be found in `tux/utils/env.py`.

## Command Groups

*(This section can be expanded with details on each command group and sub-command, potentially referencing the [CONTRIBUTING.md](../contributing.md) for basic quality checks and database commands already covered there).* Example:

* **`bot`**: Commands related to running the bot.
  * `start`: Starts the bot (uses hot-reloading in dev mode).
* **`db`**: Commands for database management. See [Database Management](../database.md) for details.
* **`dev`**: Commands for development quality checks (lint, format, type-check). See our [contributing guide](../contributing.md) for basic usage.
* **`docker`**: Commands for managing the Docker environment. See [Docker Development](../docker_development.md) for details.

::: mkdocs-click
    :module: tux.cli
    :command: cli
    :prog_name: tux
    :depth: 1
    :list_subcommands: True
