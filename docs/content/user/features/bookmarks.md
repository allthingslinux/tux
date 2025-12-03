---
title: Bookmarks
tags:
  - user-guide
  - features
  - bookmarks
---

# Bookmarks

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

The Bookmarks feature allows you to save important Discord messages for later reference. Simply react to any message with the bookmark emoji, and Tux will send a copy of that message directly to your DMs, complete with all attachments, images, and context.

## How It Works

Bookmarking a message is as simple as adding a reaction:

1. **React with 🔖** on any message you want to save
2. **Tux sends you a DM** with a formatted copy of the message
3. **Access your bookmarks** anytime in your DMs
4. **Remove bookmarks** by reacting with 🗑️ on the bookmark message in your DMs

## Using Bookmarks

### Bookmarking a Message

To bookmark a message:

1. Find a message you want to save
2. React to it with the 🔖 emoji
3. Check your DMs - Tux will send you the bookmarked message

The bookmark includes:

- Full message content
- Author information
- All attachments (up to 10 images)
- Stickers
- Jump link to the original message
- Channel and server context
- Timestamp

### Removing a Bookmark

To remove a bookmark from your DMs:

1. Open the bookmark message in your DMs
2. React with the 🗑️ emoji
3. The bookmark message will be deleted

!!! note "Removal Location"
    You can only remove bookmarks by reacting in your DMs. Reacting with 🗑️ on messages in servers won't remove bookmarks - this prevents accidental deletions.

## What Gets Bookmarked

### Message Content

The full text content of the message is included in the bookmark. If the message is too long, it will be truncated to fit Discord's embed limits.

### Attachments

All image attachments from the original message are included in the bookmark (up to 10 images). Non-image attachments are listed as links in the embed.

### Stickers

Stickers are included as images in the bookmark when possible. PNG and APNG format stickers are converted to image files.

### Embeds

If the original message contains embeds, the bookmark will note this. Embedded images are extracted and included as attachments when possible.

### Context Information

Each bookmark includes:

- **Author**: Who posted the original message
- **Jump Link**: Direct link to view the original message in context
- **Reply Reference**: If the message was a reply, a link to the original message
- **Location**: Channel name and server name
- **Timestamp**: When the message was originally posted

## Example Bookmark

When you bookmark a message, you'll receive a DM that looks like this:

```text
📌 Message Bookmarked

[Message content here]

Author: @username
Jump to Message: [Click Here]
Attachments: [filename.png]
In #general on Server Name
[Timestamp]
```

## Privacy & Permissions

### Direct Messages

Bookmarks are sent to your DMs, so you need to have DMs enabled with Tux. If you have DMs disabled:

- Tux will attempt to send the bookmark
- If it fails, you'll see a notification in the channel (deleted after 30 seconds)
- Enable DMs in your Discord privacy settings to receive bookmarks

### Server Permissions

You can bookmark messages in any channel you have access to, regardless of your server permissions. The bookmark feature works in:

- Text channels
- Threads
- Forum channels
- Any messageable channel

## Limitations

### File Limits

Discord limits messages to 10 attachments. If a message has more than 10 images:

- The first 10 images will be included
- Additional images will be listed as links in the embed

### Embed Content

Some embed content may not be fully preserved:

- Complex embeds are noted but not fully recreated
- Embedded images are extracted when possible
- Interactive embed elements (buttons, select menus) are not included

### Message Length

Very long messages may be truncated to fit Discord's embed description limits. The full content is preserved up to the limit, with a truncation indicator (`...`) if needed.

## Use Cases

### Saving Important Information

Bookmark messages containing:

- Important announcements
- Useful links and resources
- Code snippets or commands
- Server rules or guidelines
- Meeting notes or summaries

### Reference Material

Keep track of:

- Helpful explanations or tutorials
- Configuration examples
- Documentation links
- Community resources

### Personal Notes

Save messages you want to revisit:

- Interesting discussions
- Useful tips or tricks
- Personal reminders
- Favorite memes or images

## Tips

!!! tip "Quick Access"
    Keep your DMs organized by creating a folder or using Discord's search feature to find bookmarked messages quickly.

!!! tip "Jump to Context"
    Use the "Jump to Message" link in bookmarks to return to the original conversation and see replies or follow-up messages.

!!! tip "Bookmark Replies"
    If a message is a reply, the bookmark includes a link to the original message it was replying to, giving you full context.

!!! tip "Organize Your Bookmarks"
    Since bookmarks are in your DMs, you can organize them by:
    - Reacting with different emojis for categorization
    - Pinning important bookmarks
    - Using Discord's search to find specific bookmarks

!!! warning "DM Privacy"
    Make sure you're comfortable with Tux sending you DMs. If you prefer not to receive DMs, you'll need to enable them temporarily to use bookmarks, or use Discord's built-in save message feature instead.

## Troubleshooting

### Not Receiving Bookmarks

If you're not receiving bookmarks in your DMs:

1. **Check Privacy Settings**: Ensure you allow DMs from server members
2. **Check Server Settings**: Some servers restrict who can DM members
3. **Check Bot Status**: Make sure Tux is online and functioning
4. **Check Error Messages**: Look for notifications in the channel where you bookmarked

### Can't Remove Bookmarks

If you can't remove a bookmark:

- Make sure you're reacting in your DMs, not in a server channel
- Ensure you're reacting to the bookmark message itself (sent by Tux)
- Check that you're using the 🗑️ emoji

### Missing Attachments

If attachments aren't included:

- The original attachment may have been deleted
- The file may be too large
- Non-image attachments are listed as links, not included as files
- Discord's 10-file limit may have been reached

## For Administrators

The Bookmarks feature requires no configuration and works automatically once Tux is added to your server. All users can bookmark messages in channels they have access to.

If you want to restrict bookmarking:

- Use Discord's permission system to control who can react in channels
- Consider using reaction roles or moderation bots to manage reactions
- The feature respects Discord's channel permissions
