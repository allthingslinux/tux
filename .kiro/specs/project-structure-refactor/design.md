# Design Document

## Overview

This design document outlines the architectural refactor for the Tux Discord bot project, transforming the current organic structure into a well-organized, scalable architecture. The design adopts a hybrid approach combining community standards for Discord bots with modern application architecture patterns, ensuring both familiarity for Discord bot developers and scalability for future growth.

The refactor will reorganize the existing `tux/` directory structure while preserving all functionality. The new architecture emphasizes clear separation of concerns, improved maintainability, and enhanced developer experience.

## Architecture

### High-Level Architecture Principles

1. **Hybrid Modular Architecture**: Combines monorepo structure with self-contained packages for maximum flexibility
2. **Core-Extension Separation**: Essential functionality in core, optional features as loadable extensions
3. **Plugin System**: Self-contained packages that can be enabled/disabled independently
4. **Layered Architecture**: Clear separation between presentation (Discord interface), application logic (business rules), and infrastructure (database, external services)
5. **Domain-Driven Organization**: Features grouped by business domain rather than technical concerns
6. **Dependency Inversion**: High-level modules don't depend on low-level modules; both depend on abstractions
7. **Monorepo-Ready**: Structure supports future addition of web dashboard, API, or other applications
8. **Community Standards**: Aligns with established Discord bot development patterns

### Proposed Directory Structure

Based on community feedback and current structure analysis, here's the refined directory structure:

```
tux/
├── core/                  # Essential bot infrastructure ONLY
│   ├── __init__.py        # (existing DI system)
│   ├── app.py             # Application orchestration (from tux/app.py)
│   ├── bot.py             # Bot client (from tux/bot.py)
│   ├── cog_loader.py      # Module loading system (from tux/cog_loader.py)
│   ├── base_cog.py        # (existing)
│   ├── container.py       # (existing)
│   ├── interfaces.py      # (existing)
│   ├── service_registry.py # (existing)
│   └── services.py        # (existing)
│
├── ui/                    # Bot UI components
│   ├── __init__.py
│   ├── embeds.py          # Common embed templates (from tux/ui/embeds.py)
│   ├── buttons.py         # Button components (from tux/ui/buttons.py)
│   ├── help_components.py # Help system components (from tux/ui/help_components.py)
│   ├── views/             # Reusable view components (from tux/ui/views/)
│   │   ├── __init__.py
│   │   ├── config.py      # (from tux/ui/views/config.py)
│   │   ├── confirmation.py # (from tux/ui/views/confirmation.py)
│   │   └── tldr.py        # (from tux/ui/views/tldr.py)
│   └── modals/            # Modal dialog components (from tux/ui/modals/)
│       ├── __init__.py
│       └── report.py      # (from tux/ui/modals/report.py)
│
├── utils/                 # Bot-specific utilities
│   ├── __init__.py
│   ├── ascii.py           # ASCII art utilities (from tux/utils/ascii.py)
│   ├── banner.py          # Banner utilities (from tux/utils/banner.py)
│   ├── checks.py          # Permission checks (from tux/utils/checks.py)
│   ├── converters.py      # Discord converters (from tux/utils/converters.py)
│   ├── emoji.py           # Emoji management (from tux/utils/emoji.py)
│   ├── flags.py           # Command flags (from tux/utils/flags.py)
│   └── help_utils.py      # Help system utilities (from tux/utils/help_utils.py)
│
├── services/              # Backend services
│   ├── __init__.py
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   ├── client.py      # Database client (from tux/database/client.py)
│   │   └── controllers/   # Data access controllers (from tux/database/controllers/)
│   │
│   ├── wrappers/          # External service integrations
│   │   ├── __init__.py
│   │   ├── godbolt.py     # Godbolt API wrapper (from tux/wrappers/godbolt.py)
│   │   ├── wandbox.py     # Wandbox API wrapper (from tux/wrappers/wandbox.py)
│   │   ├── github.py      # GitHub API wrapper (from tux/wrappers/github.py)
│   │   ├── xkcd.py        # XKCD API wrapper (from tux/wrappers/xkcd.py)
│   │   └── tldr.py        # TLDR API wrapper (from tux/wrappers/tldr.py)
│   │
│   ├── handlers/          # Event and error handlers
│   │   ├── __init__.py
│   │   ├── error.py       # Error handling (from tux/handlers/error.py)
│   │   ├── sentry.py      # Sentry error handling (from tux/handlers/sentry.py)
│   │   ├── event.py       # Discord event handlers (from tux/handlers/event.py)
│   │   └── activity.py    # Activity handlers (from tux/handlers/activity.py)
│   │
│   ├── logger.py          # Logging configuration (from tux/utils/logger.py)
│   ├── sentry.py          # Sentry integration (from tux/utils/sentry.py)
│   └── hot_reload.py      # Hot reload functionality (from tux/utils/hot_reload.py)
│
├── shared/                # Code shared across all applications (bot, cli, future web/api)
│   ├── __init__.py
│   ├── constants.py       # Application-wide constants (from tux/utils/constants.py)
│   ├── exceptions.py      # Base exception classes (from tux/utils/exceptions.py)
│   ├── functions.py       # Generic helper functions (from tux/utils/functions.py)
│   ├── regex.py           # Regex utilities (from tux/utils/regex.py)
│   ├── substitutions.py   # Text substitution utilities (from tux/utils/substitutions.py)
│   │
│   └── config/            # Configuration management
│       ├── __init__.py
│       ├── settings.py    # Configuration classes (from tux/utils/config.py)
│       └── env.py         # Environment variable handling (from tux/utils/env.py)
│
├── modules/               # Feature modules (self-contained packages)
│   ├── __init__.py
│   ├── moderation/        # Moderation functionality (from tux/cogs/moderation/)
│   ├── fun/               # Entertainment commands (from tux/cogs/fun/)
│   ├── info/              # Information commands (from tux/cogs/info/)
│   ├── admin/             # Administrative commands (from tux/cogs/admin/)
│   ├── snippets/          # Code snippets (from tux/cogs/snippets/)
│   ├── levels/            # Leveling system (from tux/cogs/levels/)
│   ├── guild/             # Guild management (from tux/cogs/guild/)
│   ├── services/          # Service modules (from tux/cogs/services/)
│   ├── tools/             # External tool integrations (from tux/cogs/tools/)
│   ├── utility/           # Utility commands (from tux/cogs/utility/)
│   └── ...                # Additional modules
│
├── custom_modules/        # User-defined custom modules (for self-hosters)
│   └── ...                # Custom extensions
│
│
├── cli/                   # Command-line interface (from tux/cli/)
│   ├── __init__.py
│   └── ...                # Existing CLI structure
│
├── assets/                # Static assets (from assets/)
│   ├── emojis/            # Emoji assets
│   ├── branding/          # Branding assets
│   ├── embeds/            # Embed templates
│   └── ...                # Other assets
│
├── main.py                # Application entry point (from tux/main.py)
│
└── tests/                 # Test structure mirroring main structure
    ├── core/              # Tests for core functionality
    ├── ui/                # Tests for UI components
    ├── utils/             # Tests for utilities
    ├── services/          # Tests for services
    ├── shared/            # Tests for shared code
    ├── modules/           # Tests for modules
    ├── cli/               # Tests for CLI
    └── ...                # Additional test directories
```

