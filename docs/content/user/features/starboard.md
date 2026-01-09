---
title: Starboard
description: Automatically highlight popular messages by reposting them to a dedicated starboard channel when they receive enough reactions.
tags:
  - user-guide
  - features
  - starboard
---

# Starboard

Automatically highlights popular messages by reposting them to a dedicated starboard channel when they receive enough reactions. Messages appear on the starboard when they reach the reaction threshold and are removed if reactions drop below the threshold.

## How It Works

- Monitors reactions on all messages across your server
- Posts messages to starboard channel when threshold is reached
- Self-reactions are automatically removed and don't count
- Starboard messages update in real-time as reactions change
- Messages removed from starboard if reactions drop below threshold

## User Experience

- React to messages with the configured starboard emoji (typically ⭐)
- Popular messages appear in the dedicated starboard channel with original content, author info, and jump link
- Reaction counts update automatically

## Configuration

Configure starboard using `/starboard setup` command.

| Option | Type | Description |
|--------|------|-------------|
| `channel` | `TextChannel` | Channel where starred messages are posted |
| `emoji` | `string` | Emoji to use for starring (default Discord emoji only) |
| `threshold` | `integer` | Minimum reactions needed (minimum 1) |

### Example Setup

```text
/starboard setup channel:#starboard emoji:⭐ threshold:5
```

## Commands

| Command | Description |
|---------|-------------|
| `/starboard setup` | Configure starboard channel, emoji, and threshold |
| `/starboard remove` | Remove starboard configuration |

## Permissions

**Bot Permissions:**

- Read Messages
- Send Messages  
- Embed Links
- Manage Messages
- Attach Files

**User Permissions:** None required (admins can configure)

## Troubleshooting

**Messages not appearing:**

- Check reaction count meets threshold
- Verify correct emoji is used
- Ensure Tux has permissions in starboard channel

**Messages not updating:**

- Verify Tux has "Manage Messages" permission
- Check bot is online and functioning

**Wrong emoji:**

- Remove starboard: `/starboard remove`
- Reconfigure with correct emoji

## Limitations

- Only default Discord emojis work (no custom server emojis)
- One emoji per server
- Must use text channel for starboard
- Removing starboard doesn't delete existing messages
