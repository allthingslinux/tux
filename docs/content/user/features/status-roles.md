---
title: Status Roles
description: Automatically assign roles to users based on their Discord custom status messages using regex pattern matching.
tags:
  - user-guide
  - features
  - roles
---

# Status Roles

Automatically assigns roles based on Discord custom status messages using regex pattern matching. When a user's status matches a configured pattern, they receive the corresponding role. When their status changes and no longer matches, the role is automatically removed.

## How It Works

- Monitors Discord custom status messages for all users
- Checks status against configured regex patterns
- Assigns roles when patterns match
- Removes roles when status changes and no longer matches
- All users checked on bot startup

## User Experience

- Set Discord custom status normally
- Roles assigned automatically when status matches patterns
- Roles removed automatically when status changes
- No commands needed

## Configuration

Configure through your server's configuration file.

| Option | Type | Description |
|--------|------|-------------|
| `mappings` | `array` | List of status role mappings |
| `server_id` | `integer` | Discord server (guild) ID |
| `role_id` | `integer` | Discord role ID to assign |
| `status_regex` | `string` | Regex pattern to match against custom status |

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
        status_regex = ".*linux.*"
    }
]
```

### Regex Pattern Examples

```toml
status_regex = ".*linux.*"              # Contains "linux"
status_regex = "^Working$"              # Exactly "Working"
status_regex = ".*(working|busy).*"     # Contains "working" OR "busy"
status_regex = "^$"                     # Empty status
```

## Commands

No commands - works automatically based on configuration.

## Permissions

**Bot Permissions:**

- Manage Roles
- View Server Members

**User Permissions:** None required

## Troubleshooting

**Roles not assigned:**

- Verify Tux has "Manage Roles" permission
- Check role hierarchy (roles must be below Tux's highest role)
- Ensure server_id and role_id are correct
- Test regex pattern with online regex tester

**Roles not removed:**

- Check if pattern still matches new status
- Verify user's status actually changed
- Check bot logs for permission errors

**Invalid regex patterns:**

- Validate pattern using regex tester
- Check regex syntax
- Escape special characters if needed

## Limitations

- Only Discord custom status is checked (not games/streaming)
- Bot accounts never receive status roles
- Roles must be below Tux's highest role
- Case-insensitive matching only
- One role per pattern mapping
