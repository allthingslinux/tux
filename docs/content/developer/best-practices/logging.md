---
title: Logging Best Practices
description: Logging best practices for Tux development using loguru, including structured logging, third-party library interception, and debugging patterns.
tags:
  - developer-guide
  - best-practices
  - logging
---

# Logging Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

Effective logging is essential for understanding what your bot is doing, debugging issues, and monitoring production systems. Good logs tell a story of what happened, when it happened, and why it happened. Bad logs are noise that obscures important information.

## Understanding Loguru in Tux

Tux uses loguru for all logging, configured centrally in `src/tux/core/logging.py`. This setup provides a single global logger that's ready to use—just import and start logging. The configuration handles environment-based log levels, intercepts third-party library logs, and formats output for easy reading.

The logger is configured automatically when Tux starts. Logging is initialized in the CLI start script (`scripts/tux/start.py`) before any other code runs, ensuring all log statements respect the configured level.

As a defensive fallback, logging is also configured in `TuxApp.start()` before Sentry initialization. You don't need to configure it yourself—just import `logger` from loguru and use it.

The configuration automatically routes logs from Discord.py, SQLAlchemy, httpx, and other libraries through loguru, giving you consistent log formatting across your entire application.

Log levels are determined by priority. Explicit configuration parameters override environment variables, which override debug flags, which override defaults. This lets you control logging at different levels—global defaults, environment-specific overrides, or per-command debugging.

## Choosing the Right Log Level

### TRACE

Use TRACE for extremely detailed debugging—function entry and exit, variable dumps, and step-by-step execution flow. This level produces the most verbose output and should only be enabled when you need to trace exact execution paths. Most development doesn't need TRACE level logging.

### DEBUG

Use DEBUG for development debugging—SQL queries, API calls, internal state changes, and detailed execution flow. DEBUG logs help you understand what your code is doing during development. They're too verbose for production but essential for troubleshooting issues.

Enable DEBUG logging when developing new features or debugging problems. Disable it in production to reduce log volume and improve performance. DEBUG logs include detailed information that helps you understand execution flow but isn't necessary for normal operation monitoring.

### INFO

Use INFO for normal operations—startup and shutdown events, user actions, important state changes, and significant milestones. INFO logs tell the story of what your bot is doing. They're the primary logs you'll read in production to understand bot behavior.

Log user actions at INFO level. When users execute commands, join servers, or perform significant actions, log these events. They help you understand bot usage patterns and troubleshoot user-reported issues.

### SUCCESS

Use SUCCESS for positive outcomes—successful operations, achievements, and completed milestones. SUCCESS logs highlight when things go right, making it easy to see successful operations in your logs. Use them sparingly for truly significant successes.

### WARNING

Use WARNING for potential issues that don't prevent functionality—rate limits approaching, degraded performance, recoverable errors, and fallback behavior. WARNING logs indicate something might be wrong but the bot continues operating normally.

When you handle errors gracefully, log them at WARNING level. If an API call fails but you use cached data, that's a warning—something went wrong but you handled it. If a database query fails but you retry successfully, log the failure as a warning.

### ERROR

Use ERROR for application errors that need attention—failed operations, data corruption, and unexpected failures. ERROR logs indicate something went wrong that prevented normal operation. These logs need investigation to understand what failed and why.

Log errors with full context. Include user IDs, command names, operation types, and relevant parameters. Without context, error logs are useless for debugging. Always include `exc_info=True` when logging exceptions to capture full stack traces.

### CRITICAL

Use CRITICAL for system failures that prevent core functionality—database corruption, unrecoverable errors, security issues, and system-level failures. CRITICAL logs indicate serious problems that need immediate attention. These are rare but important.

Reserve CRITICAL for truly critical failures. Don't use it for routine errors or recoverable failures. CRITICAL logs should trigger alerts and immediate investigation. If your bot can continue operating, it's not critical.

## Structured Logging

Tux provides structured logging helpers through `StructuredLogger`. These helpers create consistent, queryable logs with standardized fields. Use them for performance monitoring, database operations, and API calls.

