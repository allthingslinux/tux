---
title: Status Roles
description: Automatically assign roles to users based on their Discord custom status messages using regex pattern matching.
tags:
  - user-guide
  - features
  - roles
icon: lucide/badge
---

# Status Roles

Status Roles is an automated role management system that rewards or categorizes users based on
their Discord custom status. By using regular expression (regex) pattern matching, Tux can monitor
what users have set as their status and automatically assign or remove roles accordingly. This is
commonly used to reward users who support the community in their status or to indicate a user's
current activity (e.g., "Working", "Streaming").

The system is fully dynamic and responds instantly to status changes. It also performs a full server sweep upon bot startup to ensure all users have the correct roles based on their current status, providing a reliable and hands-off experience for administrators.

## How It Works

### Mechanics

Tux utilizes Discord's gateway events to monitor when a user's presence (specifically their custom status) changes.

- **Regex Matching:** The bot compares the text of a user's custom status against a list of pre-configured regex patterns.
- **Role Assignment:** If a match is found, Tux checks if the user already has the corresponding role. If not, it assigns it.
- **Role Removal:** If a user's status changes and no longer matches any configured pattern for a specific role they hold, Tux automatically removes that role.
- **Startup Sync:** On startup, Tux iterates through all members of configured servers to reconcile status roles.

### Automation

This feature provides seamless role automation:

- **Instant Response:** Roles are updated as soon as Discord notifies the bot of a presence change.
- **No Manual Cleanup:** Admins don't need to manually remove roles when users change their status.
- **Bot Protection:** To prevent issues, Tux automatically ignores other bot accounts for status role assignment.

### Triggers

The feature activates when:

- A user updates their Discord custom status.
- Tux starts up and performs its initial member sweep.

## User Experience

### What Users See

Status roles are completely transparent to the user:

- **Automatic Updates:** Users set their status in Discord as they normally would.
- **Visual Recognition:** If their status matches a pattern (e.g., containing ".atl.dev"), they will see the new role appear on their profile.
- **Role Loss:** If they remove or change the status, the role disappears just as quickly.

### Interaction

Users do not need to interact with Tux directly. They interact with the feature through their own Discord status settings.

## Configuration

Status Roles are configured through the server's `config.toml` file.

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `mappings` | `array` | A list of objects defining the role-to-status relationships. |
| `server_id` | `integer` | The ID of the Discord server where the mapping applies. |
| `role_id` | `integer` | The ID of the role to be managed. |
| `status_regex` | `string` | The regex pattern to match against the user's status. |

### Example Configuration

```toml
[status_roles]
mappings = [
    {
        server_id = 123456789012345678,
        role_id = 987654321098765432,
        status_regex = ".*tux.*"  # Matches any status containing "tux"
    },
    {
        server_id = 123456789012345678,
        role_id = 111222333444555666,
        status_regex = "^Working$"  # Matches only if status is exactly "Working"
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

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../admin/config/index.md).

## Permissions

### Bot Permissions

Tux requires the following permissions for this feature:

- **Manage Roles** - Needed to assign and remove roles from users.
- **View Server Members** - Needed to sweep the member list on startup.

### User Permissions

None required. All members are eligible for status roles based on the server's configuration.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: Roles are not being assigned to users

**Symptoms:**

- A user has a matching status but has not received the role.

**Causes:**

- Tux is missing the "Manage Roles" permission.
- Tux's role is lower in the hierarchy than the role it is trying to assign.
- The `server_id` or `role_id` in the configuration is incorrect.
- The regex pattern is invalid or does not match as expected.

**Solutions:**

1. Ensure Tux has "Manage Roles" permission.
2. Move Tux's role above the status roles in the server hierarchy.
3. Test your regex pattern using an online tool to ensure it matches the user's exact status.

### Issue: Roles are not being removed

**Symptoms:**

- A user changed their status but still has the status-related role.

**Causes:**

- The new status still matches the regex pattern (e.g., using `.*` too broadly).
- Tux did not receive the presence update event from Discord.

**Solutions:**

1. Refine your regex pattern to be more specific if necessary.
2. Check the bot's logs for any errors related to presence updates or permissions.

## Limitations

- **Custom Status Only:** Only the text in the "Custom Status" field is checked; "Playing", "Streaming", or "Listening" activities are ignored.
- **Bot Exemption:** Bots cannot receive status roles to avoid potential loops or unintended behavior.
- **Case Sensitivity:** By default, regex matching is case-insensitive unless the pattern explicitly handles it (e.g., `(?i)`).
- **One Server Scope:** Each mapping is tied to a specific `server_id`.

## Related Documentation

- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../../admin/config/commands.md)
