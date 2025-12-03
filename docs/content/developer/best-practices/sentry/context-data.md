---
title: Context and Data
description: How to add tags, context, span data, scopes, and user information in Sentry
tags:
  - developer-guide
  - best-practices
  - sentry
---

# Context and Data

This guide shows you how to enrich Sentry events with tags, context, span data, scopes, and user information.

## Overview

- **Tags** - For filtering and searching (indexed, searchable)
- **Context** - Structured data for debugging (not searchable)
- **Span Data** - Context for specific spans in trace explorer
- **Scopes** - Isolated context for operations
- **Users** - User information (automatically set for commands)

## Tags

**Tags** are key/value pairs used for **filtering and searching** in Sentry. They're indexed and searchable.

### Tag Rules

- **Keys**: Max 32 characters, letters, numbers, underscores, periods, colons, dashes
- **Values**: Max 200 characters, no newlines
- **Purpose**: Filtering, grouping, and searching events

### Using Tags

```python
from tux.services.sentry import set_tag

# Set a tag for filtering
set_tag("feature", "moderation")
set_tag("guild_id", str(guild.id))
set_tag("command.success", True)
```

**Common Tags in Tux:**

- `command.name` - Command that was executed
- `command.success` - Whether command succeeded
- `command.error_type` - Type of error if command failed
- `error.type` - Category of error (database, api, cog, tux_error)
- `cog.name` - Cog where error occurred
- `setup_phase` - Current setup phase

### Tag Best Practices

✅ **Do:**

- Use tags for filtering and categorization
- Keep tag keys short and descriptive
- Use consistent tag naming across the codebase
- Use tags for high-level classification

❌ **Don't:**

- Use tags for detailed debugging data (use context instead)
- Include variable values like user IDs in tag keys (use tag values)
- Overwrite Sentry's automatic tags
- Use tags for large data structures

## Context

**Context** is structured data attached to events for debugging. Unlike tags, context is **not searchable** but provides rich detail when viewing an issue.

### Using Context

```python
from tux.services.sentry import set_context

# Set structured context
set_context("command", {
    "command": "moderation.ban",
    "guild_id": str(guild.id),
    "channel_id": str(channel.id),
    "args": ["user_id", "reason"],
})
```

**Common Context in Tux:**

- `command` - Command execution details (prefix commands)
- `interaction` - Interaction details (slash commands)
- `command_error` - Error details when command fails
- `database` - Database operation context
- `api_error` - API call context
- `cog_error` - Cog-related error context
- `tux_error` - Tux-specific error context

### Context Best Practices

✅ **Do:**

- Use context for detailed debugging information
- Structure context as objects with meaningful keys
- Include operation-specific details (query text, parameters, results)
- Use context for data that helps understand what happened

❌ **Don't:**

- Use context for filtering (use tags instead)
- Include sensitive data (passwords, tokens, API keys)
- Send extremely large data structures
- Use context for searchable data (use tags)

## Span Data

**Span Data** (`span.set_data()`) adds context to spans within transactions. This data appears in the trace explorer.

### Using Span Data

```python
from tux.services.sentry import start_span

with start_span("db.query", name="Fetch User") as span:
    user = await db.get_user(user_id)
    
    # Add context to this specific span
    span.set_data("db.table", "users")
    span.set_data("db.query_type", "SELECT")
    span.set_data("db.rows_returned", 1)
    span.set_data("db.user_id", user_id)
```

**When to use:**

- Operation-specific details (query text, row counts, file paths)
- Context for debugging specific operations
- Data that helps understand what happened in a particular span

## Scopes

**Scopes** manage event data isolation and context. The Sentry SDK uses a **scope stack** pattern with three types of scopes:

### Scope Stack Architecture

**Global Scope:**

- Default scope for the entire process
- Shared across all threads/async tasks
- Contains default tags, context, and user info
- Modified via `configure_scope()` (use sparingly)

**Isolation Scope:**

- Isolated scope for specific operations
- Manages concurrency isolation
- Used for background tasks and isolated operations
- Prevents context from leaking between concurrent operations

**Current Scope:**

