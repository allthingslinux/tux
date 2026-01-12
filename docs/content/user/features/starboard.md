---
title: Starboard
description: Automatically highlight popular messages by reposting them to a dedicated starboard channel when they receive enough reactions.
tags:
  - user-guide
  - features
  - starboard
icon: lucide/star
---

# Starboard

The Starboard is a community-driven feature that highlights the best content in your server. When a
message receives a specific number of reactions (typically stars ⭐), Tux automatically reposts it to
a dedicated "starboard" channel. This creates a curated gallery of the most helpful, funny, or
memorable moments from across your entire server.

The feature is fully automated and updates in real-time. As reactions are added or removed, Tux adjusts the reaction count on the starboard post. If a message falls below the required threshold, it is automatically removed, ensuring only truly popular content remains highlighted.

## How It Works

### Mechanics

Tux monitors reaction events on every message in the server. It tracks which messages have reached the server's configured threshold for the designated starboard emoji.

- **Real-time Updates:** The starboard post's reaction count is updated immediately when a new star is added or removed.
- **Anti-Gaming:** Self-reactions from the message author are automatically ignored and do not count toward the threshold.
- **Content Preservation:** Tux clones the original message content, including text, images, and attachments, into a clean embed in the starboard channel.

### Automation

The system manages the starboard channel entirely without manual intervention:

- **Automatic Posting:** Messages are sent to the starboard as soon as they reach the reaction threshold.
- **Automatic Deletion:** If users remove their reactions and the count falls below the threshold, Tux deletes the starboard post.
- **Message Syncing:** Any changes to the original message's reaction count are reflected on the starboard post's embed.

### Triggers

The feature activates when:

- A message receives a reaction matching the configured starboard emoji.
- The total reaction count (excluding the author's own reaction) reaches the server's threshold.
- The reaction count falls below the threshold.

## User Experience

### What Users See

When a message becomes popular enough to be "starred":

- **Starboard Post:** A new post appears in the `#starboard` channel containing the original message, the author's name and avatar, and a link to the original channel.
- **Reaction Count:** The post includes a count of how many times it was starred.
- **Direct Link:** Users can click "Jump to Message" to see the original conversation in its full context.

### Interaction

Users interact with this feature by:

1. Reacting to any message with the configured emoji (default is ⭐).
2. Browsing the starboard channel to find high-quality content.
3. Adding their own stars to existing starboard posts to increase their visibility.

## Configuration

The Starboard is configured using the `/starboard setup` command.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `channel` | `TextChannel` | None | The channel where starred messages will be reposted. |
| `emoji` | `string` | `⭐` | The emoji users must use to star a message. |
| `threshold` | `integer` | `3` | The minimum number of reactions required to reach the starboard. |

### Example Setup

```bash
/starboard setup channel:#starboard emoji:⭐ threshold:5
```

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../admin/config/index.md).

## Commands

This feature provides the following management commands:

| Command | Description |
|---------|-------------|
| `/starboard setup` | Configure the starboard channel, emoji, and threshold. |
| `/starboard remove` | Remove the starboard configuration from the server. |

## Permissions

### Bot Permissions

Tux requires the following permissions for this feature:

- **Read Message History** - Needed to fetch the content of starred messages.
- **Send Messages** - Needed to post to the starboard channel.
- **Embed Links** - Needed to create the formatted starboard posts.
- **Manage Messages** - Needed to remove posts if they fall below the threshold.
- **Attach Files** - Needed to forward attachments to the starboard.

### User Permissions

None required for starring messages. Only administrators can use the setup commands.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Troubleshooting

### Issue: Messages are not appearing on the Starboard

**Symptoms:**

- A message has many stars but hasn't been posted to the starboard channel.

**Causes:**

- The author's self-reaction is being counted in the UI but ignored by Tux.
- Tux does not have "Send Messages" or "Embed Links" permission in the starboard channel.
- The threshold is set higher than you think.

**Solutions:**

1. Check if the reaction count meets the threshold *excluding* the author.
2. Verify Tux's permissions in the starboard channel.
3. Use `/starboard setup` to check or update the current threshold.

### Issue: Starboard posts are not updating

**Symptoms:**

- People are adding stars but the count on the starboard post remains the same.

**Causes:**

- Tux is missing the "Manage Messages" permission.
- The bot is experiencing a temporary connection issue with Discord.

**Solutions:**

1. Ensure Tux has "Manage Messages" permission in the starboard channel.
2. Check if the bot is online and responsive to other commands.

## Limitations

- **Emoji Types:** Currently only supports default Discord emojis; custom server emojis cannot be used for the starboard.
- **Single Channel:** Only one starboard channel can be configured per server.
- **Historical Content:** Starring very old messages may not work if Tux cannot retrieve them from Discord's history.

## Related Documentation

- [Admin Configuration Guide](../../admin/config/index.md)
- [Permission Configuration](../../../admin/config/commands.md)
