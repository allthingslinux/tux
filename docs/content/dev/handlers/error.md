# Error Handling System

The error handling system in Tux provides comprehensive error management for both application commands and traditional prefix commands.

The error handler integrates with Sentry for error tracking and uses Loguru for logging.

## Architecture

The system consists of three main components:

1. Error mapping system
2. Application command error handler
3. Traditional command error handler

## Error Mapping

The `error_map` dictionary maps exception types to user-friendly error messages. It handles:

```python
error_map: dict[type[Exception], str] = {
    app_commands.AppCommandError: "An error occurred: {error}",
    commands.CommandError: "An error occurred: {error}",
    # ... other mappings
}
```

### Supported Error Types

#### Application Commands

- Command invocation errors
- Transformer errors
- Permission errors (roles, permissions)
- Cooldown errors
- Command signature mismatches

#### Traditional Commands

- Command invocation errors
- Conversion errors
- Missing arguments/flags
- Permission errors
- Cooldown management
- Custom permission errors

## Error Handler Implementation

### Application Command Errors

The `on_app_command_error` method handles errors from slash commands and other application commands:

```python
async def on_app_command_error(
    self,
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None
```

Key features:

- Maps errors to user-friendly messages
- Sends ephemeral error responses
- Integrates with Sentry for error tracking
- Handles both responded and unresponded interactions

### Traditional Command Errors

The `on_command_error` method handles errors from prefix commands:

```python
async def on_command_error(
    self,
    ctx: commands.Context[Tux],
    error: commands.CommandError | commands.CheckFailure,
) -> None
```

Features:

- Handles command and check failures
- Provides detailed error messages
- Supports custom error handlers in cogs
- Integrates with Sentry and logging

## Error Response Format

Errors are presented to users through embeds with:

- Error type indication
- User-friendly message
- Ephemeral display (only visible to the command invoker)
- Automatic cleanup (messages delete after 30 seconds)

## Custom Error Types

The system supports custom error types for permission management:

- `PermissionLevelError`: For traditional commands
- `AppCommandPermissionLevelError`: For application commands

## Error Logging

### Sentry Integration

All errors are tracked in Sentry with:

- Full exception details
- Stack traces
- Context information

### Local Logging

The `log_error_traceback` method provides detailed local logging:

```python
@staticmethod
def log_error_traceback(error: Exception) -> None
```

Features:

- Full stack trace logging
- Formatted error output
- Integration with Loguru

## Best Practices

When working with the error handling system:

1. **Custom Error Messages**
   - Add new error types to `error_map`
   - Use format strings for dynamic content
   - Keep messages user-friendly

2. **Error Handling**
   - Let the global handler manage common errors
   - Implement specific handlers for unique cases
   - Use appropriate error types

3. **Security**
   - Use ephemeral messages for errors
   - Avoid exposing sensitive information
   - Log appropriately based on error severity

4. **Custom Errors**
   - Extend existing error types when possible
   - Include relevant context in error messages
   - Register new errors in the error map

## Example Usage

### Adding New Error Types

```python
error_map[CustomError] = "A custom error occurred: {error}"
```

### Custom Error Handler in Cog

```python
@commands.Cog.listener()
async def cog_command_error(self, ctx, error):
    # Handle cog-specific errors
    pass
```

### Raising Custom Errors

```python
if not user.has_permission:
    raise PermissionLevelError("required_permission")
```