Structured logs include consistent fields that make querying and analysis easier. Instead of parsing free-form log messages, you can query logs by operation type, duration, or other structured fields. This makes monitoring and debugging much easier.

Use structured logging for operations you want to monitor or analyze. Performance logs help identify slow operations. Database logs help track query performance. API logs help monitor external service health. Structured logs make it easy to build dashboards and alerts.

## Third-Party Library Logs

Tux automatically intercepts logs from common libraries and routes them through loguru. This gives you consistent log formatting and level control for all logs, not just your application code.

For example, Discord.py logs at INFO level, SQLAlchemy at DEBUG/WARNING, and HTTP clients at WARNING level.

You can add custom library interception by adding library names to `INTERCEPTED_LIBRARIES` in the logging configuration. This ensures all logs go through loguru with consistent formatting and level control.

## Logging Patterns

### Command Execution

Log command execution at INFO level with user and command context. Include the user who executed the command, the command name, and relevant parameters. This helps you understand command usage and troubleshoot user-reported issues.

Log command success at SUCCESS level for significant operations. When commands complete successfully, log the success with relevant context. This makes it easy to see successful operations in your logs.

Log command failures at ERROR level with full context. Include the user, command, error details, and exception information. This helps you understand what went wrong and why commands failed.

### Database Operations

Log database queries at DEBUG level during development. Include the query, duration, and result count. This helps you understand database performance and identify slow queries.

In production, let SQLAlchemy handle query logging automatically. The intercepted SQLAlchemy logs provide query information without cluttering your application logs. Only log database operations explicitly when you need custom context.

Log database errors at ERROR level with full context. Include the operation type, affected tables, and error details. Database errors need investigation, so include enough context to understand what failed.

### API Calls

Log API calls at DEBUG level with request details. Include the endpoint, method, and request parameters. This helps you understand API usage and troubleshoot integration issues.

Log API failures at WARNING level if you handle them gracefully, or ERROR level if they prevent functionality. Include the endpoint, status code, and error details. API failures often indicate external service issues that need monitoring.

Log API timeouts and connection errors at WARNING level. These are often transient and handled with retries or fallbacks. Include retry information and fallback behavior in your logs.

## Error Handling and Logging

### Exception Logging

Always log exceptions with full context. Include the operation that failed, relevant parameters, and exception details. Use `exc_info=True` to capture full stack traces. Without context, exception logs are useless for debugging.

Log exceptions at the appropriate level. Use WARNING for handled exceptions that don't prevent functionality. Use ERROR for exceptions that prevent normal operation. Use CRITICAL only for system-level failures.

Chain exception context properly. When you catch an exception and raise a new one, include the original exception in the log. This preserves the full error chain and makes debugging easier.

### Context Managers

Use context managers for operation logging. They automatically log operation start, completion, and failures. This ensures consistent logging across your codebase and reduces boilerplate.

Create context managers for complex operations that need detailed logging. They handle logging automatically, ensuring you don't forget to log important events. Context managers also ensure cleanup happens even when exceptions occur.

## Debugging Techniques

### Conditional Logging

Use conditional logging for expensive operations. Check the log level before computing expensive values for logging. This prevents performance issues from logging code.

Log detailed information only when needed. Use conditional checks to include verbose details only in DEBUG mode. This keeps production logs clean while providing detailed information during development.

### Log Filtering

Disable noisy modules during debugging. If a module produces too many logs, disable it and enable only the submodules you need. This helps focus on the logs you care about.

Enable specific modules when troubleshooting. Instead of enabling all DEBUG logs, enable only the modules you're investigating. This reduces log volume and makes debugging easier.

## Performance Considerations

### Avoid Expensive Operations

Don't do expensive computations in log statements. Logging should be fast—don't make it slow by computing expensive values. Pre-compute values before logging, or use conditional logging to compute them only when needed.

Use lazy evaluation for expensive log data. Only compute detailed information when the log level requires it. This prevents performance issues from logging code.

### Log Volume

Be mindful of log volume. Logging too much creates performance problems and makes logs harder to use. Log important events, not every operation. Use appropriate log levels to control verbosity.

In loops, log summaries instead of individual items. Log the total count and sample items, not every iteration. This keeps logs manageable while still providing useful information.

