# Local Development

This section covers running and developing Tux directly on your local machine, which is the recommended approach.

**Running the Bot:**

1. **Push Database Schema:**
    If this is your first time setting up or if you've made changes to `schema.prisma`, push the schema to your development database. This command also generates the Prisma client.

    ```bash
    # Ensure you use --dev or rely on the default development mode
    poetry run tux --dev db push
    ```

    *You can explicitly regenerate the Prisma client anytime with `poetry run tux --dev db generate`.*

2. **Start the Bot:**

    Start the bot in development mode:

    ```bash
    poetry run tux --dev start
    ```

    This command will:
    * Read `DEV_DATABASE_URL` and `DEV_BOT_TOKEN` from your `.env` file.
    * Connect to the development database.
    * Authenticate with Discord using the development token.
    * Load all cogs.
    * Start the Discord bot.
    * Enable the built-in **Hot Reloading** system.

**Hot Reloading:**

The project includes a hot-reloading utility (`tux/utils/hot_reload.py`).

When the bot is running locally via `poetry run tux --dev start`, this utility watches for changes in the `tux/cogs/` directory. It attempts to automatically reload modified cogs or cogs affected by changes in watched utility files without requiring a full bot restart.

This significantly speeds up development for cog-related changes. Note that changes outside the watched directories (e.g., core bot logic, dependencies) may still require a manual restart (`Ctrl+C` and run the start command again).
