# Configuration UI System

A modular, extensible configuration interface system built with Discord Components V2.

## Architecture

The config UI system is designed with clean separation of concerns and modular extensibility:

```text
config/
├── dashboard.py          # Main dashboard interface (unified config UI)
├── modals.py             # Modal dialogs (create/edit ranks)
├── pagination.py         # Pagination navigation helpers and setup
├── callbacks.py          # Callback utilities (auth, error handling)
├── helpers.py            # UI helper functions (back buttons, error containers)
├── command_discovery.py  # Command discovery utilities
└── __init__.py           # Public API exports
```

## Core Components

### ConfigDashboard

The main unified configuration dashboard that provides a single interface for all configuration needs.

```python
from tux.ui.views.config import ConfigDashboard

# Create dashboard in specific mode
dashboard = ConfigDashboard(bot, guild, author, mode="logs")
await dashboard.build_layout()
await ctx.send(view=dashboard)
```

**Available Modes:**

- `overview` - Main dashboard with navigation buttons
- `logs` - Log channel configuration
- `ranks` - Permission rank management
- `roles` - Role-to-rank assignments
- `commands` - Command permission assignments

## Utilities

### Pagination Helpers

Reusable pagination utilities for consistent navigation:

```python
from tux.ui.views.config.pagination import PaginationHelper

# Setup pagination state
start_idx, end_idx, total_pages, current_page = PaginationHelper.setup_pagination(
    dashboard, "ranks_current_page", total_items, items_per_page
)

# Build navigation buttons
nav_row = PaginationHelper.build_navigation(
    "ranks", current_page, total_pages, page_change_handler
)
```

### Callback Utilities

Common patterns for authorization and error handling:

```python
from tux.ui.views.config.callbacks import validate_author, handle_callback_error

# Validate user authorization
if not await validate_author(interaction, dashboard.author, "Not authorized"):
    return

# Handle errors consistently
await handle_callback_error(interaction, error, "update configuration")
```

### UI Helpers

Reusable UI component builders:

```python
from tux.ui.views.config.helpers import create_back_button, create_error_container

# Create standardized back button
back_btn = create_back_button(dashboard)

# Create error container with back button
error_container = create_error_container("Something went wrong", dashboard)
```

## Usage

### Creating a Configuration Dashboard

```python
from tux.ui.views.config import ConfigDashboard

# Create dashboard in overview mode (default)
dashboard = ConfigDashboard(bot, guild, author)
await dashboard.build_layout()
await ctx.send(view=dashboard)

# Or open directly in a specific mode
dashboard = ConfigDashboard(bot, guild, author, mode="commands")
await dashboard.build_layout()
await ctx.send(view=dashboard)
```

### Adding New Configuration Modes

1. Add a new `_build_X_mode()` method to `ConfigDashboard`
2. Update `build_layout()` to handle the new mode
3. Add navigation button in `_build_overview_mode()` if needed
4. Update `_handle_mode_change()` to route to the new mode

### Component Limits Handling

The system automatically handles Discord's component limits through:

- Pagination for large option sets (configurable per mode)
- ActionRow grouping (max 5 components per row)
- Container-based organization
- Smart component distribution
- Caching to avoid rebuilding unchanged modes

## Best Practices

### Separation of Concerns

- Dashboard handles UI construction and user interaction
- Utilities handle reusable patterns (pagination, callbacks, helpers)
- Modals handle complex input forms

### Type Safety

- Use strict type hints throughout
- Leverage TypeVar for generic components
- Validate all inputs with proper error handling

### Extensibility

- Add new modes without modifying existing code
- Use utilities for consistent patterns
- Follow existing patterns for new features

### Error Handling

- Validate user permissions on all interactions
- Provide meaningful error messages
- Use `handle_callback_error` for consistent error handling
- Gracefully handle database operation failures

## Constants

Configuration constants are centralized in `tux.shared.constants`:

- `CONFIG_COLOR_BLURPLE`, `CONFIG_COLOR_GREEN`, etc. - Dashboard colors
- `CONFIG_RANKS_PER_PAGE`, `CONFIG_ROLES_PER_PAGE`, etc. - Pagination sizes
- `CONFIG_DASHBOARD_TIMEOUT` - Dashboard timeout (5 minutes)