## Testing with Logging

### Testing Log Output

Test that your code logs appropriate messages. Use pytest's `caplog` fixture to capture and verify log output. This ensures your logging works correctly and provides useful information.

Verify log levels are appropriate. Ensure errors are logged at ERROR level, warnings at WARNING level, and so on. This ensures logs are categorized correctly for monitoring and alerting.

### Mocking Logs

Mock loggers in tests when you don't need to verify log output. This speeds up tests and prevents log noise during test execution. Only verify log output when logging behavior is part of what you're testing.

## Common Anti-Patterns

### Don't Log Sensitive Data

Never log passwords, tokens, API keys, or other sensitive information. Log user IDs and usernames, but not passwords or authentication tokens. Log operation types and parameters, but sanitize sensitive data first.

If you need to log data that might contain sensitive information, sanitize it first. Remove passwords, mask tokens, and exclude personal information. Log enough to understand what happened without exposing sensitive data.

### Don't Use Print Statements

Use logging instead of print statements. Print statements bypass log configuration and can't be filtered or redirected. They also don't include timestamps, log levels, or structured context.

Replace all print statements with appropriate log calls. Use DEBUG for development output, INFO for normal messages, and ERROR for error messages. This ensures consistent log formatting and proper log level control.

### Don't Log Without Context

Always include context in your logs. Log user IDs, command names, operation types, and relevant parameters. Without context, logs are useless for debugging. You can't understand what happened or why without context.

Include exception information when logging errors. Use `exc_info=True` to capture full stack traces. Include relevant parameters and operation context. This makes error logs useful for debugging.

### Don't Flood Logs

Avoid logging in tight loops. Log summaries instead of individual iterations. Use appropriate log levels to control verbosity. Too many logs make it hard to find important information.

Log important milestones, not every step. Log operation start and completion, not every intermediate step. Use DEBUG level for detailed execution flow, INFO level for important events.

## Configuration

### Development Setup

Set `LOG_LEVEL=DEBUG` in your `.env` file for development. This enables detailed logging that helps you understand what your code is doing. DEBUG logs include SQL queries, API calls, and detailed execution flow.

Use the `--debug` flag when starting the bot for even more verbose output. This enables DEBUG level logging without modifying your `.env` file. The `--debug` flag has the highest priority and will override any `LOG_LEVEL` setting in your `.env` file.

### Production Setup

Set `LOG_LEVEL=INFO` in production. INFO logs provide enough detail to understand bot behavior without overwhelming detail. They include important events and user actions without verbose debugging information.

Disable DEBUG logging in production. DEBUG logs are too verbose and can impact performance. They're also unnecessary for normal operation monitoring.

### Testing Setup

Use test-specific logging configuration for tests. This ensures tests don't produce excessive log output while still allowing you to verify logging behavior when needed.

Configure logging in test fixtures or setup functions. Set appropriate log levels for tests and disable noisy modules. This keeps test output clean while preserving logging functionality.

## Best Practices Summary

### Log Appropriately

Use the right log level for each situation. DEBUG for development details, INFO for normal operations, WARNING for potential issues, ERROR for failures, CRITICAL for system failures. Don't use ERROR for warnings or INFO for errors.

Include context in all logs. Log user IDs, command names, operation types, and relevant parameters. Without context, logs are useless for debugging and monitoring.

### Structure Your Logs

Use structured logging for operations you want to monitor. Structured logs make querying and analysis easier. Use consistent field names and formats across your application.

Log important events consistently. Use the same log format for similar operations. This makes logs easier to read and understand.

### Performance

Avoid expensive operations in logging code. Pre-compute values or use conditional logging. Don't let logging slow down your application.

Be mindful of log volume. Log important events, not every operation. Use appropriate log levels to control verbosity. Too many logs make it hard to find important information.

## Resources

- **Loguru Documentation**: Official loguru documentation covers all features and configuration options
- **Tux Logging Source**: See `src/tux/core/logging.py` for Tux's logging configuration
- **Structured Logging Guide**: Learn about structured logging patterns and best practices
- **Twelve-Factor App Logging**: Principles for logging in production applications
