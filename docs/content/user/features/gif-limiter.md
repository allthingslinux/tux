---
title: GIF Limiter
description: Automatically prevents GIF spam in Discord channels by rate limiting GIF messages.
tags:
  - user-guide
  - features
  - moderation
---

# GIF Limiter

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The GIF Limiter feature automatically prevents GIF spam in Discord channels by rate limiting GIF messages. This helps maintain conversation quality and prevents channels from being flooded with animated images.

## How It Works

The GIF Limiter monitors all messages in your server and automatically detects GIFs. When a GIF is detected, the system checks if it exceeds configured limits:

- **Channel-wide limits**: Maximum number of GIFs allowed in a channel within a time window
- **Per-user limits**: Maximum number of GIFs a single user can post in a channel within a time window

If a GIF exceeds either limit, the message is automatically deleted and a temporary notification is sent explaining why it was removed.

## Detection

The GIF Limiter detects GIFs by checking if:

- The message contains the word "gif" (case-insensitive)
- The message has embeds (Discord automatically embeds GIF links)

!!! note "Detection Method"
    The limiter checks message content for the word "gif" and requires embeds. This means it works with:

    - Direct GIF links (e.g., `https://example.com/image.gif`)
    - GIF attachments
    - Messages mentioning GIFs that Discord embeds

## Rate Limiting

### Time Window

GIFs are tracked within a configurable time window (default: 60 seconds). Only GIFs sent within this window count toward the limits. Older GIFs are automatically removed from tracking every 20 seconds.

### Limit Types

#### Channel-Wide Limits

Prevents too many GIFs from being posted in a specific channel, regardless of who posts them. Useful for maintaining conversation quality in busy channels.

**Example**: If a channel has a limit of 5 GIFs per 60 seconds, only the first 5 GIFs posted in that channel within any 60-second window will be allowed.

#### Per-User Limits

Prevents individual users from spamming GIFs in specific channels. Each user's GIF count is tracked separately.

**Example**: If a channel has a per-user limit of 2 GIFs per 60 seconds, each user can only post 2 GIFs in that channel within any 60-second window.

### Excluded Channels

You can configure certain channels to be excluded from GIF limiting entirely. GIFs posted in excluded channels are not tracked or limited.

## Configuration

The GIF Limiter is configured through your server's configuration file.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `recent_gif_age` | `integer` | `60` | Time window in seconds for tracking GIFs |
| `gif_limits_user` | `object` | `{}` | Channel ID → max GIFs per user mapping |
| `gif_limits_channel` | `object` | `{}` | Channel ID → max GIFs per channel mapping |
| `gif_limit_exclude` | `array` | `[]` | List of channel IDs to exclude from limits |

### Example Configuration

    ```toml
    [gif_limiter]
    # Track GIFs for 60 seconds
    recent_gif_age = 60

    # Exclude GIFs from moderation channels
    gif_limit_exclude = [123456789012345678]

    [gif_limiter.gif_limits_user]
    # Allow 2 GIFs per user per 60 seconds in general chat
    987654321098765432 = 2

    [gif_limiter.gif_limits_channel]
    # Allow maximum 5 GIFs total per 60 seconds in general chat
    987654321098765432 = 5
    ```

## Behavior

### When Limits Are Exceeded

When a GIF exceeds a configured limit:

1. The message is immediately deleted
2. A temporary notification is sent: `-# GIF ratelimit exceeded for channel` or `-# GIF ratelimit exceeded for user`
3. The notification automatically deletes after 3 seconds

### Automatic Cleanup

The system automatically cleans up old GIF timestamps every 20 seconds. This ensures that:

- Only recent GIFs count toward limits
- Memory usage stays reasonable
- Limits reset after the time window expires

## Use Cases

### Preventing Spam

Configure per-user limits in busy channels to prevent individual users from flooding the channel with GIFs.

### Maintaining Conversation Quality

Set channel-wide limits to ensure GIFs don't dominate conversations in text channels.

### Channel-Specific Rules

Different channels can have different limits. For example:

- General chat: 3 GIFs per user, 10 total per channel
- Media channel: No limits (excluded)
- Serious discussion: 1 GIF per user, 3 total per channel

## Tips

!!! tip "Start Conservative"
    Begin with lower limits and adjust based on your server's needs. You can always increase limits if they're too restrictive.

!!! tip "Exclude Media Channels"
    Consider excluding dedicated media or meme channels from GIF limits, as these channels are designed for sharing images and GIFs.

!!! tip "Monitor and Adjust"
    Watch how the limits affect your community and adjust the time window and limits accordingly. Different communities have different GIF posting patterns.

## For Administrators

See the admin configuration documentation for detailed setup instructions and advanced configuration options.
