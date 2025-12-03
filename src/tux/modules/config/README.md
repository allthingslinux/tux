# Configuration System Design

## Overview

The configuration system provides a comprehensive, modular interface for managing server settings, permissions, and channels using a modern Discord Components V2 architecture.

## Architecture

The config system is built with clean separation of concerns:

### Command Layer (`src/tux/modules/config/`)

- **`Config`**: Main cog orchestrating all config operations
- **`RankManager`**: Permission rank management (create, list, delete)
- **`RoleManager`**: Role-to-rank assignment management
- **`CommandManager`**: Command permission management
- **`LogManager`**: Log channel configuration commands

### UI Layer (`src/tux/ui/views/config/`)

- **`ConfigDashboard`**: Main unified dashboard interface
- **`ConfigSection`**: Base class for configuration sections
- **`Component Registry`**: Type-safe UI component creation
- **`Page System`**: Pagination and component limit management

### Core Concepts

- **Modular Sections**: Each config area (logs, roles, permissions) is a self-contained section
- **Type-Safe Options**: Configuration options with validation and proper typing
- **Component Registry**: Extensible system for different UI component types
- **Pagination**: Automatic handling of Discord's component limits

## Key Improvements

### Modern Components V2 Architecture

- **Integrated UI**: Text, buttons, and selects in unified layouts using Discord's latest components
- **Type Safety**: Full type hints and validation throughout the system
- **Modular Design**: Clean separation between UI, business logic, and data persistence
- **Extensible Registry**: Easy to add new configuration option types and sections

### Component Registry System

```python
# Register new component types
registry.register_component("channel", ChannelSelector)
registry.register_component("role", RoleSelector)

# Create components type-safely
channel_option = ConfigOption[discord.TextChannel | None](
    key="log_channel",
    name="Log Channel",
    default_value=None,
    validator=validate_channel
)
```

### Pagination & Component Limits

- **Automatic Pagination**: Handles Discord's 5 ActionRow limit per message
- **Smart Grouping**: Organizes components efficiently within limits
- **Page Navigation**: Smooth navigation between configuration pages

### Modular Section Architecture

```python
class LogConfigSection(ConfigSection):
    """Self-contained log configuration section."""

    async def load_from_database(self):
        # Load log channel settings

    async def save_to_database(self):
        # Save log channel settings

    async def build_ui(self) -> discord.ui.Container:
        # Build log configuration UI
```

## Command Reference

All commands use hybrid slash + prefix syntax with interactive Components V2 UIs.

### Unified Dashboard

```bash
$config overview                    # Main configuration dashboard
$config wizard                      # Interactive setup wizard
$config logs                        # Log channel configuration
$config rank list                   # Rank management
$config role list                   # Role assignments
$config command list                # Command permissions
```

## File Structure

```text
src/tux/modules/config/           # Command layer
├── config.py                      # Main cog
├── logs.py                        # Log configuration commands
├── ranks.py                       # Rank management commands
├── roles.py                       # Role assignment commands
├── commands.py                    # Command permission commands
├── overview.py                    # Dashboard commands
└── wizard.py                      # Setup wizard commands

src/tux/ui/views/config/           # UI layer
├── core.py                        # Foundation classes & utilities
├── ui_core.py                     # UI component wrappers
├── registry.py                    # Component registry & schemas
├── sections.py                    # Configuration section implementations
├── dashboard.py                   # Main dashboard LayoutView
└── README.md                      # UI architecture documentation
```

## Migration from Old System

The new system replaces the previous monolithic approach with:

- **Modular Architecture**: Each config area is self-contained
- **Type-Safe Components**: Full type hints and validation
- **Components V2**: Modern Discord UI with integrated layouts
- **Registry System**: Extensible component creation
- **Automatic Pagination**: Handles Discord's component limits

### Benefits

- **Maintainable**: Clean separation of concerns
- **Extensible**: Easy to add new configuration types
- **Type-Safe**: Full type checking throughout
- **Modern UX**: Rich, integrated Discord interfaces
- **Scalable**: Handles complex configurations with pagination
