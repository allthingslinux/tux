# Dynamic and DRY Moderation Command System

## Overview

This document outlines a comprehensive approach to implementing truly dynamic and DRY (Don't Repeat Yourself) moderation commands using the `mixed_args` system.

## Current State Analysis

### Problems with Current Implementation

1. **Code Duplication**: Each moderation command has nearly identical argument parsing logic
2. **Inconsistent Patterns**: Some commands use flags, others use positional arguments, some use mixed
3. **Maintenance Overhead**: Changes to argument parsing require updates across multiple files
4. **Inconsistent User Experience**: Different commands have different argument formats

### Current Command Structure

```
tux/cogs/moderation/
├── __init__.py          # Base class with common functionality
├── timeout.py           # Individual command implementation
├── ban.py              # Individual command implementation
├── tempban.py          # Individual command implementation
├── kick.py             # Individual command implementation
└── ...                 # 15+ more individual files
```

## Proposed Solution: Dynamic Command System

### Architecture Overview

```
└── tux/cogs/moderation/
    ├── __init__.py              # Enhanced base class
    ├── command_config.py        # Command definitions
    ├── dynamic_moderation.py    # Dynamic command generation
    └── DRY_APPROACH.md         # This document
```

### Key Components

#### 1. Command Configuration System

**File**: `command_config.py`

```python
@dataclass
class ModerationCommandConfig:
    name: str
    aliases: list[str]
    case_type: CaseType
    required_permission_level: int
    supports_duration: bool
    supports_purge: bool
    dm_action: str
    discord_action: Callable
    # ... other configuration options
```

**Benefits**:

- Single source of truth for command behavior
- Easy to add new commands
- Consistent configuration across all commands

#### 2. Enhanced Base Class

**File**: `__init__.py` (enhanced)

```python
class ModerationCogBase(commands.Cog):
    async def execute_mixed_mod_action(
        self,
        ctx: commands.Context[Tux],
        config: ModerationCommandConfig,
        user: discord.Member | discord.User,
        mixed_args: str,
    ) -> None:
        """Execute moderation action using mixed_args parsing."""
        # Unified argument parsing
        # Unified validation
        # Unified execution
        # Unified response handling
```

**Benefits**:

- Centralized logic for all moderation actions
- Consistent error handling
- Unified logging and case creation

#### 3. Dynamic Command Generation

**File**: `dynamic_moderation.py`

```python
class DynamicModerationCog(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self._generate_commands()
    
    def _generate_commands(self) -> None:
        """Generate all moderation commands from configuration."""
        for name, config in MODERATION_COMMANDS.items():
            self._create_command(name, config)
```

**Benefits**:

- Automatic command generation from configuration
- Consistent command structure
- Easy to maintain and extend

## Implementation Strategy

### Phase 1: Foundation (Current)

✅ **Completed**:

- Fixed `mixed_args.py` parsing issues
- Created demonstration command (`dtimeout`)
- Established proof of concept

### Phase 2: Enhanced Base Class

**Next Steps**:

1. Add `execute_mixed_mod_action()` method to `ModerationCogBase`
2. Add unified argument parsing and validation
3. Add unified error handling and response generation

```python
async def execute_mixed_mod_action(
    self,
    ctx: commands.Context[Tux],
    config: ModerationCommandConfig,
    user: discord.Member | discord.User,
    mixed_args: str,
) -> None:
    """Execute moderation action with unified mixed_args parsing."""
    
    # Parse arguments
    parsed_args = parse_mixed_arguments(mixed_args)
    
    # Validate arguments based on config
    validated_args = self._validate_args(config, parsed_args)
    
    # Check conditions
    if not await self.check_conditions(ctx, user, ctx.author, config.name):
        return
    
    # Execute action
    await self.execute_mod_action(
        ctx=ctx,
        case_type=config.case_type,
        user=user,
        reason=validated_args.get("reason", "No reason provided"),
        silent=validated_args.get("silent", False),
        dm_action=config.dm_action,
        actions=[(config.discord_action(ctx.guild, user, validated_args), type(None))],
    )
```

### Phase 3: Command Registry

**Next Steps**:

1. Complete the command configuration system
2. Define all moderation commands in the registry
3. Create dynamic command generation

```python
MODERATION_COMMANDS = {
    "ban": ModerationCommandConfig(
        name="ban",
        aliases=["b"],
        case_type=CaseType.BAN,
        required_permission_level=3,
        supports_duration=False,
        supports_purge=True,
        dm_action="banned",
        discord_action=lambda guild, user, args: guild.ban(
            user, 
            reason=args.get("reason"), 
            delete_message_seconds=args.get("purge", 0) * 86400
        ),
    ),
    # ... all other commands
}
```

### Phase 4: Migration

**Next Steps**:

1. Create parallel implementation alongside existing commands
2. Test thoroughly with existing test suite
3. Gradually migrate commands one by one
4. Remove old implementations after validation

## Benefits of This Approach

### 1. Code Reduction

**Before**: 15+ individual command files (~2000 lines)
**After**: 3 files (~500 lines)
**Reduction**: ~75% less code

### 2. Consistency

- All commands use the same argument parsing
- All commands have the same error handling
- All commands follow the same patterns
- Unified user experience across all commands

### 3. Maintainability

- Single place to update argument parsing logic
- Single place to update validation rules
- Single place to update error messages
- Easy to add new commands

### 4. Flexibility

- Easy to add new argument types
- Easy to modify command behavior
- Easy to add new validation rules
- Easy to customize per-command behavior

## Example Usage

### Current Approach (Inconsistent)

```bash
# Different commands, different syntax
timeout @user 14d reason
ban @user reason -p 7
kick @user -r reason -s
```

### New Approach (Consistent)

```bash
# All commands use the same syntax
timeout @user 14d reason
ban @user reason -p 7
kick @user reason -s

# Or with flags
timeout @user reason -d 14d
ban @user reason -p 7 -s
kick @user reason -s
```

## Migration Path

### Step 1: Parallel Implementation

- Keep existing commands working
- Create new dynamic commands with different names (e.g., `dtimeout`)
- Test thoroughly

### Step 2: Gradual Migration

- Migrate one command at a time
- Update tests to use new commands
- Validate functionality

### Step 3: Cleanup

- Remove old command implementations
- Update documentation
- Remove unused flag classes

## Testing Strategy

### Unit Tests

- Test argument parsing for each command type
- Test validation logic
- Test error handling

### Integration Tests

- Test full command execution
- Test with real Discord API calls
- Test permission handling

### User Experience Tests

- Test all argument combinations
- Test error messages
- Test help text generation

## Conclusion

This dynamic and DRY approach provides:

1. **Massive code reduction** (75% less code)
2. **Consistent user experience** across all commands
3. **Easy maintenance** and extension
4. **Better testing** with unified logic
5. **Future-proof architecture** for new commands

The implementation is designed to be:

- **Backward compatible** during migration
- **Gradually adoptable** (one command at a time)
- **Thoroughly testable** with existing test infrastructure
- **Extensible** for future moderation features

This approach transforms the moderation system from a collection of individual commands into a unified, maintainable, and extensible system that provides a consistent experience for both users and developers.
