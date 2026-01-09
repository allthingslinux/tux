---
title: Temp VC
description: Automatically create and manage temporary voice channels for users when they join a designated template channel.
tags:
  - user-guide
  - features
  - voice-channels
---

# Temp VC

Automatically creates temporary voice channels when users join a designated template channel. Channels are named `/tmp/[username]` and automatically deleted when empty. If a channel already exists for you, you're moved to the existing one instead of creating a new one.

## How It Works

- Monitors when users join the configured template voice channel
- Creates new channel by cloning template with custom name
- Moves user automatically to their temporary channel
- Reuses existing channels instead of creating duplicates
- Automatically deletes empty channels

## User Experience

- Join the designated template channel
- Get automatically moved to your own channel named `/tmp/[username]`
- If you already have a channel, you're moved to it
- Channel deleted automatically when empty

## Configuration

Configure through your server's configuration file.

| Option | Type | Description |
|--------|------|-------------|
| `tempvc_channel_id` | `string` | Template voice channel ID users join |
| `tempvc_category_id` | `string` | Category ID where temp channels are created |

### Example Configuration

```toml
[temp_vc]
tempvc_channel_id = "123456789012345678"
tempvc_category_id = "987654321098765432"
```

### Setup Steps

1. Create a category for temporary voice channels
2. Create a template voice channel in that category
3. Configure permissions on template channel (cloned to temp channels)
4. Get channel and category IDs (enable Developer Mode)
5. Add configuration to `config.toml`
6. Restart Tux

## Commands

No commands - works automatically based on configuration.

## Permissions

**Bot Permissions:**

- Manage Channels
- Move Members
- Connect
- View Channel

**User Permissions:** None required

## Troubleshooting

**Channels not created:**

- Verify channel and category IDs are correct
- Check Tux has "Manage Channels" and "Move Members" permissions
- Ensure category exists and is accessible

**Channels not deleted:**

- Verify channel name starts with `/tmp/`
- Check channel is in configured category
- Ensure channel is actually empty

**Users not moved:**

- Verify Tux has "Move Members" permission
- Check user joined correct template channel
- Ensure Tux's role is above users' roles

## Limitations

- Discord voice channel limits (50 per server, 200 with Nitro)
- Channels must follow `/tmp/[username]` naming pattern
- One channel per user (reuses existing)
- Template channel settings are cloned to temp channels
- Temp channels must be in configured category
