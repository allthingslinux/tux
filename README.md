# Tux

## About
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec euismod, nisl eget ultricies ultricies, nunc nisl ultricies nunc, quis aliquam nisl nunc eu nisl. Donec euismod, nisl eget ultricies ultricies, nunc nisl ultricies nunc, quis aliquam nisl nunc eu nisl. Donec euismod, nisl eget ultricies ultricies, nunc nisl ultricies nunc, quis aliquam nisl nunc eu nisl. Donec euismod, nisl eget ultricies ultricies, nunc nisl ultricies nunc, quis aliquam nisl nunc eu nisl. Donec euismod, nisl eget ultricies ultricies, nunc nisl ultricies nunc, quis aliquam nisl nunc eu nisl.

### Requirements
- Python 3.11
- Poetry
- Docker (optional)

## Development Setup
- Clone the repository
- Install dependencies with `poetry install`
- Create a `.env` file based on the `.env.example` file
- Run the application with `poetry run python tux/main.py`

## Docker Setup
- Clone the repository
- Create a `.env` file based on the `.env.example` file
- Run `docker-compose up`

## Testing
- Run `poetry run pytest` to run all tests
- Run `poetry run pytest tests/<test_file>` to run a specific test file

## Linting
- Run `poetry run pre-commit run --all-files` to run all pre-commit hooks
- Run `poetry run pre-commit run <hook_id>` to run a specific pre-commit hook

## Architecture
Tux is built using the [discord.py]() library. It is a Python wrapper for the Discord API. The application is built using the [Command Pattern](https://en.wikipedia.org/wiki/Command_pattern) and [Event Driven Architecture](https://en.wikipedia.org/wiki/Event-driven_architecture). The application is split into two main parts: commands and events. Commands are used to execute actions in the application, while events are used to react to actions in the application. The application is also split into modules, which are used to group related commands and events together. The application is also split into cogs, which are used to group related modules together. The application is also split into utils, which are used to group related utility functions together.

## Key Files
- [main.py](tux/main.py): The main execution file for the application
- [cog_loader.py](tux/cog_loader.py): The file for loading cogs/modules (commands, events, utils)
- [permissions.py](tux/utils/permissions.py): The file for managing user permissions
- [tux_logger.py](tux/utils/tux_logger.py): The application's logger file

## Project Structure

```
tux/
├─ .git/                                   # Git source repository
├─ .venv/                                  # Python virtual environment
├─ config/                                 # Configuration files directory
│  ├─ settings.ini                         # App configuration settings
├─ docs/                                   # Documentation files directory
│  ├─ DOCS.md                              # Main documentation file
├─ logs/                                   # Log files directory
│  ├─ application.log                      # Application's log file
├─ scripts/                                # Scripts directory
│  ├─ seed_db.sh                           # Script for seeding the database
├─ tux/                                    # Main application directory
│  ├─ commands/                            # Directory for command files
│  │  ├─ quick_ban.py                      # File for the 'quick ban' command
│  ├─ events/                              # Directory for event files
│  │  ├─ on_message.py                     # File for the 'on message' event
│  ├─ utils/                               # Utility files directory
│  │  ├─ completions.py                    # Helper file for autocompletions
│  │  ├─ db.py                             # Database helper file
│  │  ├─ permissions.py                    # File to manage user permissions
│  │  ├─ tux_logger.py                     # Application's logger file
│  ├─ main.py                              # Main execution file
│  ├─ cog_loader.py                        # File for loading cogs/modules
├─ tests/                                  # Test files directory
│  ├─ commands/                            # Directory for command tests
│  │  ├─ test_quick_ban.py                 # Tests for the 'quick ban' command
│  ├─ events/                              # Directory for event tests
│  │  ├─ test_on_message.py                # Tests for the 'on message' event
│  ├─ utils/                               # Directory for utils tests
│  │  ├─ test_permissions.py               # Tests for user permissions file
├─ .env                                    # Environment variables
├─ .env.example                            # Example for setting up your own .env
├─ .gitignore                              # Specifies files to ignore in git
├─ .pre-commit-config.yaml                 # Configuration for pre-commit hooks
├─ docker-compose.yml                      # Docker compose for containerization
├─ LICENSE.md                              # Application's license
├─ Makefile                                # Make file for building the app
├─ poetry.lock                             # Lock file created by Poetry, ensuring consistent package versions
├─ pyproject.toml                          # Python project config file (used by poetry)
├─ README.md                               # Readme file with project info and setup guide
└─ requirements.txt                        # List of Python dependencies
```

## License
This project is licensed under the terms of the The Unlicense license. See the [LICENSE](LICENSE.md) file for details.