---
title: GIF Limiter
description: Automatically prevents GIF spam in Discord channels by rate limiting GIF messages.
tags:
  - user-guide
  - features
  - moderation
---

# GIF Limiter

Prevents GIF spam by rate limiting GIF messages in channels. Monitors messages and automatically deletes GIFs that exceed configured limits, with brief notifications explaining why messages were removed.

## How It Works

- Monitors all messages for GIF content (word "gif" + embeds)
- Tracks GIFs with timestamps for users and channels
- Automatically deletes GIFs exceeding limits
- Sends brief notification (auto-deletes after 3 seconds)
- Cleans up old timestamps every 20 seconds

## User Experience

- Post GIFs normally if within limits
- Messages deleted with notification if limits exceeded
- Wait for time window to reset before posting more GIFs

## Configuration

Configure through your server's configuration file.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `recent_gif_age` | `integer` | `60` | Time window in seconds for tracking GIFs |
| `gif_limits_user` | `object` | `{}` | Channel ID → max GIFs per user mapping |
| `gif_limits_channel` | `object` | `{}` | Channel ID → max GIFs per channel mapping |
| `gif_limit_exclude` | `array` | `[]` | Channel IDs to exclude from limits |

### Example Configuration

```toml
[gif_limiter]
recent_gif_age = 60
gif_limit_exclude = [123456789012345678]

[gif_limiter.gif_limits_user]
987654321098765432 = 2  # 2 GIFs per user per 60 seconds

[gif_limiter.gif_limits_channel]
987654321098765432 = 5  # 5 GIFs total per 60 seconds
```

## Commands

No commands - works automatically based on configuration.

## Permissions

**Bot Permissions:**

- Read Messages
- Manage Messages
- Send Messages

**User Permissions:** None required

## Troubleshooting

**GIFs not detected:**

- Ensure message contains "gif" (case-insensitive)
- Verify Discord is embedding the GIF link
- Check if channel is in exclude list

**Limits not working:**

- Verify Tux has "Manage Messages" permission
- Check configuration has limits set for the channel
- Restart Tux or reload configuration

## Limitations

- Only detects GIFs by checking for "gif" in message content with embeds
- Works with GIF links Discord embeds, may not catch all formats
- Limits based on rolling time window
- No per-server limits (only per-channel)
