# Architecture Overview

This document provides a high-level overview of Tux's architecture and design principles.

## Structure

```bash
.
├── tux/
│   ├── main.py
│   ├── bot.py
│   ├── cog_loader.py
│   ├── help.py
│   ├── cogs
│   ├── database
│   ├── handlers
│   ├── ui
│   ├── utils
│   └── wrappers
```

### Key Components

#### `main.py` - The main entry point for the bot

#### `bot.py` - The main bot class

#### `cog_loader.py` - The cog loader class

#### `help.py` - The help command class

#### `cogs` - The directory for all cogs

#### `database` - The directory for all database controllers and client

#### `handlers`

The directory for various services and handlers that live "behind the scenes" of the bot.

#### `ui`

The directory for all UI components and views.

#### `utils`

The directory for all utility functions and classes.

**Important utilities to note:**

- `logger.py` - Our custom logger that overrides the default logger with `loguru` and `rich` for better logging.
- `config.py` - Our configuration manager that handles all bot configuration and secret/environment variables.
- `constants.py` - Our constants manager that handles all constant values used throughout the bot like colors, emojis, etc.
- `checks.py` - Our custom permission system that provides decorators for command access checks.
- `flags.py` - Our custom flag system that provides a way to handle flags for command arguments.

#### `wrappers`

The directory for all API wrappers and clients.

- We use `httpx` for all API requests.
