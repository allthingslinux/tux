---
title: Starboard
description: Automatically highlight popular messages by reposting them to a dedicated starboard channel when they receive enough reactions.
tags:
  - user-guide
  - features
  - starboard
---

# Starboard

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The Starboard feature automatically highlights popular messages in your server by reposting them to a dedicated starboard channel when they receive enough reactions. This helps showcase high-quality content and celebrate community favorites.

## How It Works

When a message receives enough reactions using the configured starboard emoji:

1. **The message is posted** to your designated starboard channel
2. **The starboard message** includes the original content, author, and a jump link
3. **Reaction count updates** automatically as reactions are added or removed
4. **Messages are removed** from the starboard if reactions drop below the threshold

## Setting Up Starboard

### Prerequisites

Before setting up starboard, ensure:

- You have permission to configure Tux (typically rank 5+)
- You have a dedicated channel for the starboard
- Tux has permission to send messages in that channel

### Configuration Command

Use the `/starboard setup` command to configure starboard:

```text
/starboard setup channel:#starboard emoji:⭐ threshold:5
```

**Parameters:**

- **channel**: The text channel where starred messages will be posted
- **emoji**: The emoji to use for starring (must be a single default Discord emoji)
- **threshold**: Minimum number of reactions needed (must be at least 1)

### Example Setup

```text
/starboard setup channel:#best-of emoji:⭐ threshold:3
```

This configuration will:

- Post messages to `#best-of` channel
- Use ⭐ emoji for reactions
- Require at least 3 reactions to appear on starboard

## How Messages Get Starred

### Reaction Requirements

For a message to appear on the starboard:

- It must receive reactions equal to or greater than the configured threshold
- Reactions must use the exact emoji configured for starboard
- Self-reactions (author reacting to their own message) don't count and are automatically removed

### Automatic Updates

Starboard messages update automatically:

- **Reaction count** updates in real-time as reactions are added or removed
- **Messages are removed** from starboard if reactions drop below the threshold
- **Original content** is preserved even if the original message is edited

### What Gets Included

Each starboard message includes:

- **Original message content** (full text)
- **Author information** (name and avatar)
- **Reaction count** (displayed in footer)
- **Jump link** to the original message
- **First attachment** (if the original message had images)
- **Timestamp** of when the original message was posted

## Starboard Message Format

Starboard messages appear as embeds with:

```text
⭐ [Reaction Count]

[Original Message Content]

Author: @username
Source: [Jump to message]

[First attachment image, if present]
```

## Removing Starboard

To remove starboard configuration:

```text
/starboard remove
```

This will:

- Remove the starboard configuration
- Stop monitoring reactions for starboard
- **Note**: Existing starboard messages remain in the channel

## Behavior Details

### Self-Reactions

Authors cannot star their own messages:

- If an author reacts to their own message, the reaction is automatically removed
- Self-reactions don't count toward the threshold
- This prevents self-promotion and ensures genuine community appreciation

### Reaction Changes

The starboard responds to reaction changes:

- **Adding reactions**: Message appears or updates when threshold is reached
- **Removing reactions**: Message updates or is removed if below threshold
- **Clearing reactions**: Starboard message is deleted if all reactions are cleared

### Channel Restrictions

Starboard works in:

- Text channels
- Threads
- Forum channels
- Any messageable channel

Starboard messages are only posted to the configured starboard channel.

## Configuration Options

### Emoji Selection

**Requirements:**

- Must be a single default Discord emoji (Unicode)
- Custom emojis are not supported
- Common choices: ⭐, 💫, 🌟, ⚡, 🔥

**Examples:**

- `⭐` - Classic star (most common)
- `💫` - Dizzy star
- `🌟` - Glowing star
- `⚡` - Lightning bolt
- `🔥` - Fire

### Threshold Values

**Recommended thresholds:**

- **Small servers** (< 100 members): 2-3 reactions
- **Medium servers** (100-1000 members): 3-5 reactions
- **Large servers** (> 1000 members): 5-10 reactions

**Considerations:**

- Lower thresholds = more messages on starboard
- Higher thresholds = only exceptional content
- Start conservative and adjust based on activity

## Use Cases

### Highlighting Quality Content

Use starboard to showcase:

- Helpful answers and explanations
- Creative content and artwork
- Funny memes and jokes
- Important announcements
- Community achievements

### Community Engagement

Starboard encourages:

- **Quality posting** - Members strive to create content worth starring
- **Community recognition** - Popular content gets visibility
- **Content discovery** - Easy way to find best messages
- **Positive reinforcement** - Rewards good contributions

### Server Culture

Build community culture by:

- Celebrating helpful members
- Showcasing server highlights
- Creating a "best of" collection
- Encouraging positive interactions

## Tips

!!! tip "Choose the Right Threshold"
    Start with a threshold that matches your server size. You can always adjust it later if you find too many or too few messages are being starred.

!!! tip "Use a Dedicated Channel"
    Create a channel specifically for starboard to keep it organized and easy to browse. Consider naming it something like `#starboard`, `#best-of`, or `#highlights`.

!!! tip "Monitor Starboard Activity"
    Check your starboard regularly to see what content resonates with your community. This can help you understand what your members value.

!!! tip "Combine with Other Features"
    Starboard works great alongside:
    - XP system (reward starred messages)
    - Moderation (mods can manually star important messages)
    - Announcements (pin important starred messages)

!!! warning "Emoji Limitations"
    Only default Discord emojis work. Custom server emojis cannot be used for starboard. Make sure to choose an emoji that's easy to access and commonly used.

## Troubleshooting

### Messages Not Appearing on Starboard

If messages aren't appearing:

1. **Check threshold** - Ensure the message has enough reactions
2. **Verify emoji** - Make sure reactions use the exact configured emoji
3. **Check permissions** - Tux needs permission to send messages in starboard channel
4. **Verify configuration** - Run `/starboard setup` to check current settings

### Starboard Messages Not Updating

If reaction counts aren't updating:

1. **Check bot status** - Ensure Tux is online and functioning
2. **Verify permissions** - Tux needs permission to edit messages in starboard channel
3. **Check logs** - Look for error messages in bot logs

### Wrong Emoji Being Used

If the wrong emoji is configured:

1. **Remove starboard** - Use `/starboard remove`
2. **Reconfigure** - Use `/starboard setup` with the correct emoji
3. **Note**: Existing starboard messages won't be affected

## For Administrators

### Setup Best Practices

1. **Create dedicated channel** - Use a channel specifically for starboard
2. **Set appropriate permissions** - Allow members to react but restrict posting
3. **Choose accessible emoji** - Pick an emoji that's easy to find and use
4. **Start with moderate threshold** - Begin with 3-5 reactions and adjust

### Channel Configuration

Recommended starboard channel settings:

- **Read permissions**: Everyone can view
- **Send messages**: Only Tux can post
- **Add reactions**: Everyone can react
- **Manage messages**: Admins only (for cleanup if needed)

### Integration with Other Features

Starboard integrates well with:

- **XP System**: Consider giving bonus XP for starred messages
- **Moderation**: Mods can manually react to highlight important messages
- **Announcements**: Pin frequently starred messages for visibility

### Maintenance

Regular maintenance tasks:

- Review starboard channel periodically
- Adjust threshold if activity is too high/low
- Consider archiving old starboard messages
- Monitor for spam or inappropriate content
