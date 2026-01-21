---
title: GIF Limiter
description: Automatically prevents GIF spam in Discord channels by rate limiting GIF messages.
tags:
  - user-guide
  - features
  - moderation
icon: lucide/scale
---

# GIF Limiter

The GIF Limiter is an automated moderation tool designed to maintain channel quality by preventing
GIF spam. It monitors message content in real-time and automatically removes GIFs that exceed your
server's configured limits, ensuring conversations remain readable and focused.

This feature works silently in the background, only intervening when specific thresholds are met. It provides brief, self-cleaning notifications to users when their messages are removed, explaining the reason for the action without cluttering the channel.

## How It Works

### Mechanics

Tux inspects all incoming messages for GIF content by checking for the word "gif" in the message body and the presence of Discord embeds.

- **Tracking:** Tux maintains a rolling timestamp of GIF messages for every user and channel.
- **Cleanup:** A background task runs every 20 seconds to prune expired timestamps, keeping memory usage low.
- **Detection:** The system identifies GIFs provided through links that Discord automatically embeds.

### Automation

This feature provides hands-off moderation:

- **Instant Deletion:** If a user or channel exceeds the GIF limit, Tux immediately deletes the offending message.
- **Self-Cleaning Alerts:** When a message is deleted, Tux sends a temporary notification that automatically deletes itself after 3 seconds.
- **Pattern Matching:** Tux monitors both message content and embed metadata to accurately identify GIFs.

### Triggers

The feature activates when:

- A message is sent that contains a GIF link or the word "gif".
- The number of GIFs sent within the `recent_gif_age` window exceeds the user or channel limit.

## User Experience

### What Users See

Under normal circumstances, users post GIFs without any interruption. However, when limits are exceeded:

- **Message Removal:** Their message containing the GIF is instantly removed.
- **Moderation Alert:** A brief message appears: "You are posting GIFs too fast! Please wait a moment."
- **Auto-Cleanup:** The alert message disappears after 3 seconds, leaving the channel clean.

### Interaction

Users do not need to interact with the bot to use this feature. They simply need to stay within the established limits for the channel.

## Configuration

The GIF Limiter is configured through the server's `config.json` file.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `RECENT_GIF_AGE` | `integer` | `60` | The time window (in seconds) during which GIFs are tracked. |
| `GIF_LIMITS_USER` | `object` | `{}` | A mapping of user IDs to the maximum GIFs that user may post in the window. |
| `GIF_LIMITS_CHANNEL` | `object` | `{}` | A mapping of channel IDs to the maximum GIFs allowed in that channel (total). |
| `GIF_LIMIT_EXCLUDE` | `array` | `[]` | A list of channel IDs where the GIF Limiter does not run. |

### Example Configuration

```json
{
  "GIF_LIMITER": {
    "RECENT_GIF_AGE": 60,
    "GIF_LIMIT_EXCLUDE": [123456789012345678],
    "GIF_LIMITS_USER": {
      "987654321098765432": 2
    },
    "GIF_LIMITS_CHANNEL": {
      "987654321098765432": 5
    }
  }
}
```

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../admin/config/index.md).

## Permissions

### Bot Permissions

Tux requires the following permissions for this feature:

- **Read Messages** - Needed to monitor channel activity for GIFs.
- **Manage Messages** - Needed to delete messages that exceed the limits.
- **Send Messages** - Needed to post the temporary moderation notifications.

### User Permissions

None required. All users are subject to the limits unless the channel is excluded.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: GIFs not being detected

**Symptoms:**

- Users are posting GIFs but they are not being counted against the limit.

**Causes:**

- The message does not contain the word "gif".
- Discord has not yet generated an embed for the GIF link.
- The channel is in the `GIF_LIMIT_EXCLUDE` list.

**Solutions:**

1. Check if the channel is in the exclude list in your configuration.
2. Verify that Tux has permission to view the channel and its embeds.

### Issue: Messages not being deleted

**Symptoms:**

- Tux sends a notification about the limit but the original message remains.

**Causes:**

- Tux is missing the "Manage Messages" permission in that channel.
- Tux's role is below the user's role in the hierarchy (for some Discord settings).

**Solutions:**

1. Ensure Tux has the "Manage Messages" permission.
2. Check that Tux's role is positioned correctly in the server's role settings.

## Limitations

- **Content-Based Detection:** Currently only detects GIFs by checking for "gif" in the message content along with embeds.
- **Rolling Window:** The limit is based on a fixed rolling time window, not a calendar period.
- **Per-Channel Logic:** Limits are applied per-channel; there is currently no global per-user limit across the entire server.

## Related Documentation

- [Moderation Module](../modules/moderation/index.md)
- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../admin/config/commands.md)
