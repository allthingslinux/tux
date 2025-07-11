# Tux Architecture

This document describes the new modular, scalable, and minimal architecture for Tux.

## Directory Structure

```plaintext
tux/
├── core/                    # Core bot functionality
│   ├── __init__.py
│   ├── app.py              # Application orchestration
│   ├── bot.py              # Main bot class
│   ├── cog_loader.py       # Cog loading system
│   ├── config.py           # Configuration management
│   ├── env.py              # Environment utilities
│   ├── help.py             # Help command system
│   ├── ui/                 # User interface components
│   │   ├── __init__.py
│   │   ├── embeds.py       # Embed creation utilities
│   │   ├── buttons.py      # Button components
│   │   ├── help_components.py
│   │   ├── views/          # Discord view components
│   │   └── modals/         # Discord modal components
│   └── utils/              # Core utilities
│       ├── __init__.py
│       ├── functions.py    # General utility functions
│       ├── constants.py    # Constants and enums
│       ├── exceptions.py   # Custom exceptions
│       ├── ascii.py        # ASCII art utilities
│       ├── regex.py        # Regex patterns
│       ├── emoji.py        # Emoji management
│       ├── converters.py   # Discord converters
│       ├── checks.py       # Permission checks
│       ├── flags.py        # Command flag utilities
│       ├── help_utils.py   # Help system utilities
│       └── banner.py       # Startup banner
├── infra/                  # Infrastructure components
│   ├── __init__.py
│   ├── database/           # Database layer
│   │   ├── __init__.py
│   │   ├── client.py       # Database client
│   │   └── controllers/    # Database controllers
│   ├── logger.py           # Logging configuration
│   ├── sentry.py           # Sentry integration
│   ├── hot_reload.py       # Hot reload system
│   ├── wrappers/           # External API wrappers
│   │   ├── __init__.py
│   │   ├── godbolt.py      # Compiler API
│   │   ├── wandbox.py      # Code execution
│   │   ├── github.py       # GitHub API
│   │   ├── xkcd.py         # XKCD API
│   │   └── tldr.py         # TLDR API
│   └── handlers/           # Infrastructure handlers
│       ├── __init__.py
│       ├── error.py        # Error handling
│       ├── sentry.py       # Sentry integration
│       ├── event.py        # Event handling
│       └── activity.py     # Activity management
├── modules/                # Official feature modules
│   ├── __init__.py
│   ├── moderation/         # Moderation commands
│   ├── fun/               # Fun commands
│   ├── info/              # Information commands
│   ├── admin/             # Admin commands
│   ├── snippets/          # Code snippet commands
│   ├── levels/            # Leveling system
│   ├── guild/             # Guild management
│   ├── services/          # Service integrations
│   ├── tools/             # Utility tools
│   └── utility/           # General utilities
├── custom_modules/         # Self-hoster add-ons (gitignored)
│   └── README.md
├── cli/                   # CLI tools
│   └── __init__.py
├── assets/                # Static assets
│   ├── emojis/
│   ├── branding/
│   └── embeds/
├── main.py                # Application entry point
└── tests/                 # Test suite
    ├── core/
    ├── infra/
    ├── modules/
    └── cli/
```

## Architecture Principles

### 1. Clear Separation of Concerns

- **Core**: Essential bot functionality, startup, shared UI, helpers
- **Infrastructure**: Database, logging, external APIs, infrastructure handlers
- **Modules**: Feature modules (cogs/extensions) for official functionality
- **Custom Modules**: Self-hoster add-ons (not tracked in git)

### 2. Minimal Root-Level Clutter

Only essential directories at the top level:
- `core/` - Core functionality
- `infra/` - Infrastructure
- `modules/` - Official features
- `custom_modules/` - User add-ons
- `main.py` - Entry point

### 3. Extensibility Model

#### Official Modules (`modules/`)
- Maintained by Tux team
- Always loaded by default
- Tracked in git
- Core features and public bot functionality

#### Custom Modules (`custom_modules/`)
- Maintained by self-hosters
- Only loaded if present
- Not tracked in git (unless using submodules)
- Server-specific, private, or experimental features

### 4. Loading Order

1. **Infrastructure Handlers** (`infra/handlers/`) - Highest priority
2. **Official Modules** (`modules/`) - Core features
3. **Custom Modules** (`custom_modules/`) - User add-ons

## Module Structure

Each module should follow this structure:

```plaintext
modules/moderation/
├── __init__.py           # Module setup
├── commands.py           # Command implementations
├── services.py           # Business logic
├── tasks.py              # Background tasks
├── models.py             # Data models (if needed)
└── README.md             # Module documentation
```

## Import Guidelines

### From Core
```python
from core.bot import Tux
from core.config import CONFIG
from core.utils.functions import generate_usage
from core.ui.embeds import EmbedCreator
```

### From Infrastructure
```python
from infra.database.controllers import DatabaseController
from infra.wrappers.github import GitHubWrapper
from infra.sentry import start_span
```

### From Other Modules
```python
from modules.services.levels import LevelsService
```

### From Custom Modules
```python
# Custom modules can import from core, infra, and modules
from core.bot import Tux
from infra.database.client import db
```

## Database Considerations

- **Core-only**: Most modules use the core's database API/models
- **Advanced**: Modules can define their own models (careful with migrations)
- **Isolated**: Small, isolated data can use local files (SQLite, JSON)

## Testing

Tests mirror the main structure:
- `tests/core/` - Core functionality tests
- `tests/infra/` - Infrastructure tests
- `tests/modules/` - Module tests
- `tests/cli/` - CLI tool tests

## Migration Guide

### For Contributors

1. **New Features**: Add to appropriate `modules/` subdirectory
2. **Infrastructure**: Add to `infra/` with appropriate subdirectory
3. **Core Changes**: Add to `core/` with appropriate subdirectory
4. **Tests**: Add to corresponding `tests/` subdirectory

### For Self-Hosters

1. **Custom Features**: Add to `custom_modules/`
2. **Simple Extensions**: Single `.py` file
3. **Complex Extensions**: Package with `__init__.py`
4. **Shared Extensions**: Use git submodules

## Benefits

1. **Scalability**: Easy to add new features without cluttering
2. **Maintainability**: Clear organization makes code easier to find
3. **Contributor-Friendly**: Logical structure for new contributors
4. **Self-Hosting**: Easy to add custom features without touching main code
5. **Testing**: Mirrored test structure for clarity
6. **Extensibility**: Support for both official and custom modules

## Future Considerations

- Plugin system for third-party modules
- Module marketplace
- Automated module discovery
- Module dependency management
- Module versioning and updates
