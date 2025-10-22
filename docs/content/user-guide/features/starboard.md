# Starboard

The starboard highlights popular messages by reposting them to a dedicated channel when they receive enough reactions.

## What is Starboard?

Starboard is a feature that:

- Automatically reposts popular messages
- Requires a threshold of reactions (configured emoji)
- Creates a "best of" channel
- Celebrates great content
- Engages the community

## How It Works

### 1. User Reacts with Configured Emoji

When users find a great message, they react with the configured emoji (typically ⭐).

### 2. Threshold Reached

Once the configured threshold is reached (e.g., 3 stars), the message is posted to the starboard channel.

### 3. Starboard Post Created

The bot creates a special embed in the starboard channel showing:

- Original message content
- Who sent it
- How many reactions it has
- Link to original message
- Attachments/images (if any)

### 4. Updates Automatically

As more users add/remove reactions:

- Reaction count updates in starboard
- If reactions drop below threshold, post may be removed

## Setup

### Prerequisites

1. **Starboard channel** - Create a channel like #starboard
2. **Choose emoji** - Usually ⭐ (star)
3. **Decide threshold** - How many reactions needed

### Quick Setup

#### Option 1: Config Wizard (Recommended)

```
/config wizard
```

Follow the prompts to set up starboard.

#### Option 2: Manual Setup

```
/starboard setup #starboard ⭐ 3
```

**Parameters:**

- `channel` (#starboard) - Where to post starred messages
- `emoji` (⭐) - Which emoji triggers starboard
- `threshold` (3) - Number of reactions required

## Commands

Starboard management commands:

### Setup

Configure or update starboard settings.

```
/starboard setup #channel ⭐ 3
```

**Parameters:**

- `channel` (required) - Starboard channel
- `emoji` (required) - Trigger emoji (must be single default Discord emoji)
- `threshold` (required) - Reactions needed (minimum 1)

**Permission:** Requires appropriate permission rank

**Notes:**

- Run again to update settings
- Emoji must be a single printable character
- Threshold must be at least 1
- Bot needs Send Messages permission in channel

### Remove

Remove starboard configuration.

```
/starboard remove
```

**Permission:** Requires appropriate permission rank

**Notes:**

- Deletes all starboard configuration
- Existing starboard posts remain
- Can set up again later with `/starboard setup`

## Usage

### For Users

Just react with the configured emoji (usually ⭐) to messages you like!

```
Someone posts a great explanation
↓
React with ⭐
↓
Others also star it
↓
Appears in #starboard when threshold reached!
```

### Star Threshold

Typical thresholds:

- **Small servers (< 50 members):** 2-3 stars
- **Medium servers (50-500):** 3-5 stars
- **Large servers (500+):** 5-10 stars

Choose based on your server size and activity level.

## Starboard Posts

### What Gets Posted

- Message content (text)
- Embeds (if present)
- Images/attachments
- Author information
- Reaction count
- Link to original

### What Doesn't Get Posted

- Messages below threshold
- System messages
- Messages that can't be accessed

### Starboard Embed Format

```
⭐ 5 | #general

[Message content here]

— Author Name
[Link to message] | Posted timestamp
```

## Best Practices

### Threshold Selection

✅ **Good thresholds:**

- High enough to be meaningful
- Low enough to be achievable
- Based on server activity level
- Adjusted over time

❌ **Avoid:**

- Threshold = 1 (every message)
- Threshold too high (nothing gets starred)
- Never adjusting as server grows

### Channel Placement

- Create dedicated #starboard channel
- Make it public (everyone can view)
- Consider read-only (only bot can post)
- Pin introduction message explaining starboard

### Emoji Choice

- **⭐ (Star)** - Most common, intuitive
- **💖 (Heart)** - For positive content
- **🏆 (Trophy)** - For achievements
- Any single default Discord emoji works

### Community Guidelines

- Encourage starring quality content
- Discourage star begging
- Moderate inappropriate starred content
- Celebrate diverse types of content (helpful, funny, creative)

## Tips

!!! tip "Organic Growth"
    Let starboard grow naturally - don't force it. Quality content will naturally get stars.

!!! tip "Multiple Reactions"
    Users can un-star and re-star. The count updates live!

!!! tip "Celebrate Diversity"
    Encourage starring different types of content: helpful answers, funny jokes, creative works.

!!! warning "Moderation Still Applies"
    Starred messages can still violate rules. Moderators can delete starboard posts if needed.

!!! info "Emoji Requirement"
    The emoji parameter must be a single default Discord emoji (⭐, 💖, 🏆, etc.). Custom emojis are not supported in the current implementation.

## Troubleshooting

### Message Not Appearing in Starboard

**Causes:**

- Not enough reactions yet
- Threshold not met
- Starboard not configured
- Wrong emoji (must match configured emoji)

**Solutions:**

- Check threshold and current reaction count
- Verify starboard is configured
- Check channel exists and bot can post there
- Ensure using the correct emoji

### Can't Set Up Starboard

**Cause:** Missing permissions or invalid parameters

**Solutions:**

- Must have appropriate permission rank
- Emoji must be single character
- Threshold must be ≥ 1
- Bot needs Send Messages in starboard channel

### "Invalid Emoji" Error

**Cause:** Emoji parameter is invalid

**Solution:**

- Use a single default Discord emoji
- Not multi-character emojis
- Not custom server emojis
- Examples that work: ⭐, 💖, 🏆, 👍

### Starboard Posts Not Updating

**Causes:**

- Bot offline
- Permission issues
- Database error

**Solutions:**

- Check bot status
- Verify bot has "Send Messages" in starboard channel
- Check logs for errors

## Configuration

### For Self-Hosters

Starboard is configured via commands (stored in database), not config files.

Use the `/starboard setup` command to configure.

## Related Commands

- **[Bookmarks](bookmarks.md)** - Personal message saving
- **[Info Commands](../commands/info.md)** - Message information

---

**Next:** Learn about [Bookmarks](bookmarks.md) for personal message management.