- Active scope for current execution context
- Thread-local storage (isolated per thread/async task)
- Modified via `push_scope()` and `configure_scope()`
- Automatically restored when scope exits

### Scope Operations

**Push Scope** (`push_scope()`):
Creates a new isolated scope that doesn't affect parent scopes:

```python
import sentry_sdk

with sentry_sdk.push_scope() as scope:
    scope.set_tag("operation", "user_update")
    scope.set_context("user", {"user_id": user_id})
    sentry_sdk.capture_exception(error)
    # Scope automatically restored when exiting context
```

**Configure Scope** (`configure_scope()`):
Modifies the current scope (use with caution—affects all subsequent events):

```python
import sentry_sdk

def configure_scope(callback):
    scope = sentry_sdk.Scope.get_current_scope()
    callback(scope)
```

### Using Scopes in Tux

When capturing exceptions with specific context, Tux automatically creates a new scope:

```python
from tux.services.sentry import capture_exception_safe

# This automatically creates a new scope
capture_exception_safe(
    error,
    extra_context={"operation": "user_update", "user_id": user_id}
)
```

**Behind the scenes**, this uses `push_scope()`:

```python
import sentry_sdk

with sentry_sdk.push_scope() as scope:
    scope.set_context("extra", extra_context)
    scope.set_tag("error.captured_safely", True)
    sentry_sdk.capture_exception(error)
```

### Scope Isolation Example

Scopes prevent context from leaking between operations:

```python
import sentry_sdk

# Operation 1: Set context in isolated scope
with sentry_sdk.push_scope() as scope:
    scope.set_tag("operation", "user_update")
    scope.set_context("user", {"user_id": 123})
    # Capture error - includes user_update context
    sentry_sdk.capture_exception(error1)

# Operation 2: Different scope, no context leakage
with sentry_sdk.push_scope() as scope:
    scope.set_tag("operation", "guild_config")
    scope.set_context("guild", {"guild_id": 456})
    # Capture error - only includes guild_config context
    sentry_sdk.capture_exception(error2)
```

### Scope Best Practices

✅ **Do:**

- Use `push_scope()` for isolated error capture
- Use scoped context for operations that shouldn't affect subsequent events
- Set context early, before performing operations
- Let context managers handle scope restoration automatically

❌ **Don't:**

- Use `configure_scope()` for operation-specific context (use `push_scope()` instead)
- Set global context that should be operation-specific
- Modify scopes inside `push_scope()` using top-level APIs (use scope methods directly)
- Forget to restore scopes (context managers handle this automatically)

## Users

**Yes! Tux tracks users via Discord user IDs.** This enables powerful user-based analytics in Sentry, including user impact analysis, error grouping by user, and user-specific error tracking.

### Automatic User Tracking

User context is **automatically set for all commands** (both prefix and slash commands) by `SentryHandler`:

```python
# Automatically called by SentryHandler for every command
set_user_context(ctx.author)  # Prefix commands
set_user_context(interaction.user)  # Slash commands
```

### User Data Captured

**Primary Identifier:**

- `id` - **Discord user ID** (used as unique identifier in Sentry)

**User Information:**

- `username` - Discord username
- `display_name` - Display name (nickname or username)
- `bot` - Whether user is a bot
- `system` - Whether user is a system user

**Guild Context (if member):**

- `guild_id` - Guild ID
- `guild_name` - Guild name
- `guild_member_count` - Total members in guild
- `guild_permissions` - User's permissions value
- `top_role` - User's top role name
- `joined_at` - When user joined guild (ISO format)

### Benefits of User Tracking

With Discord user IDs as identifiers, you can:

✅ **Filter errors by user** - See all errors for a specific Discord user
✅ **User impact analysis** - See how many users are affected by an issue
✅ **User-based grouping** - Group errors by user to identify problematic users
✅ **User analytics** - Track error rates per user in Sentry Insights
✅ **User-specific debugging** - Understand what a specific user was doing when errors occurred

### Example: Viewing User Data in Sentry

When you view an error in Sentry, you'll see:

