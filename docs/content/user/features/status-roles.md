---
title: Status Roles
description: Automatically assign roles to users based on their Discord custom status messages using regex pattern matching.
tags:
  - user-guide
  - features
  - roles
---

# Status Roles

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The Status Roles feature automatically assigns roles to users based on their Discord custom status messages. When a user's status matches a configured pattern, they receive the corresponding role. When their status changes and no longer matches, the role is automatically removed.

## How It Works

Status Roles monitors Discord custom status messages and matches them against configured regex patterns:

1. **User sets a custom status** in Discord (e.g., "Working on Tux bot")
2. **Tux checks the status** against all configured patterns
3. **If a pattern matches**, the user receives the corresponding role
4. **If status changes** and no longer matches, the role is removed
5. **All users are checked** when the bot starts up

## Key Features

### Automatic Role Management

- **Adds roles** when status matches a pattern
- **Removes roles** when status no longer matches
- **Updates in real-time** as users change their status
- **Checks all users** on bot startup

### Regex Pattern Matching

- **Case-insensitive** matching by default
- **Flexible patterns** using regex syntax
- **Empty status** treated as empty string for matching
- **Multiple patterns** can be configured per server

### Server-Specific Configuration

- Each mapping is tied to a specific server
- Different servers can have different rules
- Roles are only assigned in the configured server

## Configuration

Status Roles is configured through your server's configuration file.

### Configuration Format

Each mapping requires three fields:

- **`server_id`**: The Discord server (guild) ID
- **`role_id`**: The Discord role ID to assign
- **`status_regex`**: The regex pattern to match against custom status

### Example Configuration

```toml
[status_roles]
mappings = [
    {
        server_id = 123456789012345678,
        role_id = 987654321098765432,
        status_regex = ".*working.*"
    },
    {
        server_id = 123456789012345678,
        role_id = 111222333444555666,
        status_regex = "^Looking for"
    }
]
```

### Regex Pattern Examples

**Simple Text Match:**

```toml
status_regex = ".*linux.*"  # Matches any status containing "linux"
```

**Exact Match:**

```toml
status_regex = "^Working$"  # Matches only "Working" exactly
```

**Multiple Keywords:**

```toml
status_regex = ".*(working|busy|away).*"  # Matches any of these words
```

**Case-Insensitive:**

```toml
status_regex = ".*DEVELOPER.*"  # Case-insensitive by default
```

**Empty Status:**

```toml
status_regex = "^$"  # Matches users with no custom status
```

## How Status Matching Works

### Custom Status Detection

Tux checks for Discord custom status messages:

- **Custom Activity** status is extracted
- **Other activity types** (games, streaming) are ignored
- **No custom status** is treated as an empty string

### Pattern Matching Process

1. **Extract custom status** from user's activities
2. **Convert to lowercase** for case-insensitive matching
3. **Test against each configured pattern** for the server
4. **Add role** if pattern matches and user doesn't have it
5. **Remove role** if pattern doesn't match and user has it

### Real-Time Updates

Status changes are detected automatically:

- **On presence update** - When user changes their status
- **On bot startup** - All users are checked
- **Immediate application** - Roles added/removed instantly

## Use Cases

### Work Status Indicators

Assign roles based on work status:

```toml
status_regex = ".*working.*"     # "Working on project"
status_regex = ".*busy.*"        # "Busy right now"
status_regex = ".*available.*"   # "Available for help"
```

### Technology Stack

Identify users by their tech stack:

```toml
status_regex = ".*python.*"      # Python developers
status_regex = ".*rust.*"        # Rust developers
status_regex = ".*linux.*"       # Linux users
```

### Project Involvement

Track project involvement:

```toml
status_regex = ".*tux.*"         # Working on Tux
status_regex = ".*contributing.*" # Contributing to projects
```

### Availability Status

Show availability:

```toml
status_regex = ".*afk.*"         # Away from keyboard
status_regex = ".*back.*"        # Back online
status_regex = "^$"             # No status (available)
```

## Behavior Details

### Bot Users

Bot accounts are automatically excluded:

