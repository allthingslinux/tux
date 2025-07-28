# Initialization Patterns Analysis

## Standard Initialization Pattern

### Basic Pattern (Found in 25+ cogs)

```python
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()
```

**Examples**:

- `tux/cogs/utility/ping.py`
- `tux/cogs/info/avatar.py`
- `tux/cogs/fun/fact.py`

### Extended Pattern with Usage Generation (Found in 15+ cogs)

```python
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()  # Sometimes omitted if using base class
    self.command1.usage = generate_usage(self.command1)
    self.command2.usage = generate_usage(self.command2, FlagsClass)
    # ... repeated for each command
```

**Examples**:

- `tux/cogs/admin/dev.py` (9 usage generations)
- `tux/cogs/moderation/ban.py` (1 usage generation)
- `tux/cogs/snippets/create_snippet.py` (1 usage generation)

### Base Class Pattern (Found in 8+ cogs)

```python
def __init__(self, bot: Tux) -> None:
    super().__init__(bot)  # Base class handles bot and db
    self.command.usage = generate_usage(self.command)
```

**Examples**:

- `tux/cogs/moderation/ban.py` (extends `ModerationCogBase`)
- `tux/cogs/snippets/create_snippet.py` (extends `SnippetsBaseCog`)

### Service Pattern with Configuration (Found in 3+ cogs)

```python
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()
    # Extensive configuration loading
    self.config_var1 = CONFIG.VALUE1
    self.config_var2 = CONFIG.VALUE2
    # ... multiple config assignments
```

**Examples**:

- `tux/cogs/services/levels.py` (8 config assignments)
- `tux/cogs/guild/config.py` (database controller assignment)

## Base Class Analysis

### ModerationCogBase

**Location**: `tux/cogs/moderation/__init__.py`
**Provides**:

- Database controller initialization
- Common moderation utilities
- Standardized error handling
- User action locking mechanisms
- Embed creation helpers

**Usage Pattern**:

```python
class Ban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.ban.usage = generate_usage(self.ban, BanFlags)
```

### SnippetsBaseCog

**Location**: `tux/cogs/snippets/__init__.py`
**Provides**:

- Database controller initialization
- Snippet-specific utilities
- Permission checking
- Common embed creation
- Error handling helpers

**Usage Pattern**:

```python
class CreateSnippet(SnippetsBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.create_snippet.usage = generate_usage(self.create_snippet)
```

## Database Controller Instantiation Analysis

### Direct Instantiation (35+ occurrences)

```python
self.db = DatabaseController()
```

### Through Base Class (8+ occurrences)

```python
# In base class __init__
self.db = DatabaseController()
```

### Specialized Controller Access (5+ occurrences)

```python
# In guild/config.py
self.db = DatabaseController().guild_config
```

## Usage Generation Pattern Analysis

### Manual Generation (100+ occurrences)

```python
self.command_name.usage = generate_usage(self.command_name)
self.command_with_flags.usage = generate_usage(self.command_with_flags, FlagsClass)
```

### Patterns by Cog Type

- **Admin cogs**: 5-10 usage generations per cog
- **Moderation cogs**: 1-2 usage generations per cog
- **Utility cogs**: 1-3 usage generations per cog
- **Service cogs**: 0-1 usage generations per cog

## Configuration Loading Patterns

### Simple Configuration (Most cogs)

```python
# No explicit configuration loading
# Uses imported CONFIG where needed
```

### Complex Configuration (Service cogs)

```python
def __init__(self, bot: Tux) -> None:
    self.bot = bot
    self.db = DatabaseController()
    self.xp_cooldown = CONFIG.XP_COOLDOWN
    self.levels_exponent = CONFIG.LEVELS_EXPONENT
    self.xp_roles = {role["level"]: role["role_id"] for role in CONFIG.XP_ROLES}
    self.xp_multipliers = {role["role_id"]: role["multiplier"] for role in CONFIG.XP_MULTIPLIERS}
    self.max_level = max(item["level"] for item in CONFIG.XP_ROLES)
    self.enable_xp_cap = CONFIG.ENABLE_XP_CAP
```

## Dependency Relationships

### Direct Dependencies (All cogs)

- `Tux` bot instance
- `DatabaseController` (directly or through base class)

### Indirect Dependencies (Through usage)

- `EmbedCreator` for embed creation
- `generate_usage` for command usage strings
- Various utility functions
- Configuration objects

### External Dependencies

- Discord.py components
- Prisma database models
- Sentry for monitoring
- Various utility libraries

## Anti-Patterns Identified

1. **Repeated Database Controller Instantiation**: Every cog creates its own instance
2. **Manual Usage Generation**: Repetitive boilerplate for every command
3. **Inconsistent Base Class Usage**: Some cogs use base classes, others don't
4. **Configuration Scattering**: Configuration access patterns vary widely
5. **Tight Coupling**: Direct instantiation creates tight coupling to implementations

## Improvement Opportunities

1. **Dependency Injection Container**: Centralize instance management
2. **Automatic Usage Generation**: Use decorators or metaclasses
3. **Consistent Base Classes**: Extend base class pattern to all cogs
4. **Configuration Injection**: Make configuration injectable
5. **Service Locator Pattern**: Centralize service access
