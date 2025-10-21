# Bookmarks

Save messages for later with personal bookmarks using reactions.

## What Are Bookmarks?

Bookmarks allow you to:

- Save important messages for personal reference
- Receive saved messages in your DMs
- Keep a personal collection of helpful content
- Access original messages via jump links

## How Bookmarks Work

Bookmarks are **reaction-based** - no commands needed!

### Adding a Bookmark

To bookmark a message:

1. **React with 🔖** (bookmark emoji) to any message
2. Bot DMs you a copy of the message
3. DM includes:
   - Original message content
   - Author information
   - Link to jump to original
   - Attached images/files (up to 10)
   - Timestamp and channel info

**Example:**

```
Someone posts helpful Linux advice
↓
React with 🔖
↓
Bot sends you a DM with the message!
```

### Removing a Bookmark

To remove a bookmark:

1. Go to your DMs with the bot
2. Find the bookmarked message
3. **React with 🗑️** (trash emoji) on the bookmark DM
4. Bot deletes the bookmark message

## Privacy & Storage

**Important:**

- Bookmarks are sent to your **DMs** (private)
- **Not stored in database** - exists only as DM messages
- Only you can see your bookmarks
- No centralized list or management
- Unlimited bookmarks (limited only by DM history)

## Permissions

**Permission:** Rank 0 (Everyone)

No special permissions needed - anyone can bookmark messages they can see.

## Use Cases

### Knowledge Management

Bookmark:

- Helpful tutorials or guides
- Important announcements
- Useful commands or syntax
- Reference documentation
- Code snippets

### Task Tracking

Bookmark:

- Messages to follow up on
- Questions to answer later
- Pending discussions
- Action items

### Personal Collection

Bookmark:

- Memorable conversations
- Funny moments
- Great advice
- Interesting links
- Resources to read

## How It's Different from Other Features

### vs. Snippets

- **Bookmarks:** Personal, reaction-based, DM'd
- **Snippets:** Server-wide, command-based, shared

### vs. Starboard

- **Bookmarks:** Personal saves (just you)
- **Starboard:** Community highlights (everyone sees)

### vs. Discord "Save Message"

- **Bookmarks:** Rich embed with jump link, includes images
- **Discord Save:** Just a reference in saved messages

## Tips

!!! tip "React to Bookmark"
    Just react with 🔖 - that's it! No commands needed.

!!! tip "Check Your DMs"
    Bookmarks go to your DMs with the bot. Make sure you have DMs enabled!

!!! tip "Jump Links Work Forever"
    As long as the original message exists and you have channel access, the jump link works!

!!! tip "Includes Attachments"
    Images and files are copied to your bookmark (up to 10 files).

!!! warning "DMs Must Be Enabled"
    You must allow DMs from server members for bookmarks to work!

## Emojis Used

- **🔖 (Bookmark)** - Add bookmark
- **🗑️ (Trash)** - Remove bookmark (in DMs only)

## Troubleshooting

### Not Receiving Bookmark DMs

**Causes:**

- DMs disabled from server members
- Bot can't DM you
- You blocked the bot

**Solutions:**

1. Enable DMs: **User Settings** → **Privacy & Safety** → **Allow direct messages from server members**
2. Check you haven't blocked the bot
3. Verify bot is online

When DMs fail, bot sends a notice in the channel.

### Bookmark Not Working

**Causes:**

- Wrong emoji (must be 🔖)
- Bot offline
- Message in unsupported channel

**Solutions:**

- Use the exact 🔖 emoji
- Check bot status
- Try in a different channel

### Can't Remove Bookmark

**Causes:**

- Not reacting in your DMs
- Wrong emoji
- Not the bot's bookmark message

**Solutions:**

- Must react 🗑️ on the bookmark DM (not original message)
- Use trash emoji 🗑️
- Only works on bookmarks sent by the bot

### Bookmark Missing Images

**Causes:**

- More than 10 attachments (limit)
- Attachment deleted from original
- Attachment too large

**Solutions:**

- Discord limits to 10 files per message
- Images must exist when bookmarking
- Check Discord file size limits

## Limitations

- **No command interface** - Reaction-based only
- **No centralized list** - Bookmarks are just DM messages
- **No search function** - Scroll through DMs
- **Requires DMs** - Must allow DMs from server
- **10 file limit** - Discord limitation
- **No database** - If you delete DMs, bookmarks are gone

## Best Practices

### Organization

Since bookmarks are just DMs:

- Scroll through DMs to find bookmarks
- Use Discord's search in DMs (Ctrl+F)
- Clear old bookmarks regularly (react 🗑️)
- Don't over-bookmark (DM clutter)

### What to Bookmark

✅ **Good for bookmarking:**

- Important information you'll need later
- Helpful guides or tutorials
- Complex commands or code
- Links to check later
- Reference material

❌ **Don't bookmark:**

- Everything (DM overload)
- Memes (unless truly memorable)
- Temporary information
- Things you could search for

## Security & Privacy

- **Private** - Only you see your bookmarks
- **No logs** - Not stored in Tux database
- **Jump links** - Link to original (requires channel access)
- **DM-based** - If you lose DM access to bot, bookmarks remain in DM history

## Related Features

- **[Snippets](../commands/snippets.md)** - Server-wide reusable text
- **[Starboard](starboard.md)** - Community-highlighted messages
- **[Info Commands](../commands/info.md)** - Message information

---

**Next:** Learn about [Temporary Voice Channels](temp-vc.md).
