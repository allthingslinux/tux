# Status Roles

Automatically assign roles based on Discord user status (online, idle, DND, offline).

## What Are Status Roles?

Status roles automatically:

- Assign roles when user's Discord status changes
- Remove roles when status changes back
- Work based on presence (online, idle, DND, streaming, etc.)
- Fully automatic - no user action needed

## How It Works

### Status Detection

Bot monitors user presence:

- **Online** - Green dot
- **Idle** - Yellow/away
- **Do Not Disturb (DND)** - Red
- **Offline** - Gray
- **Streaming** - Purple
- **Custom Status** - Can include text/emoji

### Automatic Role Assignment

When user's status changes:

1. Bot detects status change
2. Checks configured mappings
3. Adds appropriate role
4. Removes previous status role

### Example

Configuration:

- Online → @Active role
- Streaming → @Live role

User starts streaming → Gets @Live role → Shows they're live!

## Setup

### Configuration Required

Status roles must be configured by server administrators in the config file:

```toml
[status_roles]
mappings = [
    { status = "online", role_id = 123456789 },
    { status = "streaming", role_id = 987654321 },
]
```

### Available Statuses

- `online` - User is online
- `idle` - User is idle/away
- `dnd` - Do Not Disturb
- `offline` - User is offline
- `streaming` - User is streaming

## Use Cases

### Activity Indicators

Show who's active:

- @Active - Currently online
- @Away - Idle status
- @Busy - DND status

### Streamer Highlight

Promote streamers:

- @Live - Currently streaming
- Automatic highlight
- No manual role assignment needed

### Privacy Indicators

Respect user status:

- @DND - Don't ping me
- @Available - Open to chat

## Configuration

### For Self-Hosters

Edit `config.toml`:

```toml
[status_roles]
mappings = [
    { status = "online", role_id = 1234567890 },
    { status = "idle", role_id = 2345678901 },
    { status = "dnd", role_id = 3456789012 },
    { status = "streaming", role_id = 4567890123 },
]
```

**See:** [Admin Guide - Status Roles](../../admin-guide/configuration/features.md#status-roles)

## Best Practices

### Role Selection

✅ **Good uses:**

- Highlight streamers
- Show active members
- Visual server activity
- Organize by availability

❌ **Avoid:**

- Too many status roles (clutters role list)
- Roles with important permissions (security risk)
- Conflicting with other role systems

### Performance

- Keep mappings minimal
- Use for meaningful statuses
- Monitor role churn

## Limitations

- Bot must be online to detect status changes
- Brief delay in role updates
- Requires "Manage Roles" permission
- Bot role must be above status roles

## Tips

!!! tip "Streamer Promotion"
    Great for highlighting community streamers automatically!

!!! info "Automatic Management"
    Once configured, requires no maintenance - fully automatic!

!!! warning "Role Hierarchy"
    Ensure bot's role is above status roles in the role list!

## Troubleshooting

### Roles Not Applying

**Causes:**

- Bot offline
- Missing Manage Roles permission
- Bot role below status roles
- Configuration error

**Solutions:**

- Ensure bot is online
- Grant permission
- Adjust role hierarchy
- Verify configuration

### Roles Stuck

**Causes:**

- Bot was offline during status change
- User went invisible

**Solutions:**

- Wait for next status change
- Restart bot to resync

## Related Features

- **[Temp VC](temp-vc.md)** - Temporary voice channels
- **[XP System](xp-system.md)** - XP-based role rewards

---

**Next:** Learn about [GIF Limiter](gif-limiter.md) for content moderation.
