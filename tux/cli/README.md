# Tux CLI System

This directory contains the main components of the Tux Discord bot's command-line interface (CLI). The CLI is built using `click`.

## CLI Organization

The CLI system is structured as follows:

- `cli/`: Contains the top-level CLI definitions and command group modules.
  - `core.py`: Core CLI functionality (main `cli` group, `command_registration_decorator`, `create_group`, UI integration).
  - `ui.py`: Terminal UI utilities using `rich` for formatted output.
  - Command group modules (e.g., `bot.py`, `database.py`, `dev.py`, `docker.py`, `docs.py`): Define command groups and register individual commands using the `command_registration_decorator`.
- `cli/impl/`: Contains the actual implementation logic for the commands, keeping the definition files clean.
  - `core.py`: Core utilities potentially shared by implementations.
  - Implementation modules (e.g., `database.py`, `dev.py`, `docker.py`): House the functions that perform the actions for each command.

## Command Structure Example

The CLI uses command groups for organization. A simplified view:

```bash
tux                       # Main entry point (defined in cli/core.py)
├── --dev / --prod        # Global environment flags
├── bot                   # Bot commands (defined in cli/bot.py)
│   └── start             # Starts the bot
├── db                    # Database commands (defined in cli/database.py)
│   ├── generate          # Generate Prisma client
│   ├── migrate           # Run migrations
│   ├── pull              # Pull schema
│   ├── push              # Push schema changes
│   └── reset             # Reset database
├── dev                   # Development tools (defined in cli/dev.py)
│   ├── lint              # Run linters
│   ├── lint-fix          # Fix linting issues
│   ├── format            # Format code
│   ├── type-check        # Check types
│   └── pre-commit        # Run pre-commit checks
├── docker                # Docker commands (defined in cli/docker.py)
│   ├── build             # Build Docker image
│   ├── up                # Start Docker services
│   ├── down              # Stop Docker services
│   ├── logs              # View service logs
│   ├── ps                # List service containers
│   └── exec              # Execute command in service
└── docs                  # Documentation tools (defined in cli/docs.py)
    ├── build             # Build documentation
    └── serve             # Serve documentation
```

## Using the CLI

The CLI is intended to be run via Poetry from the project root:

```bash
poetry run tux [GLOBAL OPTIONS] [GROUP] [COMMAND] [ARGS...]
```

**Examples:**

```bash
# Start the bot (defaults to development mode)
poetry run tux bot start

# Explicitly start in production mode
poetry run tux --prod bot start

# Lint the code (defaults to development mode)
poetry run tux dev lint

# Push database changes (defaults to development mode)
poetry run tux db push

# Push database changes using the production database URL
poetry run tux --prod db push

# Run docker compose up using development settings
poetry run tux --dev docker up --build
```

## Environment Handling

Environment mode (`development` or `production`) is determined globally when the `tux` command starts:

- If `--prod` is passed (e.g., `tux --prod ...`), the mode is set to `production`.
- Otherwise (no flag or `--dev` passed), the mode defaults to `development`.

This ensures the entire command execution uses the correct context (e.g., database URL). The core logic resides in `tux/utils/env.py`. The `command_registration_decorator` in `cli/core.py` handles displaying the current mode and basic UI.

## Adding New Commands

1. **Implement the Logic:** Write the function that performs the command's action in an appropriate module within `cli/impl/`.

    ```python
    # In cli/impl/example.py
    def do_cool_thing(param1: str) -> int:
        print(f"Doing cool thing with {param1}")
        # Return 0 on success, non-zero on failure
        return 0
    ```

2. **Define the Command:** In the relevant command group module (e.g., `cli/custom.py` if you create a new group, or an existing one like `cli/dev.py`), define a Click command function and use the `command_registration_decorator`.

    ```python
    # In cli/custom.py (or another group file)
    import click
    from tux.cli.core import create_group, command_registration_decorator

    # Create or get the target group
    # custom_group = create_group("custom", "Custom commands")
    from tux.cli.dev import dev_group # Example: Adding to dev group

    @command_registration_decorator(dev_group) # Pass the target group
    @click.argument("param1") # Define any Click options/arguments
    def cool_thing(param1: str) -> int:
        """Does a cool thing."""
        from tux.cli.impl.example import do_cool_thing
        # The decorator handles calling do_cool_thing
        # with parameters parsed by Click.
        # Just return the result from the implementation.
        return do_cool_thing(param1=param1)
    ```

3. **Register the Module (if new):** If you created a new command group file (e.g., `cli/custom.py`), ensure it's imported in `cli/core.py`'s `register_commands` function so Click discovers it.