- Bots never receive status roles
- Only human users are processed
- Prevents accidental role assignment to bots

### Role Hierarchy

Important considerations:

- **Tux must have permission** to assign the role
- **Role must be below Tux's highest role** in hierarchy
- **Users must be in the server** for roles to be assigned

### Multiple Patterns

If multiple patterns match:

- **All matching roles** are assigned
- **Each pattern** is evaluated independently
- **Roles are removed** when patterns no longer match

### Status Changes

When a user changes their status:

- **Old status** is checked against patterns
- **New status** is checked against patterns
- **Roles are updated** based on matches
- **Changes are logged** for debugging

## Tips

!!! tip "Start Simple"
    Begin with simple patterns like `.*keyword.*` to match any status containing a keyword. You can refine patterns later.

!!! tip "Test Patterns"
    Test your regex patterns using online regex testers before adding them to configuration. Make sure they match what you expect.

!!! tip "Use Specific Patterns"
    More specific patterns reduce false matches. For example, `^Working on` is more specific than `.*working.*`.

!!! tip "Monitor Logs"
    Check Tux's logs to see when roles are added or removed. This helps verify your patterns are working correctly.

!!! tip "Consider Role Hierarchy"
    Make sure the roles you're assigning are positioned correctly in your server's role hierarchy. Tux can only assign roles below its own highest role.

!!! warning "Regex Complexity"
    Complex regex patterns can be hard to maintain. Keep patterns simple and well-documented. Invalid regex patterns will cause errors in logs.

!!! warning "Permission Requirements"
    Tux needs the "Manage Roles" permission and the role must be below Tux's highest role in the hierarchy. Without proper permissions, role assignment will fail silently.

## Troubleshooting

### Roles Not Being Assigned

If roles aren't being assigned:

1. **Check permissions** - Tux needs "Manage Roles" permission
2. **Verify role hierarchy** - Role must be below Tux's highest role
3. **Check server ID** - Ensure `server_id` matches your server
4. **Verify role ID** - Ensure `role_id` is correct
5. **Test regex pattern** - Use a regex tester to verify the pattern
6. **Check logs** - Look for error messages in Tux's logs

### Roles Not Being Removed

If roles aren't being removed:

1. **Check pattern** - Pattern might still be matching
2. **Verify status change** - User's status might not have actually changed
3. **Check logs** - Look for permission errors

### Invalid Regex Patterns

If you see regex errors in logs:

1. **Validate pattern** - Use a regex tester to find the issue
2. **Check syntax** - Ensure proper regex syntax
3. **Escape special characters** - Some characters need escaping
4. **Test incrementally** - Start with simple patterns and add complexity

### Multiple Roles Assigned

If users are getting multiple roles:

- **Check mappings** - Multiple patterns might be matching
- **Review patterns** - Patterns might be too broad
- **Consider exclusivity** - Use more specific patterns to avoid overlaps

## For Administrators

### Configuration Best Practices

1. **Document patterns** - Add comments explaining what each pattern matches
2. **Test thoroughly** - Test patterns with various status messages
3. **Monitor logs** - Watch for errors or unexpected behavior
4. **Start conservative** - Begin with simple patterns and expand

### Role Setup

Before configuring status roles:

1. **Create the roles** you want to assign
2. **Position roles** below Tux's highest role
3. **Set permissions** appropriately for each role
4. **Note role IDs** for configuration

### Server ID and Role ID

To find IDs:

- **Server ID**: Right-click server → Copy Server ID (Developer Mode must be enabled)
- **Role ID**: Right-click role → Copy Role ID (Developer Mode must be enabled)

### Pattern Design

Effective pattern design:

- **Be specific** - Avoid overly broad patterns
- **Use anchors** - `^` and `$` for exact matches
- **Group alternatives** - Use `(option1|option2)` for multiple options
- **Test edge cases** - Test with empty status, long status, special characters

### Monitoring

Regular monitoring tasks:

- **Review logs** for role assignment activity
- **Check role counts** to see how many users have each role
- **Gather feedback** from users about role assignments
- **Adjust patterns** based on usage and feedback