## Components and Interfaces

### Core Layer Components

#### Core Module (`tux/core/`)
- **bot.py**: Contains the main `Tux` bot class, extending `discord.ext.commands.Bot`
- **app.py**: Application orchestration and lifecycle management (`TuxApp` class)
- **cog_loader.py**: Dynamic module loading and management
- **container.py**: Dependency injection container (existing)
- **service_registry.py**: Service registration system (existing)
- **base_cog.py**: Base cog class with DI support (existing)

### UI Layer Components

#### UI Module (`tux/ui/`)
- **embeds.py**: Reusable embed templates and builders
- **buttons.py**: Button interaction components
- **help_components.py**: Help system UI components
- **views/**: Generic view components (confirmation dialogs, pagination)
- **modals/**: Modal dialog components

### Utils Layer Components

#### Utils Module (`tux/utils/`)
- **checks.py**: Permission and validation checks
- **converters.py**: Discord.py argument converters
- **flags.py**: Command flag definitions
- **ascii.py**: ASCII art utilities
- **banner.py**: Banner generation utilities
- **emoji.py**: Emoji management utilities
- **help_utils.py**: Help system utilities

### Services Layer Components

#### Database Module (`tux/services/database/`)
- **client.py**: Database connection and session management
- **controllers/**: Data access layer with repository pattern

#### Wrappers Module (`tux/services/wrappers/`)
- Wrappers for external APIs (GitHub, Godbolt, Wandbox, XKCD, TLDR)
- Standardized interface for external service integration
- Rate limiting and error handling for external calls

#### Handlers Module (`tux/services/handlers/`)
- **error.py**: Error handling and logging
- **event.py**: Discord event handlers
- **activity.py**: Bot activity management
- **sentry.py**: Sentry integration for error tracking

#### Service Utilities
- **logger.py**: Logging configuration and management
- **sentry.py**: Sentry integration and monitoring
- **hot_reload.py**: Hot reload functionality for development

### Shared Layer Components

#### Shared Module (`tux/shared/`)
- **constants.py**: Application-wide constants
- **exceptions.py**: Base exception classes
- **functions.py**: Generic helper functions
- **regex.py**: Regex utilities
- **substitutions.py**: Text substitution utilities

#### Config Module (`tux/shared/config/`)
- **settings.py**: Configuration management classes
- **env.py**: Environment variable handling

### Modules Layer Components

#### Feature Modules (`tux/modules/`)
Each module contains Discord commands and related functionality:
- **moderation/**: Moderation commands and logic
- **admin/**: Administrative commands
- **guild/**: Guild management features
- **utility/**: General utility commands
- **info/**: Information and lookup commands
- **fun/**: Entertainment commands
- **levels/**: User leveling system
- **snippets/**: Code snippet management
- **tools/**: External tool integrations
- **services/**: Background service modules



## Error Handling

### Hierarchical Error Structure
```python
# Base exceptions in shared/exceptions.py
class TuxError(Exception):
    """Base exception for all Tux-related errors."""

class TuxConfigurationError(TuxError):
    """Configuration-related errors."""

class TuxServiceError(TuxError):
    """Service layer errors."""

class TuxBotError(TuxError):
    """Bot layer errors."""
```

### Error Handling Strategy
1. **Layer-Specific Handling**: Each layer handles its own errors appropriately
2. **Centralized Logging**: All errors logged through structured logging
3. **User-Friendly Messages**: Bot errors translated to user-friendly Discord messages
4. **Monitoring Integration**: Critical errors automatically reported to Sentry

## Testing Strategy

### Test Structure Mirroring
```
tests/
├── unit/
│   ├── bot/
│   │   ├── features/
│   │   │   ├── moderation/
│   │   │   └── ...
│   │   └── components/
│   ├── services/
│   │   ├── database/
│   │   └── external/
│   └── shared/
│       └── utils/
├── integration/
│   ├── bot/
│   └── services/
└── fixtures/
    ├── discord/
    └── database/
```

### Testing Approach
1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Feature Tests**: End-to-end testing of complete features
4. **Mock Strategy**: Mock external dependencies (Discord API, database)

## Migration Strategy

### Phase 1: Infrastructure Setup
1. Create new directory structure
2. Set up import path mappings
3. Create base classes and interfaces

### Phase 2: Core Migration
1. Move and refactor core bot components
2. Update dependency injection system
3. Migrate shared utilities

### Phase 3: Feature Migration
1. Migrate features one domain at a time
2. Update imports and dependencies
3. Refactor cogs into feature structure

### Phase 4: Services Migration
1. Move database and external service code
2. Update service registrations
3. Refactor monitoring and task management

### Phase 5: Testing and Validation
1. Update all tests to match new structure
2. Validate all functionality works
3. Performance testing and optimization

## Import Path Strategy

### New Import Patterns
```python
# Core imports
from tux.core.bot import Tux
from tux.core.app import TuxApp
from tux.core.container import ServiceContainer

# UI imports
from tux.ui.embeds import ErrorEmbed
from tux.ui.views.confirmation import ConfirmationView

# Utils imports
from tux.utils.checks import has_permission
from tux.utils.flags import BanFlags

# Service imports
from tux.services.database.controllers import GuildController
from tux.services.wrappers.github import GitHubAPI

# Shared imports
from tux.shared.constants import DEFAULT_PREFIX
from tux.shared.config.settings import CONFIG
from tux.shared.exceptions import TuxError

# Module imports
from tux.modules.moderation.ban import Ban
from tux.modules.utility.ping import Ping
```

## Performance Considerations

### Lazy Loading
- Features loaded on-demand rather than at startup
- Service initialization optimized for fast bot startup
- Database connections pooled and managed efficiently

### Memory Management
- Singleton services for shared resources
- Proper cleanup of Discord resources
- Monitoring of memory usage patterns

### Caching Strategy
- Configuration caching at application level
- Database query result caching where appropriate
- External API response caching with TTL

## Security Considerations

### Access Control
- Permission checks centralized in shared utilities
- Feature-level access control through dependency injection
- Audit logging for administrative actions

### Data Protection
- Sensitive configuration isolated in secure modules
- Database credentials managed through environment variables
- API keys and tokens properly secured

### Input Validation
- Centralized input validation in shared utilities
- SQL injection prevention through ORM usage
- Discord input sanitization for user safety

This design provides a robust foundation for the Tux bot's future growth while maintaining the familiar patterns that Discord bot developers expect. The modular structure supports both current needs and future expansion into web applications or APIs.