```text
User
├─ ID: 123456789012345678 (Discord user ID)
├─ Username: alice
├─ Display Name: Alice
├─ Bot: false
└─ Guild: My Server (guild_id: 987654321098765432)
```

You can then:

- Click on the user ID to see all their errors
- Filter issues by user ID
- See user impact metrics

### Manual User Context

If you need to set user context manually:

```python
from tux.services.sentry import set_user_context

set_user_context(ctx.author)
```

### User Best Practices

✅ **Do:**

- Let Tux automatically set user context (handled by `SentryHandler`)
- Include user context for all user-facing operations
- Use user IDs (not usernames) for identification

❌ **Don't:**

- Include sensitive user data (passwords, tokens)
- Set user context for background operations
- Overwrite user context unnecessarily

## Breadcrumbs

Breadcrumbs create a trail of events leading up to an error, providing context about what happened before the error occurred.

### Automatic Breadcrumbs

Tux uses **LoguruIntegration** to automatically capture logs as breadcrumbs:

- **All log levels** captured as breadcrumbs (DEBUG, INFO, WARNING, ERROR)
- **Structured data** from log messages included
- **Timestamps** and log levels preserved
- **Maximum 50 breadcrumbs** per event (configurable)

This means you rarely need to manually add breadcrumbs—your logs automatically become breadcrumbs!

### Breadcrumb Categories

Breadcrumbs are automatically categorized based on their source:

- **HTTP**: HTTP requests and responses
- **Database**: Database queries and operations
- **Navigation**: User actions and navigation
- **Console**: Log messages (via LoguruIntegration)
- **Custom**: Manually added breadcrumbs

### Manual Breadcrumbs

You can manually add breadcrumbs for custom events:

```python
import sentry_sdk

# Manually add a breadcrumb
sentry_sdk.add_breadcrumb(
    message="User authenticated",
    category="auth",
    level="info",
    data={"user_id": user_id, "method": "oauth"}
)
```

**When to use manual breadcrumbs:**

- Important events that aren't logged
- Custom operation milestones
- User actions that aren't captured by logs

**Note:** Tux primarily relies on Loguru integration for breadcrumbs. Manual breadcrumbs are rarely needed since logs are automatically captured as breadcrumbs.

## Common Patterns

### Pattern 1: Capturing Error with Context

```python
from tux.services.sentry import capture_exception_safe

try:
    await perform_operation()
except Exception as e:
    capture_exception_safe(
        e,
        extra_context={
            "operation": "user_update",
            "user_id": user_id,
            "guild_id": guild_id,
        }
    )
    raise
```

### Pattern 2: Setting Tags for Filtering

```python
from tux.services.sentry import set_tag

# Set tags for filtering
set_tag("feature", "moderation")
set_tag("guild_id", str(guild.id))
set_tag("operation", "ban_user")
```

### Pattern 3: Setting Context for Debugging

```python
from tux.services.sentry import set_context

# Set structured context
set_context("moderation", {
    "action": "ban",
    "target_user_id": str(target.id),
    "moderator_id": str(moderator.id),
    "reason": reason,
    "duration": duration,
})
```

### Pattern 4: Adding Span Data

```python
from tux.services.sentry import start_span

with start_span("db.query", name="Fetch User") as span:
    user = await db.get_user(user_id)
    
    # Add context to this span
    span.set_data("db.table", "users")
    span.set_data("db.operation", "SELECT")
    span.set_data("db.user_id", user_id)
    span.set_data("db.rows_returned", 1 if user else 0)
```

## Summary

- **Tags** - For filtering and searching (indexed, searchable)
- **Context** - For debugging details (not searchable, rich data)
- **Span Data** - For trace context (visible in trace explorer)
- **Scopes** - For isolated context (operation-specific)
- **Users** - Automatically set for commands
- **Breadcrumbs** - Automatic via Loguru integration

## Related Documentation

- [Choosing Instrumentation](./choosing-instrumentation.md) - When to use transactions/spans vs metrics
- [Transactions and Spans](./transactions-spans.md) - How to use transactions and spans
- [Metrics](./metrics.md) - Metrics implementation
