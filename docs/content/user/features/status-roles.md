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

Status Roles are configured through the server's `config.json` file.

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `MAPPINGS` | `array` | A list of objects with `status` and `role_id`. Each `status` is a regex or string to match against the user's custom status. |

Each mapping object:

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Regex or literal string to match against the user's Discord custom status. |
| `role_id` | `integer` | The role to assign when the status matches. |

### Example Configuration

```json
{
  "STATUS_ROLES": {
    "MAPPINGS": [
      { "status": ".*tux.*", "role_id": 987654321098765432 },
      { "status": "^Working$", "role_id": 111222333444555666 }
    ]
  }
}
```

### Regex Pattern Examples

| Pattern | Matches |
|---------|---------|
| `".*linux.*"` | Status contains "linux" |
| `"^Working$"` | Status is exactly "Working" |
| `".*(working\|busy).*"` | Status contains "working" or "busy" |
| `"^$"` | Empty status |

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
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: Roles are not being assigned to users

**Symptoms:**

- A user has a matching status but has not received the role.

**Causes:**

- Tux is missing the "Manage Roles" permission.
- Tux's role is lower in the hierarchy than the role it is trying to assign.
- The `role_id` in a `MAPPINGS` entry is incorrect.
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
- **Server-scoped:** Status role mappings apply only within the guild where the config is used.

## Related Documentation

- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../admin/config/commands.md)
