# Mixed Arguments System

The Tux bot now supports a flexible argument parsing system that allows commands to accept both positional arguments and flag-based arguments simultaneously. This provides users with multiple ways to interact with commands while maintaining backward compatibility.

## Overview

The mixed arguments system allows commands to accept arguments in multiple formats:

- **Traditional flags**: `command @user reason -d 14d`
- **Positional arguments**: `command @user 14d reason`
- **Mixed usage**: `command @user 14d reason -s`

Positional arguments take precedence over flag arguments when both are provided.

## Supported Commands

Currently, the following commands support mixed arguments:

### Timeout Command

```bash
# Traditional flag format
timeout @user reason -d 14d
timeout @user reason -d 14d -s

# Positional format
timeout @user 14d reason
timeout @user 14d

# Mixed format
timeout @user 14d reason -s
timeout @user 14d -s
```

### Tempban Command

```bash
# Traditional flag format
tempban @user reason -d 14d
tempban @user reason -d 14d -p 7 -s

# Positional format
tempban @user 14d reason
tempban @user 14d

# Mixed format
tempban @user 14d reason -s
tempban @user 14d -p 7 -s
```

## Implementation Details

### Utility Functions

The system is built around several utility functions in `tux/utils/mixed_args.py`:

#### `is_duration(text: str) -> bool`

Checks if a string matches a duration pattern (e.g., "14d", "1h30m").

```python
from tux.utils.mixed_args import is_duration

is_duration("14d")  # True
is_duration("1h30m")  # True
is_duration("reason")  # False
```

#### `generate_mixed_usage(command_name, required_params, optional_params, flags) -> str`

Generates a usage string that shows both positional and flag formats.

```python
from tux.utils.mixed_args import generate_mixed_usage

usage = generate_mixed_usage(
    "timeout", 
    ["member"], 
    ["duration", "reason"], 
    ["-d duration", "-s"]
)
# Result: "timeout <member> [duration|reason] [-d duration] [-s]"
```

#### `parse_mixed_arguments(argument_string: str) -> Dict[str, Any]`

Parses mixed positional and flag arguments from a string.

```python
from tux.utils.mixed_args import parse_mixed_arguments

args = parse_mixed_arguments("14d reason -s")
# Result: {'duration': '14d', 'reason': 'reason', 'silent': True}
```

### Command Implementation Pattern

To implement mixed arguments in a new command, follow this pattern:

```python
@commands.hybrid_command(name="example")
async def example(
    self,
    ctx: commands.Context[Tux],
    member: discord.Member,
    duration_or_reason: str | None = None,
    *,
    flags: ExampleFlags | None = None,
) -> None:
    """
    Example command with mixed arguments.
    
    Supports both positional and flag-based arguments:
    - Positional: `example @user 14d reason`
    - Flag-based: `example @user reason -d 14d`
    - Mixed: `example @user 14d reason -s`
    """
    
    # Parse arguments - support both positional and flag formats
    duration = None
    reason = None
    silent = False

    # Check if duration_or_reason is a duration
    if duration_or_reason and is_duration(duration_or_reason):
        duration = duration_or_reason
        if flags:
            reason = flags.reason
            silent = flags.silent
        else:
            reason = "No reason provided"
    else:
        # duration_or_reason is not a duration, treat as reason
        if duration_or_reason:
            reason = duration_or_reason
        elif flags:
            reason = flags.reason
        else:
            reason = "No reason provided"
        
        # Use flags for duration and silent if provided
        if flags:
            duration = flags.duration
            silent = flags.silent

    # Validate required arguments
    if not duration:
        await ctx.send("Duration is required.", ephemeral=True)
        return

    # Process the command...
```

### Usage Generation

Update the command's usage string in the `__init__` method:

```python
def __init__(self, bot: Tux) -> None:
    super().__init__(bot)
    self.example.usage = generate_mixed_usage(
        "example", 
        ["member"], 
        ["duration", "reason"], 
        ["-d duration", "-s"]
    )
```

## Duration Format

The system recognizes duration values in the following format:

- `s` - seconds
- `m` - minutes  
- `h` - hours
- `d` - days

Examples:

- `30s` - 30 seconds
- `5m` - 5 minutes
- `2h` - 2 hours
- `14d` - 14 days
- `1h30m` - 1 hour 30 minutes

## Backward Compatibility

All existing flag-based commands continue to work exactly as before. The mixed arguments system is additive and doesn't break any existing functionality.

## Future Expansion

The system can be extended to support other types of arguments:

- Numeric values (purge days, limits, etc.)
- Boolean flags (silent, quiet, etc.)
- String values (reasons, messages, etc.)

To add support for new argument types, update the `parse_mixed_arguments` function in `tux/utils/mixed_args.py`.

## Best Practices

1. **Always provide clear usage examples** in command docstrings
2. **Use the `generate_mixed_usage` function** for consistent usage strings
3. **Validate required arguments** before processing
4. **Maintain backward compatibility** with existing flag-based usage
5. **Test both formats** to ensure they work correctly

## Error Handling

The system includes robust error handling:

- Invalid duration formats are caught and reported
- Missing required arguments are handled gracefully
- Conflicting arguments (positional vs flag) are resolved with positional taking precedence
- Invalid flag values are ignored rather than causing errors
