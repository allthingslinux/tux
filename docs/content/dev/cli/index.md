# CLI Reference

This section provides details on using the custom `tux` command-line interface, built with Click.

## Environment Selection

The `tux` CLI defaults to **development mode** for all command groups (`db`, `dev`, `docker`). This ensures that operations like database migrations or starting the bot target your development resources unless explicitly specified otherwise.

* **Production Mode:**
    To run a command targeting production resources (e.g., production database, production bot token), you **must** use the global `--prod` flag immediately after `tux`:

    ```bash
    # Example: Apply migrations to production database
    poetry run tux db migrate --prod

    # Example: Start the bot using production token/DB
    poetry run tux start --prod
    ```

* **Development Mode (Default / Explicit):**
    Running any command without `--prod` automatically uses development mode. You can also explicitly use the `--dev` flag, although it is redundant.

    ```bash
    # These are equivalent and run in development mode:
    poetry run tux db push
    poetry run tux db push --dev

    poetry run tux start
    poetry run tux start --dev
    ```

This default-to-development approach prioritizes safety by preventing accidental operations on production environments. The environment determination logic can be found in `tux/utils/env.py`.

::: mkdocs-click
    :module: tux.cli
    :command: cli
    :prog_name: tux
    :depth: 0
    :style: table
    :list_subcommands: True
